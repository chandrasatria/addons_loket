from . import __version__ as app_version

app_name = "addons"
app_title = "Addons"
app_publisher = "DAS"
app_description = "addons"
app_email = "DAS@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/addons/css/addons.css"
# app_include_js = "/assets/addons/js/addons.js"

# include js, css files in header of web template
# web_include_css = "/assets/addons/css/addons.css"
# web_include_js = "/assets/addons/js/addons.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "addons/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
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
jinja = {
	# "methods": "addons.utils.jinja_methods",
	"filters": "addons.jinja.toTerbilang"
}

# Installation
# ------------

# before_install = "addons.install.before_install"
# after_install = "addons.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "addons.uninstall.before_uninstall"
# after_uninstall = "addons.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "addons.notifications.get_notification_config"

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

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"CLD Log": {
		"after_insert": "addons.addons.doctype.cld_log.cld_log.create_je"
	},
	"Invoice Log": {
		"after_insert": "addons.addons.doctype.invoice_log.invoice_log.create_invoice_log"
	},
	"Journal Entry":{
		"autoname": "addons.addons.doctype.cld_log.cld_log.create_je_autoname",
		"validate": "addons.custom_method.patch_cost_center",
	},
	"ACF Log": {
		"after_insert": "addons.addons.doctype.acf_log.acf_log.create_je"
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"addons.tasks.all"
#	],
#	"daily": [
#		"addons.tasks.daily"
#	],
#	"hourly": [
#		"addons.tasks.hourly"
#	],
#	"weekly": [
#		"addons.tasks.weekly"
#	],
#	"monthly": [
#		"addons.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "addons.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "addons.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "addons.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["addons.utils.before_request"]
# after_request = ["addons.utils.after_request"]

# Job Events
# ----------
# before_job = ["addons.utils.before_job"]
# after_job = ["addons.utils.after_job"]

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
#	"addons.auth.validate"
# ]
