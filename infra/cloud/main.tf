resource "aws_servicecatalogappregistry_application" "cs3_soar" {
  provider    = aws.application
  name        = "CS3"
  description = "Case Study 3 - Employee on-boarding and off-boarding"
}

# provider "aws" {
#   default_tags {
#     tags = merge(
#       var.tags,
#       aws_servicecatalogappregistry_application.cs3_soar.application_tag
#     )
#   }
# }