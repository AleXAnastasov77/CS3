from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl, time
from config import Config


def _connect_vsphere():
    ctx = ssl._create_unverified_context()
    return SmartConnect(
        host=Config.VCENTER_HOST,
        user=Config.VCENTER_USER,
        pwd=Config.VCENTER_PASS,
        sslContext=ctx,
    )


def _find_resource_pool(datacenter):
    """
    Recursively search *ALL* resource pools inside the datacenter, not only top level.
    Needed because Netlab pools are nested (Cluster → _Courses-RP-A → MA-NCA1-RP → i547391)
    """

    target = Config.VCENTER_RESOURCE_POOL

    def walk(pool):
        if pool.name == target:
            return pool
        for child in getattr(pool, "resourcePool", []):
            found = walk(child)
            if found:
                return found
        return None

    # Iterate clusters
    for cluster in datacenter.hostFolder.childEntity:
        if isinstance(cluster, vim.ClusterComputeResource) and cluster.name == Config.VCENTER_CLUSTER:
            return walk(cluster.resourcePool)

    return None


def create_vsphere_vm(vm_name):
    si = _connect_vsphere()
    content = si.RetrieveContent()

    # ---------------------------
    # TEMPLATE & FOLDER
    # ---------------------------
    template = content.searchIndex.FindByInventoryPath(Config.VCENTER_TEMPLATE_PATH)
    if not template:
        Disconnect(si)
        raise Exception(f"Template not found: {Config.VCENTER_TEMPLATE_PATH}")

    folder = content.searchIndex.FindByInventoryPath(Config.VCENTER_VM_FOLDER_PATH)
    if not folder:
        Disconnect(si)
        raise Exception(f"VM Folder not found: {Config.VCENTER_VM_FOLDER_PATH}")

    # ---------------------------
    # DATACENTER
    # ---------------------------
    datacenter = None
    for dc in content.rootFolder.childEntity:
        if isinstance(dc, vim.Datacenter) and dc.name == Config.VCENTER_DATACENTER:
            datacenter = dc
            break
    if not datacenter:
        Disconnect(si)
        raise Exception("Datacenter not found")

    # ---------------------------
    # DATASTORE (supports clusters & normal)
    # ---------------------------
    datastore = None
    for entity in datacenter.datastoreFolder.childEntity:
        if isinstance(entity, vim.Datastore) and entity.name == Config.VCENTER_DATASTORE:
            datastore = entity
            break

        if isinstance(entity, vim.StoragePod):    # datastore cluster
            for ds in entity.childEntity:
                if ds.name == Config.VCENTER_DATASTORE:
                    datastore = ds
                    break

    if not datastore:
        Disconnect(si)
        raise Exception("Datastore not found")

    # ---------------------------
    # RESOURCE POOL (FULLY FIXED)
    # ---------------------------
    pool = _find_resource_pool(datacenter)
    if not pool:
        Disconnect(si)
        raise Exception(
            f"Resource pool '{Config.VCENTER_RESOURCE_POOL}' not found "
            f"in cluster '{Config.VCENTER_CLUSTER}'"
        )

    # ---------------------------
    # CLONING
    # ---------------------------
    relocate = vim.vm.RelocateSpec(datastore=datastore, pool=pool)
    clone_spec = vim.vm.CloneSpec(location=relocate, powerOn=True, template=False)

    task = template.CloneVM_Task(folder=folder, name=vm_name, spec=clone_spec)
    print("[vSphere] Clone task started — waiting for completion...")

    while task.info.state == vim.TaskInfo.State.running:
        time.sleep(2)

    if task.info.state != vim.TaskInfo.State.success:
        err = task.info.error
        Disconnect(si)
        raise Exception(f"VM clone failed: {err}")

    print(f"[vSphere] VM '{vm_name}' clone SUCCESS")

    # ----------------------------------------------------
    # GET VM IP (Poll the VMware guest tools until ready)
    # ----------------------------------------------------
    vm_obj = task.info.result

    ip = None
    for _ in range(60):  
        if vm_obj.guest and vm_obj.guest.ipAddress:
            ip = vm_obj.guest.ipAddress
            break
        time.sleep(2)

    Disconnect(si)

    if not ip:
        raise Exception("VM cloned but no IP acquired (VMware Tools not ready?)")

    print(f"[vSphere] VM '{vm_name}' IP acquired: {ip}")
    return ip


def delete_vsphere_vm(vm_name):
    si = _connect_vsphere()
    content = si.RetrieveContent()

    vm = content.searchIndex.FindByDnsName(None, vm_name, True)
    if vm:
        task = vm.Destroy_Task()
        print(f"[vSphere] Deleting VM '{vm_name}'...")
        while task.info.state == vim.TaskInfo.State.running:
            time.sleep(2)

    Disconnect(si)
