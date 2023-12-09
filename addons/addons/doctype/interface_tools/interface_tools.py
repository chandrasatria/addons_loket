# Copyright (c) 2023, DAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_site_name
from frappe.utils import cstr
import os
from os import listdir
from os.path import isfile, join

@frappe.whitelist()
def get_url_inter():
	site_name = site_name = cstr(frappe.local.site)
	return site_name

class InterfaceTools(Document):
	@frappe.whitelist()
	def get_cld_from_interface(self):
		from frappe.core.doctype.scheduled_job_type.scheduled_job_type import execute_event,execute_event_long
		execute_event_long(str(frappe.as_json(frappe.get_doc("Scheduled Job Type","Check CLD From Interface"))))

		frappe.msgprint("CLD Check has been queued. To check status, please go to <a href ='{}'>Check CLD From Interface</a> and check the latest execute.".format("http://{}/app/scheduled-job-log/view/list?scheduled_job_type=Check%20CLD%20From%20Interface".format(get_url_inter())))

		

@frappe.whitelist()
def interface_go_cld():
	command = """ cd /home/frappe/frappe-bench/ && bench --site 10.30.0.3 execute interface_loket.custom.check_cld """
	os.system(command)
			