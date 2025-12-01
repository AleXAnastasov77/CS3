import os
import tempfile
import subprocess
from config import Config
from provisioning.vsphere import get_vm_ip

def unjoin_domain(vm_name):
    """
    Unjoin a Windows VM from the domain using its IP address.
    WinRM MUST reach the host by IP, not hostname.
    """
    vm_ip = get_vm_ip(vm_name)

    inventory = f"""[windows]
{vm_ip} ansible_user={Config.WIN_LOCAL_USER} ansible_password={Config.WIN_LOCAL_PASS} ansible_connection=winrm ansible_winrm_transport=ntlm ansible_winrm_server_cert_validation=ignore
"""

    with tempfile.NamedTemporaryFile("w", delete=False) as inv:
        inv.write(inventory)
        inv_path = inv.name

    playbook_path = os.path.join(
        os.path.dirname(__file__), "ansible", "unjoin_domain.yml"
    )

    cmd = [
        "ansible-playbook",
        "-i",
        inv_path,
        playbook_path,
    ]

    print(f"[Ansible] Unjoining domain for VM at IP {vm_ip}...")
    subprocess.run(cmd, check=True)

    os.remove(inv_path)
