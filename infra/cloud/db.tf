resource "aws_db_subnet_group" "sqldb_sg" {
  name       = "main"
  subnet_ids = [aws_subnet.privateDB_cs3_A.id, aws_subnet.privateDB_cs3_B.id]

  tags = {
    Name = "sqldb_sg"
  }
}

resource "aws_db_instance" "sqldb_cs3" {
  allocated_storage     = 20
  max_allocated_storage = 25
  db_subnet_group_name  = aws_db_subnet_group.sqldb_sg.name

  engine                    = "sqlserver-ee"
  engine_version            = "15.00"
  instance_class            = "db.t3.micro"
  username                  = var.DB_USERNAME
  password                  = var.DB_PASSWORD
  skip_final_snapshot       = false
  final_snapshot_identifier = "HRapp-MSSQL-final-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  storage_type              = "gp2"
  vpc_security_group_ids    = [aws_security_group.db_sg.id]
  storage_encrypted = true
  lifecycle {
    ignore_changes = [
      password, # Don’t try to reset the password every run
      backup_retention_period,
      maintenance_window,
      final_snapshot_identifier
    ]
  }
}
