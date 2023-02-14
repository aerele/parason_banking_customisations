frappe.ui.form.on('Bank Account', {
	refresh(frm) {
		if (frm.doc.workflow_state == 'Approved') {
			frm.set_read_only();
		}
	},
	onload(frm){
		if (frm.doc.workflow_state == 'Approved') {
			frm.set_read_only();
		}
	},
	after_workflow_action: function (frm) {
		if (frm.doc.workflow_state == 'Approved') {
			frm.set_read_only();
		}
		frm.reload_doc();
	},
})