app_name = "fateh_logistics"
app_title = "Fateh Logistics"
app_publisher = "ramees@enfono.com"
app_description = "custom app for logistics module"
app_email = "ramees@enfono.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "fateh_logistics",
# 		"logo": "/assets/fateh_logistics/logo.png",
# 		"title": "Fateh Logistics",
# 		"route": "/fateh_logistics",
# 		"has_permission": "fateh_logistics.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/fateh_logistics/css/fateh_logistics.css"
app_include_js = [
    "assets/fateh_logistics/js/driver_quick_entry.js",
    "assets/fateh_logistics/js/vehicle_quick_entry.js"
]

# include js, css files in header of web template
# web_include_css = "/assets/fateh_logistics/css/fateh_logistics.css"
# web_include_js = "/assets/fateh_logistics/js/fateh_logistics.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "fateh_logistics/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    # "Purchase Order": "public/js/purchase_order.js",
    # "Sales Order": "public/js/sales_order.js",
    # "Quotation": "public/js/quotation.js",
    "Vehicle": "public/js/vehicle.js",
    "Driver": "public/js/driver.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "fateh_logistics/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "fateh_logistics.utils.jinja_methods",
# 	"filters": "fateh_logistics.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "fateh_logistics.install.before_install"
# after_install = "fateh_logistics.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "fateh_logistics.uninstall.before_uninstall"
# after_uninstall = "fateh_logistics.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "fateh_logistics.utils.before_app_install"
# after_app_install = "fateh_logistics.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "fateh_logistics.utils.before_app_uninstall"
# after_app_uninstall = "fateh_logistics.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "fateh_logistics.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Vehicle": "fateh_logistics.fateh_logistics.override.vehicle.Vehicle"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Expense Request": {
		"on_update": "fateh_logistics.api.setup"
	},
    "Sales Invoice": {
        "before_submit": "fateh_logistics.api.validate_job_record_sales_invoice"
    }
    # "Purchase Order": {
    #     "on_submit": "fateh_logistics.po_hooks.update_job_record_percent",
    #     "on_cancel": "fateh_logistics.po_hooks.update_job_record_percent",
    #     "on_amend": "fateh_logistics.po_hooks.update_job_record_percent"
    # },
    # "Purchase Invoice": {
    #     "on_submit": "fateh_logistics.po_hooks.update_job_record_percent",
    #     "on_cancel": "fateh_logistics.po_hooks.update_job_record_percent",
    #     "on_amend": "fateh_logistics.po_hooks.update_job_record_percent"
    # },
    # "Purchase Receipt": {
    #     "on_submit": "fateh_logistics.po_hooks.update_job_record_percent",
    #     "on_cancel": "fateh_logistics.po_hooks.update_job_record_percent",
    #     "on_amend": "fateh_logistics.po_hooks.update_job_record_percent"
    # },
    # "Sales Order": {
    #     "on_submit": "fateh_logistics.po_hooks.update_job_record_percent",
    #     "on_cancel": "fateh_logistics.po_hooks.update_job_record_percent",
    #     "on_amend": "fateh_logistics.po_hooks.update_job_record_percent"
    # },
    # "Sales Invoice": {
    #     "on_submit": "fateh_logistics.po_hooks.update_job_record_percent",
    #     "on_cancel": "fateh_logistics.po_hooks.update_job_record_percent",
    #     "on_amend": "fateh_logistics.po_hooks.update_job_record_percent"
    # },
    # "Delivery Note": {
    #     "on_submit": "fateh_logistics.po_hooks.update_job_record_percent",
    #     "on_cancel": "fateh_logistics.po_hooks.update_job_record_percent",
    #     "on_amend": "fateh_logistics.po_hooks.update_job_record_percent"
    # }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"fateh_logistics.tasks.all"
# 	],
# 	"daily": [
# 		"fateh_logistics.tasks.daily"
# 	],
# 	"hourly": [
# 		"fateh_logistics.tasks.hourly"
# 	],
# 	"weekly": [
# 		"fateh_logistics.tasks.weekly"
# 	],
# 	"monthly": [
# 		"fateh_logistics.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "fateh_logistics.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "fateh_logistics.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "fateh_logistics.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["fateh_logistics.utils.before_request"]
# after_request = ["fateh_logistics.utils.after_request"]

# Job Events
# ----------
# before_job = ["fateh_logistics.utils.before_job"]
# after_job = ["fateh_logistics.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"fateh_logistics.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Custom fields for Sales Invoice
fixtures = [
    "Workflow", 
    "Workflow State", 
    "Workflow Action Master",

    "Client Script",
    "Server Script",

    {
        "dt": "Property Setter",
        "filters": [
            ["module", "=", "Fateh Logistics"]
        ]
    },

    {
        "dt": "Custom Field",
        "filters": [
            ["module", "=", "Fateh Logistics"]
        ]
    },

    {
        "dt": "Role",
        "filters": [
            ["name", "in", ["Operations Executive", "Warehouse Executive"]]
        ]
    },

    {
        "dt": "Vehicle Type"
    }
]
