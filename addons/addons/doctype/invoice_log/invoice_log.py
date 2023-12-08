# Copyright (c) 2023, DAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class InvoiceLog(Document):
	pass

@frappe.whitelist()
def create_invoice_log_debug():
	self = frappe.get_doc("Invoice Log","109522")
	create_invoice_log(self,"validate")

@frappe.whitelist()
def create_invoice_log(self,method):
	# create Sales Invoice
	if self.event_owner_id:
		try:
			customer_doc = frappe.get_doc("Customer",{"event_owner_id":self.event_owner_id})
		except:
			new_customer_doc = frappe.new_doc("Customer")
			new_customer_doc.event_owner_id = self.event_owner_id
			new_customer_doc.customer_name = self.event_owner_id
			new_customer_doc.territory = "Indonesia"
			new_customer_doc.tax_id = "-"
			new_customer_doc.save()
			frappe.db.commit()

		finally:
			customer_doc = frappe.get_doc("Customer",{"event_owner_id":self.event_owner_id})

		receivable_account = "103010399 - SALES RECEIVABLE - PGLS"
		if customer_doc.accounts:
			for row in customer_doc.accounts:
				if row.company == "PT Global Loket Sejahtera":
					receivable_account = customer_doc.accounts[0].account


		new_doc = frappe.new_doc("Sales Invoice")
		new_doc.customer = customer_doc.name
		new_doc.items = []
		new_doc.company = "PT Global Loket Sejahtera"
		
		project_doc = frappe.get_doc("Project",{"custom_event_id":self.event_id})
		cost_center = ""
		if self.provit_segment == "EN":
			cost_center = "Event Business Enterprise - PGLS"

		elif self.provit_segment == "SS":
			cost_center = "Digital Business - PGLS"

		elif self.provit_segment == "GB":
			cost_center = "Gotix Business - PGLS"

		new_doc.append("items",{
			"item_code" : "Commision Fee",
			"item_name" : "Commision Fee",
			"qty": 1,
			"rate": frappe.utils.flt(self.total_commission),
			"amount": frappe.utils.flt(self.total_commission),
			"project": project_doc.name,
			"event_id": self.event_id,
			"cost_center": cost_center,
			"income_account": "401010101 - REVENUE - TICKETING - B2B - COMMISSION FEE - PGLS"
		})

		new_doc.debit_to = receivable_account

		new_doc.save()
		if self.provit_segment == "SS":
			new_doc.submit()

		# buat JE baru
		je_doc = frappe.new_doc("Journal Entry")
		je_doc.posting_date = self.closing_date
		je_doc.custom_event_id = event_id
		je_doc.custom_closing_document_log = self.name
		je_doc.custom_provit_segment = self.provit_segment
		je_doc.naming_series = "ECF-JV-.YYYY.-"

		cost_center = ""
		if je_doc.custom_provit_segment == "EN":
			cost_center = "Event Business Enterprise - PGLS"

		elif je_doc.custom_provit_segment == "SS":
			cost_center = "Digital Business - PGLS"

		elif je_doc.custom_provit_segment == "GB" or self.source_data == "G0tix":
			cost_center = "Gotix Business - PGLS"

		new_project_doc = frappe.get_doc("Project",{"custom_event_id":row.event_id})
		event_doc = frappe.get_doc("Event ID", row.event_id)

		if self.total_commission:
			je_doc.append("accounts",{
				"account" : "103010303 - ACCRUED TRADE RECEIVABLES - COMMISSION - PGLS",
				"debit" : 0,
				"debit_in_account_currency" : 0,
				"credit" : frappe.utils.flt(self.total_commission),
				"credit_in_account_currency" : frappe.utils.flt(self.total_commission),
				"event_id" : row.event_id,
				"cost_center": cost_center,
				"custom_closing_document_log" : self.name,
				"project" : new_project_doc.name,
			})
			comm_fee = frappe.utils.flt(self.total_commission)/1.11
			je_doc.append("accounts",{
				"account" : "402010101 - REV - PLATFORM - EVENT CREATOR - SERVICE FEE - PGLS",
				"debit" : comm_fee,
				"debit_in_account_currency" : comm_fee,
				"credit" : 0,
				"credit_in_account_currency" : 0,
				"event_id" : row.event_id,
				"cost_center": cost_center,
				"custom_closing_document_log" : self.name,
				"project" : new_project_doc.name,
			})
			je_doc.append("accounts",{
				"account" : "201020010 - ACCRUALS - VAT OUT (DOMESTIC) - PGLS",
				"debit" : comm_fee * 0.11
				"debit_in_account_currency" : comm_fee * 0.11,
				"credit" : 0,
				"credit_in_account_currency" : 0,
				"event_id" : row.event_id,
				"cost_center": cost_center,
				"custom_closing_document_log" : self.name,
				"project" : new_project_doc.name,
			})

		je_doc.save()
		je_doc.submit()