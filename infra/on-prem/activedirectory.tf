resource "vsphere_virtual_machine" "ad_dc" {
  name             = "SERVERS_DC"
  folder           = "/_Courses/MA-NCA1/i547391"
  resource_pool_id = data.vsphere_resource_pool.pool.id
  datastore_id     = data.vsphere_datastore.ds.id
  firmware = "efi"
  num_cpus = 2
  memory   = 12288
  guest_id = data.vsphere_virtual_machine.win2019_template.guest_id
  wait_for_guest_net_timeout = 0
  network_interface {
    network_id   = data.vsphere_network.servers.id
    adapter_type = "vmxnet3"
  }

  disk {
    label            = "disk0"
    size             = 90
    thin_provisioned = true
  }

  clone {
    template_uuid = data.vsphere_virtual_machine.win2019_template.id
  }
}
