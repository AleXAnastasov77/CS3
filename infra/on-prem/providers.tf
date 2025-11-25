terraform {
  backend "s3" {
    bucket       = "tfstate-alex-cs3"
    key          = "dev/terraform-onprem.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
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