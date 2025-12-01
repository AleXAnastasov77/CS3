from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl, time
from config import Config

def wait_for_task(task):
    """Waits for a vSphere task to finish and returns the result or raises an error."""
    import time

    while True:
        state = task.info.state

        if state == "success":
            return task.info.result

        if state == "error":
            # Return full structured error for debugging
            err = task.info.error
            msg = getattr(err, "msg", None) or getattr(err, "localizedMessage", None)
            raise Exception(f"vSphere task failed: {msg}")

        time.sleep(1)


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


    # Properly wait for it
    wait_for_task(task)

    print(f"[OK] VM '{vm_name}' cloned successfully.")

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

    print(f"[vSphere] Searching for VM '{vm_name}'...")
    vm = content.searchIndex.FindByInventoryPath(Config.VCENTER_VM_FOLDER_PATH)


    if not vm:
        print(f"[vSphere] VM '{vm_name}' not found, skipping deletion.")
        Disconnect(si)
        return

    # --- 1) Power off the VM if needed ---
    try:
        if vm.runtime.powerState == "poweredOn":
            print(f"[vSphere] VM '{vm_name}' is powered ON → powering off...")
            power_off_task = vm.PowerOffVM_Task()
            wait_for_task(power_off_task)
            print(f"[vSphere] VM '{vm_name}' is now powered OFF.")
        else:
            print(f"[vSphere] VM '{vm_name}' is already powered OFF.")
    except Exception as e:
        print(f"[vSphere] WARNING: failed to power off VM '{vm_name}': {e}")

    # --- 2) Destroy the VM ---
    try:
        print(f"[vSphere] Deleting VM '{vm_name}'...")
        destroy_task = vm.Destroy_Task()
        wait_for_task(destroy_task)
        print(f"[vSphere] VM '{vm_name}' deleted successfully.")
    except Exception as e:
        print(f"[vSphere] ERROR deleting VM '{vm_name}': {e}")

    Disconnect(si)

def get_vm_ip(vm_name):
    si = _connect_vsphere()
    content = si.RetrieveContent()

    vm = content.searchIndex.FindByInventoryPath(Config.VCENTER_VM_FOLDER_PATH)
    if not vm:
        raise Exception(f"VM '{vm_name}' not found")

    # Try guest tools first
    if vm.guest is not None and vm.guest.net:
        for nic in vm.guest.net:
            if nic.ipAddress:
                # return first non-IPv6 IP
                for ip in nic.ipAddress:
                    if "." in ip:
                        Disconnect(si)
                        return ip

    Disconnect(si)
    raise Exception(f"No valid IPv4 found for VM '{vm_name}' (Guest Tools?)")