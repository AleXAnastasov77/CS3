import threading
from config import Config
from db import get_conn
from provisioning.ad import create_ad_user, disable_ad_user
from provisioning.vsphere import create_vsphere_vm, delete_vsphere_vm
from provisioning.ansible_join import join_domain
from provisioning.ansible_remove import unjoin_domain

# -------------------------------------------------------------------
# In-memory provisioning status (no DB changes)
# -------------------------------------------------------------------

PROVISION_STATUS = {}  # key = ad_username, value = string status


def _set_status(username, status: str):
    PROVISION_STATUS[username] = status
    print(f"[STATUS] {username}: {status}")


# -------------------------------------------------------------------
# Department helper (unchanged)
# -------------------------------------------------------------------

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
                cur.execute(
                    "SELECT name FROM departments WHERE id=%s",
                    (emp["department_id"],)
                )
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


# -------------------------------------------------------------------
# Background worker: only the slow domain join
# -------------------------------------------------------------------

def _domain_join_worker(ad_username, vm_ip, computer_ou):
    try:
        _set_status(ad_username, "joining_domain")
        join_domain(vm_ip, computer_ou)
        _set_status(ad_username, "completed")
    except Exception as e:
        _set_status(ad_username, f"failed: {e}")


# -------------------------------------------------------------------
# Provision: called from create_employee()
# -------------------------------------------------------------------

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

    # Determine department OUs
    dept_key = _get_department_key(emp)

    user_ou = Config.AD_USER_OU.get(dept_key)
    if not user_ou:
        user_ou = next(iter(Config.AD_USER_OU.values()))

    computer_ou = Config.AD_COMPUTER_OU.get(dept_key)
    if not computer_ou:
        computer_ou = next(iter(Config.AD_COMPUTER_OU.values()))

    # -------------------------
    # 1) Create AD User
    # -------------------------
    _set_status(ad_username, "creating_ad_user")
    create_ad_user(
        ad_username=ad_username,
        first_name=first,
        last_name=last,
        email=email,
        password=ad_password,
        ou_dn=user_ou,
    )

    # -------------------------
    # 2) Clone VM from template (sync)
    #    create_vsphere_vm returns the VM IP now
    # -------------------------
    vm_name = f"vm-{ad_username}"
    _set_status(ad_username, "cloning_vm")
    vm_ip = create_vsphere_vm(vm_name)
    print(f"[INFO] VM '{vm_name}' IP acquired: {vm_ip}")
    _set_status(ad_username, "vm_ready")

    # -------------------------
    # 3) Join VM to domain (ASYNC)
    #    IMPORTANT: use IP, not hostname
    # -------------------------
    _set_status(ad_username, "queued_for_domain_join")
    t = threading.Thread(
        target=_domain_join_worker,
        args=(ad_username, vm_ip, computer_ou),
        daemon=True,
    )
    t.start()

    # API still gets the same return type as before
    return vm_name, vm_ip


# -------------------------------------------------------------------
# Deprovision: keeps your warning prints
# -------------------------------------------------------------------

def deprovision_employee(emp):
    """
    Called from deactivate_employee().
    """
    ad_username = emp["ad_username"]
    vm_name = emp.get("vm_name")

    # 1) Disable AD user
    disable_ad_user(ad_username)

    # 2) Try unjoining from domain (if VM still reachable)
    if vm_name:
        try:
            unjoin_domain(vm_name)  # unjoin still uses hostname/IP check inside
        except Exception as e:
            print("WARNING: unjoin_domain failed:", e)

    # 3) Delete VM
    if vm_name:
        try:
            delete_vsphere_vm(vm_name)
        except Exception as e:
            print("WARNING: delete_vsphere_vm failed:", e)

    # Drop any in-memory status
    PROVISION_STATUS.pop(ad_username, None)

    return True
