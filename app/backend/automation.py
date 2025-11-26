# Placeholder for Ansible calls.
# You can implement real Ansible integration here later.

def provision_employee(emp, ad_password):
    """
    emp = dict containing employee data from DB
    ad_password = plaintext password entered by HR for AD user

    This function will:
      - create AD user
      - create VM in vSphere
      - run Ansible script for domain join
    """

    ad_username = emp["ad_username"]
    first = emp["first_name"]
    last = emp["last_name"]
    email = emp["email"]
    department_id = emp["department_id"]

    # TODO: 1) Create user in Active Directory
    # create_ad_user(ad_username, first, last, email, ad_password)

    # TODO: 2) Provision VM on vSphere
    # vm_name = create_vsphere_vm(ad_username)

    # TODO: 3) Join VM to domain using Ansible
    # run_ansible_join(vm_name, ad_username, ad_password)

    # TEMPORARY placeholder until provisioning is implemented
    vm_name = f"vm-{ad_username}"

    return vm_name

def deprovision_employee(emp_row):
    # TODO: run ansible-playbook to delete VM and disable/remove AD account.
    return True
