resource "aws_db_subnet_group" "sqldb_sg" {
  name       = "main"
  subnet_ids = [aws_subnet.privateDB_cs3_A.id, aws_subnet.privateDB_cs3_B.id]

  tags = {
    Name = "sqldb_sg"
  }
}

resource "aws_db_instance" "mysqldb_cs3" {
  allocated_storage         = 20
  max_allocated_storage     = 25
  identifier = "HR-CS3"
  engine                    = "mysql"
  engine_version            = "8.0" 
  instance_class            = "db.t3.micro"

  username                  = var.DB_USERNAME
  password                  = var.DB_PASSWORD

  db_subnet_group_name      = aws_db_subnet_group.sqldb_sg.name
  vpc_security_group_ids    = [aws_security_group.db_sg.id]

  
  storage_encrypted         = true

  skip_final_snapshot       = false
  final_snapshot_identifier = "HRapp-MySQL-final-${formatdate("YYYYMMDDhhmmss", timestamp())}"

  backup_retention_period   = 7

  lifecycle {
    ignore_changes = [
      password,
      backup_retention_period,
      maintenance_window,
      final_snapshot_identifier
    ]
  }
}
