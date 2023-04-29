frappe.ui.form.on('Payment Order', {
	onload(frm) {
		frm.set_df_property("payment_order_type", "options", [""].concat(["Payment Request", "Payment Entry", "Purchase Invoice"]));
		frm.refresh_field("payment_order_type");
	},
	refresh(frm) {
		frm.set_df_property('summary', 'cannot_delete_rows', true);
		frm.set_df_property('summary', 'cannot_add_rows', true);
		frm.remove_custom_button("Payment Entry", "Get Payments from");
		frm.remove_custom_button("Payment Request", "Get Payments from");
		frm.set_df_property("payment_order_type", "options", [""].concat(["Payment Request", "Payment Entry", "Purchase Invoice"]));
		frm.refresh_field("payment_order_type");
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
						status: ["in", ["Initiated"]],
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
						on_hold: ["!=", 1],
						due_date : ["<=", frm.doc.posting_date],
						outstanding: [">", 0]
					}
				});
			}, __("Get from"));
		};
		if (frm.doc.docstatus===1 && frm.doc.payment_order_type==='Payment Request') {
			frm.remove_custom_button(__('Create Payment Entries'));
		}
		if (frm.doc.status == "Pending" && frm.doc.docstatus == 1) {
			if (frm.has_perm('write') && 'summary' in frm.doc) {
				var uninitiated_payments = 0;
				for(var i = 0; i < frm.doc.summary.length; i++) {
					if (!frm.doc.summary[i].payment_initiated) {
						uninitiated_payments += 1
					}
				}
				if (uninitiated_payments > 0) {
					frm.add_custom_button(__('Initiate Payment'), function() {
						frappe.call({
							method: "parason_banking_customisations.parason_banking_customisations.doc_events.payment_order.make_bank_payment",
							args: {
								docname: frm.doc.name,
							},
							callback: function(r) {
								if(r.message) {
									frappe.msgprint(r.message)
								}
								frm.reload_doc();
							}
						});
					});
				}
			}
		}

	},
	after_workflow_action(frm) {
		// if (frm.doc.workflow_state == "Approved") {
		// 	frappe.call({
		// 		method: "parason_banking_customisations.parason_banking_customisations.doc_events.payment_order.make_payment_entries",
		// 		args: {
		// 			docname: frm.doc.name,
		// 		},
		// 		callback: function(r) {
		// 			if(r.message) {
		// 				//
		// 			}
		// 		}
		// 	});
		// 	frappe.call({
		// 		method: "parason_banking_customisations.parason_banking_customisations.doc_events.payment_order.log_payload",
		// 		args: {
		// 			docname: frm.doc.name,
		// 		},
		// 		callback: function(r) {
		// 			if(r.message) {
		// 				//
		// 			}
		// 		}
		// 	});
		// }
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
		if (frm.doc.docstatus > 0) {
			frappe.msgprint("Not allowed to change post submission");
			return
		}
		frappe.call({
			method: "parason_banking_customisations.parason_banking_customisations.doc_events.payment_order.get_supplier_summary",
			args: {
				references: frm.doc.references,
				company_bank_account: frm.doc.company_bank_account
			},
			freeze: true,
			callback: function(r) {
				if(r.message) {
					let summary_data = r.message
					frm.clear_table("summary");
					var doc_total = 0
					for (var i = 0; i < summary_data.length; i++) {
						doc_total += summary_data[i].amount
						let row = frm.add_child("summary");
						row.supplier = summary_data[i].supplier;
						row.supplier_name = summary_data[i].supplier_name;
						row.amount = summary_data[i].amount;
						row.bank_account = summary_data[i].bank_account;
						row.account = summary_data[i].account;
						row.mode_of_transfer = summary_data[i].mode_of_transfer;
						row.plant = summary_data[i].plant;
					}
					frm.refresh_field("summary");
					frm.doc.total = doc_total;
					frm.refresh_fields();
				}
			}
		});
	},
	update_status: function(frm) {
		if (frm.doc.docstatus != 1) {
			frappe.msgprint("Updating status is not allowed without submission");
			return
		}

		if (!frm.doc.approval_status) {
			frappe.msgprint("Updating status is not allowed without value");
			return
		}

		var selected_rows = frm.get_selected()
		if (!Object.keys(selected_rows).length || !"summary" in selected_rows){
			frappe.msgprint("No rows are selected");
			return
		}

		frappe.call({
			method: "parason_banking_customisations.parason_banking_customisations.doc_events.payment_order.modify_approval_status",
			args: {
				items: selected_rows.summary,
				approval_status: frm.doc.approval_status,
			},
			callback: function(r) {
				if(r.message) {
					var updated_count = 0
					for (var line_item in r.message) {
						if (r.message[line_item].status) {
							frappe.model.set_value("Payment Order Summary", line_item, "approval_status", r.message[line_item].message);
							updated_count += 1
						} else {
							frappe.msgprint(r.message[line_item].message)
						}
					}
					frappe.msgprint(updated_count + " record(s) updated.")
				}
				frm.dirty();
				frm.refresh_fields();
			}
		});
	}

})