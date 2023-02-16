// Copyright (c) 2023, Aerele Technologies Private Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Mode of Transfer', {
	bank: function(frm) {
		frm.set_query("bank_account", function() {
			return {
				filters: {
					bank: frm.doc.bank,
					is_company_account: 1
				}
			};
		});
	}
});
