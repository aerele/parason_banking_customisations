frappe.ui.form.on('Payment Order', {
	refresh(frm) {
		frm.remove_custom_button("Payment Entry", "Get Payments from");
		frm.remove_custom_button("Payment Request", "Get Payments from");
		if (frm.doc.docstatus == 0) {
			frm.add_custom_button(__('Payment Request'), function() {
				frm.trigger("remove_row_if_empty");
				erpnext.utils.map_current_doc({
					method: "parason_banking_customisations.parason_banking_customisations.doc_events.payment_request.make_payment_order",
					source_doctype: "Payment Request",
					target: frm,
					setters: {
						party: frm.doc.supplier || "",
						grand_total: "",
					},
					get_query_filters: {
						docstatus: 1,
						status: ["in", ["Initiated", "Partially Paid"]],
						mode_of_payment: "Wire Transfer",
						transaction_date : ["<=", frm.doc.posting_date]
					}
				});
			}, __("Get from"));

			frm.add_custom_button(__('Purchase Invoice'), function() {
				frm.trigger("remove_row_if_empty");
				erpnext.utils.map_current_doc({
					method: "parason_banking_customisations.parason_banking_customisations.doc_events.purchase_invoice.make_payment_order",
					source_doctype: "Purchase Invoice",
					target: frm,
					setters: {
						supplier: "",
						outstanding_amount: "",
						status: ""
					},
					get_query_filters: {
						docstatus: 1,
						status: ["not in", ["Hold on Payments"]],
						due_date : ["<=", frm.doc.posting_date],
						outstanding: [">", 0]
					}
				});
			}, __("Get from"));
			frm.trigger("remove_button")
		}
	},
	remove_button: function(frm) {
		// remove custom button of order type that is not imported

		let label = ["Payment Request", "Purchase Invoice"];

		if (frm.doc.references.length > 0 && frm.doc.payment_order_type) {
			label = label.reduce(x => {
				x!= frm.doc.payment_order_type;
				return x;
			});
			frm.remove_custom_button(label, "Get from");
		}
	},
	get_summary: function(frm) {
		frappe.call({
			method: "parason_banking_customisations.parason_banking_customisations.doc_events.payment_order.get_supplier_summary",
			args: {
				references: frm.doc.references,
			},
			freeze: true,
			callback: function(r) {
				if(r.message) {
					let summary_data = r.message
					frm.clear_table("summary");
					for (var i = 0; i < summary_data.length; i++) {
						let row = frm.add_child("summary");
						row.supplier = summary_data[i].supplier;
						row.amount = summary_data[i].amount;
						// frm.trigger('mode_of_transfer');
					}
					frm.refresh_field("summary");
				}
			}
		});
	},

})