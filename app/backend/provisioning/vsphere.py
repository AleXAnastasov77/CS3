from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
from config import Config


def _connect_vsphere():
    ctx = ssl._create_unverified_context()
    return SmartConnect(
        host=Config.VCENTER_HOST,
        user=Config.VCENTER_USER,
        pwd=Config.VCENTER_PASS,
        sslContext=ctx,
    )


def create_vsphere_vm(vm_name):
    si = _connect_vsphere()
    content = si.RetrieveContent()

    template = content.searchIndex.FindByInventoryPath(Config.VCENTER_TEMPLATE_PATH)
    if not template:
        Disconnect(si)
        raise Exception(f"Template not found at {Config.VCENTER_TEMPLATE_PATH}")

    folder = content.searchIndex.FindByInventoryPath(Config.VCENTER_VM_FOLDER_PATH)
    if not folder:
        Disconnect(si)
        raise Exception(f"VM folder not found at {Config.VCENTER_VM_FOLDER_PATH}")

    # datastore
    datacenter = None
    datastore = None

    for entity in datacenter.datastoreFolder.childEntity:
        # Case 1: individual datastore
        if isinstance(entity, vim.Datastore) and entity.name == Config.VCENTER_DATASTORE:
            datastore = entity
            break

        # Case 2: storage cluster (StoragePod)
        if isinstance(entity, vim.StoragePod):
            for ds in entity.childEntity:
                if ds.name == Config.VCENTER_DATASTORE:
                    datastore = ds
                    break

        if datastore:
            break

    if not datastore:
        Disconnect(si)
        raise Exception("Datastore not found (checked datastore folders AND storage pods)")

    # resource pool
    pool = None
    for cluster in datacenter.hostFolder.childEntity:
        if isinstance(cluster, vim.ClusterComputeResource) and cluster.name == Config.VCENTER_CLUSTER:
            for rp in cluster.resourcePool.resourcePool:
                if rp.name == Config.VCENTER_RESOURCE_POOL:
                    pool = rp
                    break
            if not pool and cluster.resourcePool.name == Config.VCENTER_RESOURCE_POOL:
                pool = cluster.resourcePool
            break

    if not pool:
        Disconnect(si)
        raise Exception("Resource pool not found")

    relocate = vim.vm.RelocateSpec(datastore=datastore, pool=pool)
    clone_spec = vim.vm.CloneSpec(location=relocate, powerOn=True, template=False)

    task = template.CloneVM_Task(folder=folder, name=vm_name, spec=clone_spec)
    while task.info.state == vim.TaskInfo.State.running:
        continue

    if task.info.state != vim.TaskInfo.State.success:
        Disconnect(si)
        raise Exception(f"VM clone failed: {task.info.error}")

    Disconnect(si)


def delete_vsphere_vm(vm_name):
    si = _connect_vsphere()
    content = si.RetrieveContent()

    vm = content.searchIndex.FindByDnsName(None, vm_name, True)
    if vm:
        task = vm.Destroy_Task()
        while task.info.state == vim.TaskInfo.State.running:
            continue

    Disconnect(si)
