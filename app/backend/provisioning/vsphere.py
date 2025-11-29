from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
import time
from config import Config


def _connect_vsphere():
    ctx = ssl._create_unverified_context()
    return SmartConnect(
        host=Config.VCENTER_HOST,
        user=Config.VCENTER_USER,
        pwd=Config.VCENTER_PASS,
        sslContext=ctx,
    )


def _wait_for_task(task):
    while task.info.state == vim.TaskInfo.State.running:
        time.sleep(1)
    return task.info.state == vim.TaskInfo.State.success


def _get_vm_ip(vm_obj):
    """
    Extract IPv4 reported by VMware Tools.
    Returns None if not found yet.
    """
    if not vm_obj.guest or not vm_obj.guest.net:
        return None

    for nic in vm_obj.guest.net:
        if not nic.ipConfig or not nic.ipConfig.ipAddress:
            continue
        for ip in nic.ipConfig.ipAddress:
            if ":" not in ip.ipAddress:  # skip IPv6
                return ip.ipAddress
    return None


def create_vsphere_vm(vm_name):
    """
    Clone a VM from the template and return its IP (IPv4).
    """
    si = _connect_vsphere()
    content = si.RetrieveContent()

    # -----------------------
    # TEMPLATE
    # -----------------------
    template = content.searchIndex.FindByInventoryPath(Config.VCENTER_TEMPLATE_PATH)
    if not template:
        Disconnect(si)
        raise Exception(f"Template not found: {Config.VCENTER_TEMPLATE_PATH}")

    # -----------------------
    # FOLDER
    # -----------------------
    folder = content.searchIndex.FindByInventoryPath(Config.VCENTER_VM_FOLDER_PATH)
    if not folder:
        Disconnect(si)
        raise Exception(f"VM folder not found: {Config.VCENTER_VM_FOLDER_PATH}")

    # -----------------------
    # DATACENTER
    # -----------------------
    datacenter = next(
        (dc for dc in content.rootFolder.childEntity
         if isinstance(dc, vim.Datacenter) and dc.name == Config.VCENTER_DATACENTER),
        None
    )
    if not datacenter:
        Disconnect(si)
        raise Exception("Datacenter not found")

    # -----------------------
    # DATASTORE
    # -----------------------
    datastore = None
    for entity in datacenter.datastoreFolder.childEntity:
        if isinstance(entity, vim.Datastore) and entity.name == Config.VCENTER_DATASTORE:
            datastore = entity
            break

        if isinstance(entity, vim.StoragePod):
            for ds in entity.childEntity:
                if ds.name == Config.VCENTER_DATASTORE:
                    datastore = ds
                    break

        if datastore:
            break

    if not datastore:
        Disconnect(si)
        raise Exception("Datastore not found")

    # -----------------------
    # RESOURCE POOL / CLUSTER
    # -----------------------
    pool = None
    for cluster in datacenter.hostFolder.childEntity:
        if isinstance(cluster, vim.ClusterComputeResource) and cluster.name == Config.VCENTER_CLUSTER:

            # Find child resource pools
            for rp in cluster.resourcePool.resourcePool:
                if rp.name == Config.VCENTER_RESOURCE_POOL:
                    pool = rp
                    break

            # Or use cluster’s root pool
            if not pool and cluster.resourcePool.name == Config.VCENTER_RESOURCE_POOL:
                pool = cluster.resourcePool

            break

    if not pool:
        Disconnect(si)
        raise Exception("Resource pool not found")

    # -----------------------
    # CLONE VM
    # -----------------------
    relocate = vim.vm.RelocateSpec(datastore=datastore, pool=pool)
    clone_spec = vim.vm.CloneSpec(location=relocate, powerOn=True, template=False)

    task = template.CloneVM_Task(folder=folder, name=vm_name, spec=clone_spec)
    if not _wait_for_task(task):
        Disconnect(si)
        raise Exception(f"VM clone failed: {task.info.error}")

    # -----------------------
    # GET VM OBJECT
    # -----------------------
    vm_obj = content.searchIndex.FindByInventoryPath(
        f"{Config.VCENTER_VM_FOLDER_PATH}/{vm_name}"
    )

    # -----------------------
    # WAIT FOR VMWARE TOOLS & IP
    # -----------------------
    ip = None
    for _ in range(60):  # up to ~120 seconds
        ip = _get_vm_ip(vm_obj)
        if ip:
            break
        time.sleep(2)

    Disconnect(si)

    if not ip:
        raise Exception(
            "VM cloned but has no IP. VMware Tools may not be running on the template."
        )

    return ip  # crucial


def delete_vsphere_vm(vm_name):
    """
    Deletes a VM by DNS name or VM name.
    """
    si = _connect_vsphere()
    content = si.RetrieveContent()

    # Try DNS name lookup first
    vm = content.searchIndex.FindByDnsName(None, vm_name, True)

    # Fallback: search by inventory path
    if not vm:
        vm = content.searchIndex.FindByInventoryPath(
            f"{Config.VCENTER_VM_FOLDER_PATH}/{vm_name}"
        )

    if vm:
        task = vm.Destroy_Task()
        _wait_for_task(task)

    Disconnect(si)
