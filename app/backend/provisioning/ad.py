from ldap3 import Server, Connection, ALL
from config import Config
import winrm


# --------------------------
# Helpers
# --------------------------

def _ad_base_dn():
    """Convert domain 'innovatech.internal' → 'DC=innovatech,DC=internal'."""
    parts = Config.AD_DOMAIN.split(".")
    return ",".join(f"DC={p}" for p in parts)


def _admin_upn():
    """Return admin user as UPN (username@domain)."""
    if "@" in Config.AD_ADMIN_USER:
        return Config.AD_ADMIN_USER
    return f"{Config.AD_ADMIN_USER}@{Config.AD_DOMAIN}"


def _winrm_session():
    """Create a WinRM session to the DC."""
    return winrm.Session(
        f'http://{Config.AD_SERVER}:5985/wsman',
        auth=("Administrator", Config.AD_ADMIN_PASS)
    )


# --------------------------
# MAIN FUNCTIONS
# --------------------------

def create_ad_user(ad_username, first_name, last_name, email, password, ou_dn):
    """
    Create a new AD user (LDAP), then set password & enable account using WinRM.
    """

    # -----------------------
    # 1. CREATE USER (LDAP)
    # -----------------------
    server = Server(Config.AD_SERVER, get_info=ALL, use_ssl=False)
    conn = Connection(
        server,
        user=_admin_upn(),
        password=Config.AD_ADMIN_PASS,
        authentication="SIMPLE",
        auto_bind=True,
    )

    user_dn = f"CN={first_name} {last_name},{ou_dn}"

    attrs = {
        "sAMAccountName": ad_username,
        "userPrincipalName": f"{ad_username}@{Config.AD_DOMAIN}",
        "givenName": first_name,
        "sn": last_name,
        "displayName": f"{first_name} {last_name}",
        "mail": email,
    }

    conn.add(
        dn=user_dn,
        object_class=["top", "person", "organizationalPerson", "user"],
        attributes=attrs,
    )

    if conn.result["result"] != 0:
        raise Exception(f"AD user creation failed (LDAP ADD): {conn.result}")

    conn.unbind()

    ps_script = f'''
    try {{
        Import-Module ActiveDirectory

        Set-ADAccountPassword -Identity "{ad_username}" -Reset -NewPassword (ConvertTo-SecureString "{password}" -AsPlainText -Force)
        Enable-ADAccount -Identity "{ad_username}"

        Write-Output "SUCCESS"
    }}
    catch {{
        Write-Output "ERROR: $($_.Exception.Message)"
    }}
    '''

    session = _winrm_session()
    result = session.run_ps(ps_script)

    stdout = result.std_out.decode().strip()
    stderr = result.std_err.decode().strip()

    # Ignore harmless CLIXML progress spam
    if stderr.startswith("#< CLIXML"):
        stderr = ""

    # If PowerShell returned a structured error:
    if "ERROR:" in stdout:
        raise Exception(f"Failed to set AD password: {stdout}")

    # If stderr still contains unexpected errors:
    if stderr and "CLIXML" not in stderr:
        raise Exception(f"Unexpected WinRM error: {stderr}")

    # Only return success if PowerShell explicitly printed SUCCESS
    if "SUCCESS" not in stdout:
        raise Exception(f"Unexpected PowerShell output: {stdout}")

    return True


def disable_ad_user(ad_username):
    """
    Disable an AD user using WinRM.
    """
    ps_script = f'''
    try {{
        Import-Module ActiveDirectory

        Disable-ADAccount -Identity "{ad_username}"

        Write-Output "SUCCESS"
    }}
    catch {{
        Write-Output "ERROR: $($_.Exception.Message)"
    }}
    '''

    session = _winrm_session()
    result = session.run_ps(ps_script)
    stdout = result.std_out.decode().strip()
    stderr = result.std_err.decode().strip()
    if stderr.startswith("#< CLIXML"):
        stderr = ""

    # If PowerShell returned a structured error:
    if "ERROR:" in stdout:
        raise Exception(f"Failed to set AD password: {stdout}")

    # If stderr still contains unexpected errors:
    if stderr and "CLIXML" not in stderr:
        raise Exception(f"Unexpected WinRM error: {stderr}")

    # Only return success if PowerShell explicitly printed SUCCESS
    if "SUCCESS" not in stdout:
        raise Exception(f"Unexpected PowerShell output: {stdout}")


    return True
