import os
from dotenv import load_dotenv
load_dotenv()
class Config:
    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

    # DB
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "hr_app")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRES_MINUTES = int("60")

        # vSphere
    VCENTER_HOST = "vcenter.netlab.fontysict.nl"
    VCENTER_USER = os.getenv("VSPHERE_USER")
    VCENTER_PASS = os.getenv("VSPHERE_PASS")
    VCENTER_TEMPLATE_PATH = "Netlab-DC/vm/_Courses/MA-NCA1/i547391/test"
    VCENTER_VM_FOLDER_PATH = "Netlab-DC/vm/_Courses/MA-NCA1/i547391"
    VCENTER_DATASTORE = "NIM01-1"
    VCENTER_CLUSTER = "Netlab-Cluster-A"
    VCENTER_RESOURCE_POOL = "i547391"
    VCENTER_DATACENTER = "Netlab-DC"
    
    # WinRM local admin
    WIN_LOCAL_PASS = os.getenv("WIN_LOCAL_PASS")
    WIN_LOCAL_USER = "Alex"

    AD_SERVER = "192.168.0.10"
    AD_DOMAIN = "innovatech.internal"
    AD_ADMIN_USER = "webserver@innovatech.internal"
    AD_ADMIN_PASS = os.getenv("AD_ADMIN_PASS")
    AD_USER_OU = {
        "HR":        "OU=HR,OU=Users,OU=Netherlands,DC=innovatech,DC=internal",
        "IT":        "OU=IT,OU=Users,OU=Netherlands,DC=innovatech,DC=internal",
        "Finance":   "OU=Finance,OU=Users,OU=Netherlands,DC=innovatech,DC=internal",
        "Marketing": "OU=Marketing,OU=Users,OU=Netherlands,DC=innovatech,DC=internal",
    }

    # Computer OUs
    AD_COMPUTER_OU = {
        "HR":        "OU=HR,OU=Computers,OU=Netherlands,DC=innovatech,DC=internal",
        "IT":        "OU=IT,OU=Computers,OU=Netherlands,DC=innovatech,DC=internal",
        "Finance":   "OU=Finance,OU=Computers,OU=Netherlands,DC=innovatech,DC=internal",
        "Marketing": "OU=Marketing,OU=Computers,OU=Netherlands,DC=innovatech,DC=internal",
    }
