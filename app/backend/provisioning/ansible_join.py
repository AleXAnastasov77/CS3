import os
import tempfile
import subprocess
from config import Config


def join_domain(vm_ip, vm_name, computer_ou):
    """
    Join a VM to the domain using IP.
    vm_ip      = IP used for WinRM connectivity
    vm_name    = the new hostname to assign before join
    computer_ou = OU where the computer object will be created
    """

    inventory = f"""[{vm_name}]
{vm_ip} ansible_user={Config.WIN_LOCAL_USER} ansible_password={Config.WIN_LOCAL_PASS} ansible_connection=winrm ansible_winrm_transport=ntlm ansible_winrm_server_cert_validation=ignore ansible_winrm_scheme=http ansible_port=5985
"""

    with tempfile.NamedTemporaryFile("w", delete=False) as inv:
        inv.write(inventory)
        inv_path = inv.name

    playbook_path = os.path.join(
        os.path.dirname(__file__), "ansible", "join_domain.yml"
    )

    cmd = [
        "ansible-playbook",
        "-i",
        inv_path,
        playbook_path,
        "--extra-vars",
        (
            f"domain={Config.AD_DOMAIN} "
            f"admin_user={Config.AD_ADMIN_USER} "
            f"admin_pass={Config.AD_ADMIN_PASS} "
            f"computer_ou={computer_ou} "
            f"new_hostname={vm_name}"
        ),
    ]

    subprocess.run(cmd, check=True)
    os.remove(inv_path)

