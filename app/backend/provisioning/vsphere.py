from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
from config import Config


def _connect_vsphere():
    """Create an unverified SSL connection to vCenter."""
    ctx = ssl._create_unverified_context()
    return SmartConnect(
        host=Config.VCENTER_HOST,
        user=Config.VCENTER_USER,
        pwd=Config.VCENTER_PASS,
        sslContext=ctx,
    )


def _find_datacenter(content):
    """Return the datacenter object matching VCENTER_DATACENTER."""
    for dc in content.rootFolder.childEntity:
        if isinstance(dc, vim.Datacenter) and dc.name == Config.VCENTER_DATACENTER:
            return dc
    return None


def _find_datastore(datacenter):
    """
    Locate datastore by name.
    Supports:
      - direct datastores
      - datastores inside a StoragePod (datastore cluster)
    """
    target_name = Config.VCENTER_DATASTORE
    datastore_folder = datacenter.datastoreFolder

    for entity in datastore_folder.childEntity:
        # Case 1: plain datastore
        if isinstance(entity, vim.Datastore) and entity.name == target_name:
            return entity

        # Case 2: StoragePod (datastore cluster)
        if isinstance(entity, vim.StoragePod):
            for ds in entity.childEntity:
                if ds.name == target_name:
                    return ds

    return None


def _find_cluster(datacenter):
    """Return cluster object matching VCENTER_CLUSTER."""
    for c in datacenter.hostFolder.childEntity:
        if isinstance(c, vim.ClusterComputeResource) and c.name == Config.VCENTER_CLUSTER:
            return c
    return None


def _find_resource_pool_recursive(pool, target_name):
    """Recursively search for a resource pool by name."""
    if pool.name == target_name:
        return pool

    # pool.resourcePool is a list of child pools
    for child in getattr(pool, "resourcePool", []):
        found = _find_resource_pool_recursive(child, target_name)
        if found:
            return found

    return None


def create_vsphere_vm(vm_name):
    si = _connect_vsphere()
    content = si.RetrieveContent()

    # 1) Template
    template = content.searchIndex.FindByInventoryPath(Config.VCENTER_TEMPLATE_PATH)
    if not template:
        Disconnect(si)
        raise Exception(f"Template not found at {Config.VCENTER_TEMPLATE_PATH}")

    # 2) Folder to place the VM in
    folder = content.searchIndex.FindByInventoryPath(Config.VCENTER_VM_FOLDER_PATH)
    if not folder:
        Disconnect(si)
        raise Exception(f"VM folder not found at {Config.VCENTER_VM_FOLDER_PATH}")

    # 3) Datacenter
    datacenter = _find_datacenter(content)
    if not datacenter:
        Disconnect(si)
        raise Exception(f"Datacenter '{Config.VCENTER_DATACENTER}' not found")

    # 4) Datastore (supports datastore cluster)
    datastore = _find_datastore(datacenter)
    if not datastore:
        Disconnect(si)
        raise Exception(
            f"Datastore '{Config.VCENTER_DATASTORE}' not found "
            "(checked datastores and datastore clusters)"
        )

    # 5) Cluster
    cluster = _find_cluster(datacenter)
    if not cluster:
        Disconnect(si)
        raise Exception(f"Cluster '{Config.VCENTER_CLUSTER}' not found")

    # 6) Resource pool (recursive search to handle MA-NCA1-RP / i547391 nesting)
    pool = _find_resource_pool_recursive(cluster.resourcePool, Config.VCENTER_RESOURCE_POOL)
    if not pool:
        Disconnect(si)
        raise Exception(
            f"Resource pool '{Config.VCENTER_RESOURCE_POOL}' not found (searched recursively)"
        )

    # 7) Clone spec
    relocate = vim.vm.RelocateSpec(datastore=datastore, pool=pool)
    clone_spec = vim.vm.CloneSpec(location=relocate, powerOn=True, template=False)

    # 8) Start clone task
    task = template.CloneVM_Task(folder=folder, name=vm_name, spec=clone_spec)

    # Busy wait – simple but fine for now
    while task.info.state == vim.TaskInfo.State.running:
        continue

    if task.info.state != vim.TaskInfo.State.success:
        print("=== RAW TASK INFO ===")
        print("State:", task.info.state)
        print("Error:", task.info.error)
        print("Description:", task.info.description)
        print("Name:", task.info.name)
        print("Result:", task.info.result)
        print("Reason:", task.info.reason)
        print("Progress:", task.info.progress)
        print("Localized Message:", getattr(task.info.error, "localizedMessage", None) if task.info.error else None)
        Disconnect(si)
        raise Exception("Clone failed. Full info printed above.")


    Disconnect(si)


def delete_vsphere_vm(vm_name):
    """Destroy a VM by its DNS name (vm_name should match its DNS/FQDN)."""
    si = _connect_vsphere()
    content = si.RetrieveContent()

    vm = content.searchIndex.FindByDnsName(None, vm_name, True)
    if vm:
        task = vm.Destroy_Task()
        while task.info.state == vim.TaskInfo.State.running:
            continue

    Disconnect(si)
