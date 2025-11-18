# VPC
resource "aws_vpc" "vpc_cs3" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name = "vpc_cs3"
  }
}
# SUBNETS
resource "aws_subnet" "privateDB_cs3" {
  vpc_id            = aws_vpc.vpc_cs3.id
  cidr_block        = "10.0.1.0/24"

  tags = {
    Name = "privateDB_cs3"
  }
}

resource "aws_subnet" "public_cs3" {
  vpc_id                  = aws_vpc.vpc_cs3.id
  cidr_block              = "10.0.2.0/24"
  map_public_ip_on_launch = true
  tags = {
    Name = "public_cs3"
  }
}

# GATEWAY
resource "aws_internet_gateway" "igw_cs3" {
  vpc_id = aws_vpc.vpc_cs3.id

  tags = {
    Name = "igw_cs3"
  }
}

# ROUTING TABLES
# tfsec:ignore:aws-ec2-no-public-ip-subnet
resource "aws_route_table" "rt_public_cs3" {
  vpc_id = aws_vpc.vpc_cs3.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw_cs3.id
  }
  tags = {
    Name = "rt_public_cs3"
  }
}

resource "aws_route_table" "rt_private_cs3" {
  vpc_id = aws_vpc.vpc_cs3.id

  tags = {
    Name = "rt_private_cs3"
  }
}

# ROUTING TABLE ASSOCIATIONS
resource "aws_route_table_association" "a" {
    subnet_id = aws_subnet.public_cs3.id
    route_table_id = aws_route_table.rt_public_cs3.id
}

resource "aws_route_table_association" "b" {
    subnet_id = aws_subnet.privateDB_cs3.id
    route_table_id = aws_route_table.rt_private_cs3.id
}

# SECURITY GROUPS
# tfsec:ignore:aws-ec2-no-public-egress-sgr
resource "aws_security_group" "db_sg" {
    name = "db-sg"
    description = "Allow access to DB from Bastion host and VPN"
    vpc_id = aws_vpc.vpc_cs3.id

    ingress {
    description = "Allow SQL"
    from_port   = 1433
    to_port     = 1433
    protocol    = "tcp"
    cidr_blocks = ["10.0.2.0/24", "10.0.100.0/24"]
    }

    egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    }

    tags = {
    Name = "db-sg"
    }
}
# tfsec:ignore:aws-ec2-no-public-egress-sgr
resource "aws_security_group" "bastion_sg" {
    name = "bastion-sg"
    description = "Allow SSH to bastion"
    vpc_id = aws_vpc.vpc_cs3.id

    ingress {
    description = "Allow SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    }

    tags = {
    Name = "db-sg"
    }
}

