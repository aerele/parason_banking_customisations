frappe.ui.form.on('Purchase Invoice', {
	refresh(frm) {
		if (frm.doc.supplier) {
			frm.set_query("bank_account", function() {
				return {
					filters: {
						party_type: "Supplier",
						party: frm.doc.supplier,
						workflow_state: "Approved"
					}
				};
			});
		}
	}
})