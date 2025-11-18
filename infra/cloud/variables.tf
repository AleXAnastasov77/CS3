variable "region" {
  description = "The region of the deployed resources on AWS"
  type        = string
  default     = "eu-central-1"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    environment = "Development"
    project     = "Case Study 3"
    owner       = "Aleks Anastasov"
  }
}

variable "DB_USERNAME" {
  description = "The username of the SQL Database"
  type        = string
  sensitive   = true
}

variable "DB_PASSWORD" {
  description = "The password of the SQL Database"
  type        = string
  sensitive   = true
}