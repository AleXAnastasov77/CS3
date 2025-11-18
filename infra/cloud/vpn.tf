# data "aws_acm_certificate" "cert" {
#   domain   = "server.vpn.internal"
#   statuses = ["ISSUED"]
# }

# resource "aws_ec2_client_vpn_endpoint" "vpnendpoint_cs3" {
#   description            = "VPN for monitoring access"
#   server_certificate_arn = data.aws_acm_certificate.cert.arn
#   client_cidr_block      = "10.0.100.0/24"
#   dns_servers = ["10.0.0.2"]
#   vpc_id = aws_vpc.vpc_cs3.id
#   split_tunnel = true

#   authentication_options {
#     type                       = "certificate-authentication"
#     root_certificate_chain_arn = "arn:aws:acm:eu-central-1:057827529833:certificate/54ab3b77-0344-4156-9c8b-620156c5e2d4"
#   }

#   connection_log_options {
#     enabled               = false
#   }
# }

# resource "aws_ec2_client_vpn_network_association" "network_association" {
#   client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.vpnendpoint_cs3.id
#   subnet_id              = aws_subnet.privateDB_cs3.id
# }

# resource "aws_ec2_client_vpn_authorization_rule" "authorization_rule" {
#   client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.vpnendpoint_cs3.id
#   target_network_cidr    = aws_vpc.vpc_cs3.cidr_block
#   authorize_all_groups   = true
# }