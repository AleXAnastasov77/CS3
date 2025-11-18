resource "vsphere_virtual_machine" "router_pfsense" {
  name             = "ROUTER_PFSENSE"
  folder           = "/_Courses/MA-NCA1/i547391"
  resource_pool_id = data.vsphere_resource_pool.pool.id
  datastore_id     = data.vsphere_datastore.ds.id
  num_cpus = 2
  memory   = 2048
  guest_id = data.vsphere_virtual_machine.pfsense_template.guest_id
  wait_for_guest_net_timeout = 0
  network_interface {
    network_id   = data.vsphere_network.pfsense.id
    adapter_type = "vmxnet3"
  }
  network_interface {
    network_id   = data.vsphere_network.servers.id
    adapter_type = "vmxnet3"
  }
  network_interface {
    network_id = data.vsphere_network.workstations.id
    adapter_type = "vmxnet3"
  }

  disk {
    label            = "Hard Disk 1"
    size             = 16
    thin_provisioned = true
  }

  clone {
    template_uuid = data.vsphere_virtual_machine.pfsense_template.id
  }
}
