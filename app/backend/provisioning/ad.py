from ldap3 import Server, Connection, NTLM, ALL
from config import Config


def _ad_base_dn():
    # derive DC=innovatech,DC=internal from innovatech.internal
    parts = Config.AD_DOMAIN.split(".")
    return ",".join(f"DC={p}" for p in parts)


def create_ad_user(ad_username, first_name, last_name, email, password, ou_dn):
    """
    Create and enable a user in AD under the given OU.
    ou_dn example: OU=HR,OU=Users,OU=Netherlands,DC=innovatech,DC=internal
    """
    server = Server(Config.AD_SERVER, get_info=ALL, port=636, use_ssl=True)
    conn = Connection(
        server,
        user=Config.AD_ADMIN_USER,
        password=Config.AD_ADMIN_PASS,
        authentication=NTLM,
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
        # password must be quoted and UTF-16-LE encoded
        "unicodePwd": ('"%s"' % password).encode("utf-16-le"),
    }

    conn.add(user_dn, ["top", "person", "organizationalPerson", "user"], attrs)

    if conn.result["result"] != 0:
        raise Exception(f"AD user creation failed: {conn.result}")

    # Enable the account (512 = NORMAL_ACCOUNT)
    conn.modify(user_dn, {"userAccountControl": [("MODIFY_REPLACE", 512)]})

    conn.unbind()


def disable_ad_user(ad_username):
    """
    Find user by sAMAccountName and disable the account.
    """
    server = Server(Config.AD_SERVER, get_info=ALL)
    conn = Connection(
        server,
        user=Config.AD_ADMIN_USER,
        password=Config.AD_ADMIN_PASS,
        authentication=NTLM,
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
        return

    dn = conn.entries[0].distinguishedName.value

    # 514 = ACCOUNTDISABLE
    conn.modify(dn, {"userAccountControl": [("MODIFY_REPLACE", 514)]})
    conn.unbind()
