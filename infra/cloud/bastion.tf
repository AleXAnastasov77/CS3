data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

resource "aws_instance" "ec2_bastion" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.bastion_sg.id]
  subnet_id              = aws_subnet.public_cs3.id
  private_ip             = "10.0.2.10"
  key_name               = "ansible_keypair"
  root_block_device {
    encrypted   = true
    volume_size = 10
    volume_type = "gp3"
  }
  metadata_options {
    http_tokens = "required"
  }
  tags = {
    Name = "ec2_bastion"
  }
}