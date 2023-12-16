import frappe

@frappe.whitelist()
def supplier_advance_account(supplier=None):
    account = None
    if supplier:
        query = f""" select account_for_advance from `tabParty Account`
            where parent = "{supplier}" and parenttype= "Supplier" """
        account = frappe.db.sql(query, pluck='name')[0]
    return account
