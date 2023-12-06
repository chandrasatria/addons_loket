# Copyright (c) 2023, DAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ACFLog(Document):
	pass


@frappe.whitelist()
def debug_create_je():
	self = frappe.get_doc("ACF Log","98296OCTXEKIPWCD")
	create_je(self,"validate")


@frappe.whitelist()
def create_je(self,method):
	event_pro = frappe.db.sql(""" 
		SELECT ec.name 
		FROM `tabEvent Producer` ec 
		JOIN `tabEvent Producer Document Type` ecdt ON ec.name = ecdt.parent
		WHERE ecdt.ref_doctype = "ACF Log"
	""")
	if len(event_pro) > 0:
		# create JE

		event_id = self.detail_list[0].event_id
		acquiring_code = self.detail_list[0].acquiring_code

		je_doc = frappe.new_doc("Journal Entry")
		je_doc.posting_date = self.date
		je_doc.custom_event_id = event_id
		je_doc.custom_closing_document_log = self.name
		je_doc.custom_source_data = self.source_data
		je_doc.custom_acquiring_code = acquiring_code
		je_doc.custom_provit_segment = self.provit_segment

		for row in self.detail_list:
			if row.account:
				account_doc = frappe.get_doc("Account",row.account)
				company_doc = frappe.get_doc("Company", account_doc.company)

				cost_center = ""

				if je_doc.custom_provit_segment == "EN":
					cost_center = "Event Business Enterprise - PGLS"

				elif je_doc.custom_provit_segment == "SS":
					cost_center = "Digital Business - PGLS"

				elif je_doc.custom_provit_segment == "GB" or self.source_data == "G0tix":
					cost_center = "Gotix Business - PGLS"


				try:
					new_project_doc = frappe.get_doc("Project",{"custom_event_id":row.event_id})
				except:
					try:
						new_project_doc = frappe.get_doc("Project",{"project_name":str(row.event_name_long).replace('"','')})
						new_project_doc.custom_event_id = row.event_id
						new_project_doc.save()
					except:
						new_project_doc = frappe.new_doc("Project")
						new_project_doc.custom_event_id = row.event_id
						new_project_doc.project_type = self.provit_segment
						new_project_doc.project_name = str(row.event_name_long).replace('"','')
						new_project_doc.save()
						frappe.db.commit()


				try:
					event_doc = frappe.get_doc("Event ID", row.event_id)
				except:
					event_doc = frappe.new_doc("Event ID")
					event_doc.event_id = row.event_id
					event_doc.event_name = row.event_name_long
					event_doc.project = new_project_doc.name
					event_doc.project_name = new_project_doc.project_name
					event_doc.save()
					frappe.db.commit()

				if account_doc.name == "103010102 - TRADE RECEIVABLES ST - THIRD PARTIES - PGLS":
					
					customer_doc = frappe.get_doc("Customer", row.customer)
					if row.debit or row.credit:
						je_doc.append("accounts",{
							"account" : account_doc.name,
							"debit" : row.debit,
							"debit_in_account_currency" : row.debit,
							"credit" : row.credit,
							"credit_in_account_currency" : row.credit,
							"event_id" : row.event_id,
							"party": customer_doc.name,
							"party_type": "Customer",
							"cost_center": cost_center,
							"custom_closing_document_log" : self.name,
							"project" : new_project_doc.name
						})

				else:
					if row.debit or row.credit:
						je_doc.append("accounts",{
							"account" : account_doc.name,
							"debit" : row.debit,
							"debit_in_account_currency" : row.debit,
							"credit" : row.credit,
							"credit_in_account_currency" : row.credit,
							"event_id" : row.event_id,
							"cost_center": cost_center,
							"custom_closing_document_log" : self.name,
							"project" : new_project_doc.name,
						})

		je_doc.flags.ignore_mandatory = True
		je_doc.flags.ignore_validate = True
		je_doc.set_total_debit_credit()
		je_doc.naming_series = "ACF-JV-.YYYY.-"
		je_doc.save()
		# if je_doc.docstatus == 1:
		# 	repair_gl_entry_untuk_je(je_doc.name)
		# else:
		# 	je_doc.save()