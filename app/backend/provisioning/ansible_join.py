import os
import tempfile
import subprocess
from config import Config


def join_domain(vm_ip, computer_ou, vm_name):
    """
    Join a VM to the domain using its IP (most reliable).
    """,

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
        f"domain={Config.AD_DOMAIN} admin_user={Config.AD_ADMIN_USER} admin_pass={Config.AD_ADMIN_PASS} computer_ou={computer_ou}",
    ]

    subprocess.run(cmd, check=True)
    os.remove(inv_path)
