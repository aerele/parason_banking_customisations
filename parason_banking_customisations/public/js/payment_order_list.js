frappe.listview_settings['Payment Order'] = {
	onload: function(listview) {
		listview.page.add_menu_item(__("Update Status"), function() {
			method = "parason_banking_customisations.parason_banking_customisations.doc_events.payment_order.check_payment_status_bulk"
			listview.call_for_selected_items(method);
		});
	}
};