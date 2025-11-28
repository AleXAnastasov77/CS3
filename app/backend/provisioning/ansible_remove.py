import os
import tempfile
import subprocess
from config import Config


def unjoin_domain(vm_name):
    inventory = f"""[{vm_name}]
{vm_name} ansible_user={Config.WIN_LOCAL_USER} ansible_password={Config.WIN_LOCAL_PASS} ansible_connection=winrm ansible_winrm_transport=ntlm ansible_winrm_server_cert_validation=ignore
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

    subprocess.run(cmd, check=True)

    os.remove(inv_path)
