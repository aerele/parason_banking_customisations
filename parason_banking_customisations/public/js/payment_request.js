frappe.ui.form.on('Payment Request', {
	refresh(frm) {
		if(frm.doc.status == "Initiated") {
			frm.remove_custom_button(__('Create Payment Entry'))
		}
	}
})