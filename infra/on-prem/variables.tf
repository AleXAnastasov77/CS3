variable "user" {
  description = "The username to login in VCenter"
  type        = string
}

variable "password" {
  description = "The password to login in VCenter"
  type        = string
  sensitive   = true
}

variable "vsphere_server" {
  description = "The password to login in VCenter"
  type        = string
  default     = "vcenter.netlab.fontysict.nl"
}