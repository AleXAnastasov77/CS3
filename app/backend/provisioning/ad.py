from ldap3 import Server, Connection, ALL, MODIFY_REPLACE, Tls
from config import Config
import ssl

def _ad_base_dn():
    """Convert domain like innovatech.internal → DC=innovatech,DC=internal"""
    parts = Config.AD_DOMAIN.split(".")
    return ",".join(f"DC={p}" for p in parts)


def _admin_upn():
    """Return admin user in UPN format → username@domain"""
    # If your config uses AD_ADMIN_USER as 'webserver'
    if "@" not in Config.AD_ADMIN_USER:
        return f"{Config.AD_ADMIN_USER}@{Config.AD_DOMAIN}"
    return Config.AD_ADMIN_USER


def create_ad_user(ad_username, first_name, last_name, email, password, ou_dn):
    """
    Create and enable a user in AD under the given OU.
    Password is set in a second step because AD does NOT allow
    unicodePwd during ADD over non-SSL LDAP.
    """

    admin_user = _admin_upn()
    admin_pass = Config.AD_ADMIN_PASS
    tls = Tls(validate=ssl.CERT_NONE)

    server = Server(Config.AD_SERVER, use_ssl=True, port=636, tls=tls, get_info=ALL, use_ssl=False)
    conn = Connection(
    server,
    user=admin_user,
    password=admin_pass,
    authentication="SIMPLE",
    auto_bind=True,
    auto_escape=True
    )

    user_dn = f"CN={first_name} {last_name},{ou_dn}"

    # STEP 1 — create user WITHOUT password
    attrs = {
        "sAMAccountName": ad_username,
        "userPrincipalName": f"{ad_username}@{Config.AD_DOMAIN}",
        "givenName": first_name,
        "sn": last_name,
        "displayName": f"{first_name} {last_name}",
        "mail": email,
    }

    conn.add(user_dn, ["top", "person", "organizationalPerson", "user"], attrs)

    if conn.result["result"] != 0:
        raise Exception(f"AD user creation failed during ADD: {conn.result}")

    # STEP 2 — set password (works over non-SSL when done as MODIFY)
    unicode_pw = f'"{password}"'.encode("utf-16-le")
    conn.modify(
        user_dn,
        {"unicodePwd": [(MODIFY_REPLACE, [unicode_pw])]}
    )

    if conn.result["result"] != 0:
        raise Exception(f"Failed to set password: {conn.result}")

    # STEP 3 — enable account (512 = NORMAL_ACCOUNT)
    conn.modify(
        user_dn,
        {"userAccountControl": [(MODIFY_REPLACE, 512)]}
    )

    if conn.result["result"] != 0:
        raise Exception(f"Failed to enable account: {conn.result}")

    conn.unbind()


def disable_ad_user(ad_username):
    """
    Find user by sAMAccountName and disable the account (set UAC=514).
    """

    admin_user = _admin_upn()
    admin_pass = Config.AD_ADMIN_PASS

    server = Server(Config.AD_SERVER, get_info=ALL, use_ssl=False)
    conn = Connection(
        server,
        user=admin_user,
        password=admin_pass,
        authentication="SIMPLE",
        auto_bind=True,
    )

    base_dn = _ad_base_dn()
    conn.search(
        search_base=base_dn,
        search_filter=f"(sAMAccountName={ad_username})",
        attributes=["distinguishedName"],
    )

    if not conn.entries:
        conn.unbind()
        return False  # user not found

    user_dn = conn.entries[0].distinguishedName.value

    # 514 = ACCOUNTDISABLE
    conn.modify(
        user_dn,
        {"userAccountControl": [(MODIFY_REPLACE, 514)]}
    )

    if conn.result["result"] != 0:
        raise Exception(f"Failed to disable user: {conn.result}")

    conn.unbind()
    return True
