from . import __version__ as app_version

app_name = "parason_banking_customisations"
app_title = "Parason Banking Customisations"
app_publisher = "Aerele Technologies Private Limited"
app_description = "Customisations related to Bank Integrations for Parason"
app_email = "hello@aerele.in"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/parason_banking_customisations/css/parason_banking_customisations.css"
# app_include_js = "/assets/parason_banking_customisations/js/parason_banking_customisations.js"

# include js, css files in header of web template
# web_include_css = "/assets/parason_banking_customisations/css/parason_banking_customisations.css"
# web_include_js = "/assets/parason_banking_customisations/js/parason_banking_customisations.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "parason_banking_customisations/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Bank Account" : "public/js/bank_account.js",
	"Payment Request": "public/js/payment_request.js",
	"Payment Order" : "public/js/payment_order.js",
	"Purchase Invoice" : "public/js/purchase_invoice.js",
}
doctype_list_js = {"Payment Order" : "public/js/payment_order_list.js",}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "parason_banking_customisations.utils.jinja_methods",
#	"filters": "parason_banking_customisations.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "parason_banking_customisations.install.before_install"
# after_install = "parason_banking_customisations.install.after_install"
after_install = "parason_banking_customisations.parason_banking_customisations.install.after_install"


# Uninstallation
# ------------

# before_uninstall = "parason_banking_customisations.uninstall.before_uninstall"
# after_uninstall = "parason_banking_customisations.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "parason_banking_customisations.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

override_doctype_class = {
	"Payment Order": "parason_banking_customisations.parason_banking_customisations.override.payment_order.CustomPaymentOrder",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Bank Account": {
		"validate": "parason_banking_customisations.parason_banking_customisations.doc_events.bank_account.validate_ifsc_code",
	},
	"Purchase Invoice": {
		"on_submit": "parason_banking_customisations.parason_banking_customisations.doc_events.purchase_invoice.hold_invoice_for_payment",
		"on_update_after_submit": "parason_banking_customisations.parason_banking_customisations.doc_events.purchase_invoice.on_update_after_submit",
	},
	"Payment Request": {
		"validate": "parason_banking_customisations.parason_banking_customisations.doc_events.payment_request.valdidate_bank_for_wire_transfer",
	},
	"Payment Order": {
		"validate": "parason_banking_customisations.parason_banking_customisations.doc_events.payment_order.validate",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"parason_banking_customisations.tasks.all"
#	],
#	"daily": [
#		"parason_banking_customisations.tasks.daily"
#	],
#	"hourly": [
#		"parason_banking_customisations.tasks.hourly"
#	],
#	"weekly": [
#		"parason_banking_customisations.tasks.weekly"
#	],
#	"monthly": [
#		"parason_banking_customisations.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "parason_banking_customisations.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "parason_banking_customisations.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "parason_banking_customisations.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]


# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"parason_banking_customisations.auth.validate"
# ]

fixtures = [
    {"dt": "Custom Field", "filters": [
        [
            "name", "in", [
                "Payment Request-custom_account_paid_to"
            ]
        ]
    ]}
]