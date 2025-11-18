data "vsphere_datacenter" "dc" {
  name = "Netlab-DC"
}

data "vsphere_datastore" "ds" {
  name          = "NIM01-1"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_compute_cluster" "cluster" {
  name          = "Netlab-Cluster-A"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_network" "servers" {
  name          = "1415_i547391_PVlanA"
  datacenter_id = data.vsphere_datacenter.dc.id
}
data "vsphere_network" "workstations" {
  name          = "1416_i547391_PVlanB"
  datacenter_id = data.vsphere_datacenter.dc.id
}
data "vsphere_network" "pfsense" {
  name          = "0154_Internet-Static-192.168.154.0_24"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_virtual_machine" "ubuntu_template" {
  name          = "Templ_Ubuntu-Linux_Server_24.04.3"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_virtual_machine" "win2019_template" {
  name          = "Templ_Windows2019_X64"
  datacenter_id = data.vsphere_datacenter.dc.id
}
data "vsphere_virtual_machine" "pfsense_template" {
  name          = "Templ_pfSense_2.7.2_firewall"
  datacenter_id = data.vsphere_datacenter.dc.id
}
data "vsphere_resource_pool" "pool" {
  name          = "i547391"
  datacenter_id = data.vsphere_datacenter.dc.id
}

# data "vsphere_folder" "vm_folder" {
#   path = "/Netlab-DC/vm/_Courses/MA-NCA1/i547391"
# }