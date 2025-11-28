from config import Config
from db import get_conn
from provisioning.ad import create_ad_user, disable_ad_user
from provisioning.vsphere import create_vsphere_vm, delete_vsphere_vm
from provisioning.ansible_join import join_domain
from provisioning.ansible_remove import unjoin_domain


def _get_department_key(emp):
    """
    Normalize department to one of: HR, IT, Finance, Marketing.
    Uses department_name if present; otherwise looks it up.
    """
    name = emp.get("department_name")
    if not name:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM departments WHERE id=%s", (emp["department_id"],))
                row = cur.fetchone()
                if row:
                    name = row["name"]
        finally:
            conn.close()

    if not name:
        return "IT"   # fallback

    upper = name.strip().upper()
    if upper == "HR":
        return "HR"
    if upper == "IT":
        return "IT"
    if upper == "FINANCE":
        return "Finance"
    if upper == "MARKETING":
        return "Marketing"

    return "IT"  # sane default


def provision_employee(emp, ad_password):
    """
    Called from create_employee() after DB insert.
    emp: dict row from employees table.
    ad_password: plaintext password chosen in HR form.
    """
    ad_username = emp["ad_username"]
    first = emp["first_name"]
    last = emp["last_name"]
    email = emp["email"]

    dept_key = _get_department_key(emp)

    user_ou = Config.AD_USER_OU.get(dept_key)
    if not user_ou:
        user_ou = next(iter(Config.AD_USER_OU.values()))

    computer_ou = Config.AD_COMPUTER_OU.get(dept_key)
    if not computer_ou:
        computer_ou = next(iter(Config.AD_COMPUTER_OU.values()))

    # 1) Create AD user in correct Users OU
    create_ad_user(
        ad_username=ad_username,
        first_name=first,
        last_name=last,
        email=email,
        password=ad_password,
        ou_dn=user_ou,
    )

    # 2) Clone VM from template
    vm_name = f"vm-{ad_username}"
    create_vsphere_vm(vm_name)

    # 3) Join VM to domain (computer object in correct Computers OU)
    join_domain(vm_name, computer_ou)

    return vm_name


def deprovision_employee(emp):
    """
    Called from deactivate_employee().
    """
    ad_username = emp["ad_username"]
    vm_name = emp.get("vm_name")

    # 1) Disable AD user (we keep the object but disabled)
    disable_ad_user(ad_username)

    # 2) Try unjoining from domain (if VM still reachable)
    if vm_name:
        try:
            unjoin_domain(vm_name)
        except Exception as e:
            print("WARNING: unjoin_domain failed:", e)

    # 3) Delete VM from vSphere
    if vm_name:
        try:
            delete_vsphere_vm(vm_name)
        except Exception as e:
            print("WARNING: delete_vsphere_vm failed:", e)

    return True
