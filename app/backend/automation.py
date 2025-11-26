# Placeholder for Ansible calls.
# You can implement real Ansible integration here later.

def provision_employee(emp_row):
    # emp_row is a dict from the DB: first_name, last_name, email, ad_username, department_id, etc.
    # TODO: run ansible-playbook here.
    vm_name = f"vm-{emp_row['ad_username']}"
    return vm_name

def deprovision_employee(emp_row):
    # TODO: run ansible-playbook to delete VM and disable/remove AD account.
    return True
