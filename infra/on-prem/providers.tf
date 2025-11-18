terraform {
  required_providers {
    vsphere = {
      source  = "vmware/vsphere"
      version = "2.15.0"
    }
  }
}

provider "vsphere" {
  user           = var.user
  password       = var.password
  vsphere_server = var.vsphere_server
}