data "aws_acm_certificate" "cert" {
  domain   = "server.vpn.internal"
  statuses = ["ISSUED"]
}

resource "aws_ec2_client_vpn_endpoint" "vpnendpoint_cs3" {
  description            = "VPN for monitoring access"
  server_certificate_arn = data.aws_acm_certificate.cert.arn
  client_cidr_block      = "10.100.0.0/16"
  dns_servers = ["10.0.0.2"]
  vpc_id = aws_vpc.vpc_cs3.id
  split_tunnel = true

  authentication_options {
    type                       = "certificate-authentication"
    root_certificate_chain_arn = "arn:aws:acm:eu-central-1:057827529833:certificate/aaa66e36-7ce7-4697-aa3b-f76b643a0393"
  }

  connection_log_options {
    enabled               = false
  }
}

resource "aws_ec2_client_vpn_network_association" "network_association" {
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.vpnendpoint_cs3.id
  subnet_id              = aws_subnet.public_cs3.id
}

resource "aws_ec2_client_vpn_authorization_rule" "authorization_rule" {
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.vpnendpoint_cs3.id
  target_network_cidr    = aws_vpc.vpc_cs3.cidr_block
  authorize_all_groups   = true
}

resource "aws_ec2_client_vpn_route" "to_DB_A" {
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.vpnendpoint_cs3.id
  destination_cidr_block = aws_subnet.privateDB_cs3_A.cidr_block
  target_vpc_subnet_id   = aws_subnet.public_cs3.id
}

resource "aws_ec2_client_vpn_route" "to_DB_B" {
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.vpnendpoint_cs3.id
  destination_cidr_block = aws_subnet.privateDB_cs3_B.cidr_block
  target_vpc_subnet_id   = aws_subnet.public_cs3.id
}