frappe.ui.form.on('Payment Request', {
	refresh(frm) {
		if(frm.doc.status == "Initiated") {
			frm.remove_custom_button(__('Create Payment Entry'))
		}
	},
	mode_of_payment (frm) {
		var conditions = get_bank_query_conditions(frm);
		if (frm.doc.mode_of_payment == "Wire Transfer") {
			frm.set_query("bank_account", function() {
				return {
					filters: conditions
				};
			});
		}
	},
	party_type (frm) {
		var conditions = get_bank_query_conditions(frm);
		if (frm.doc.mode_of_payment == "Wire Transfer") {
			frm.set_query("bank_account", function() {
				return {
					filters: conditions
				};
			});
		}
	},
	party (frm) {
		var conditions = get_bank_query_conditions(frm);
		if (frm.doc.mode_of_payment == "Wire Transfer") {
			frm.set_query("bank_account", function() {
				return {
					filters: conditions
				};
			});
		}
		if(frm.doc.party_type == "Supplier"){
			frm.events.supplier_advance_account(frm)
		}
	},
	// onload: (frm) => {
	// 	frm.events.supplier_advance_account(frm)
	// },
	supplier_advance_account: (frm) => {
        frappe.call('parason_banking_customisations.frappe_call.supplier_advance_account', {
            supplier: frm.doc.party
        }).then(r => {
            frm.set_value("custom_account_paid_to", r.message)
        })
    }
});

var get_bank_query_conditions = function(frm) {
	var conditions = {
		workflow_state: "Approved"
	}
	if (frm.doc.party_type) {
		conditions["party_type"] = frm.doc.party_type;
	}
	if (frm.doc.party) {
		conditions["party"] = frm.doc.party;
	}
	if (frm.doc.mode_of_payment == "Wire Transfer") {
		frm.set_query("bank_account", function() {
			return {
				filters: conditions
			};
		});
	}
	return conditions;
};