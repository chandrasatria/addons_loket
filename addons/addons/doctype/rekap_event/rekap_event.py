# Copyright (c) 2023, DAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

@frappe.whitelist()
def create_je_si(rekap_event):

	target_doc = frappe.new_doc("Journal Entry")
	sumber_doc = frappe.get_doc("Rekap Event",rekap_event)

	target_doc.custom_event_id = sumber_doc.event_id
	target_doc.custom_rekap_event = sumber_doc.name

	new_project_doc = frappe.get_doc("Project",{"custom_event_id":sumber_doc.event_id})

	total_invoice = 0
	for row in sumber_doc.list_sales_invoice:
		sales_invoice_doc = frappe.get_doc("Sales Invoice",row.no_invoice)
		target_doc.append("accounts",{
			"account": sales_invoice_doc.debit_to,
			"credit": sales_invoice_doc.outstanding_amount,
			"credit_in_account_currency": sales_invoice_doc.outstanding_amount,
			"party_type" : "Customer",
			"party" : sales_invoice_doc.customer,
			"reference_type": "Sales Invoice",
			"reference_name": sales_invoice_doc.name,
			"event_id": sumber_doc.event_id,
			"project": new_project_doc.name
		})
		total_invoice += sales_invoice_doc.outstanding_amount

	target_doc.append("accounts",{
		"account": "201070202 - DEPOSIT - PARTNER - PGLS",
		"debit": total_invoice,
		"debit_in_account_currency": total_invoice,
		"event_id": sumber_doc.event_id,
		"project": new_project_doc.name
	})

	if total_invoice == 0:
		frappe.throw("Invoice sudah sepenuhnya terbayar.")

	return target_doc.as_dict()


@frappe.whitelist()
def create_je_ticket(rekap_event):
	target_doc = frappe.new_doc("Journal Entry")
	sumber_doc = frappe.get_doc("Rekap Event",rekap_event)

	target_doc.custom_event_id = sumber_doc.event_id
	target_doc.custom_rekap_event = sumber_doc.name

	new_project_doc = frappe.get_doc("Project",{"custom_event_id":sumber_doc.event_id})

	list_journal_terpakai = frappe.db.sql("""
		SELECT si.name,SUM(sii.debit)
		FROM `tabJournal Entry` si 
		JOIN `tabJournal Entry Account` sii ON sii.parent=si.name AND sii.account = "201070202 - DEPOSIT - PARTNER - PGLS"
		WHERE si.custom_event_id = "{}" 
		and si.docstatus = 1 
		and si.custom_rekap_event = "{}"
		AND (sii.custom_closing_document_log IS NULL OR sii.custom_closing_document_log = "")
		GROUP BY si.name
		""".format(target_doc.custom_event_id,target_doc.custom_rekap_event))
	si = 0
	if list_journal_terpakai:
		if list_journal_terpakai[0]:
			if list_journal_terpakai[0][1]:
				si = list_journal_terpakai[0][1]

	total_invoice = frappe.utils.flt(sumber_doc.total_uang_ticket) - frappe.utils.flt(si)

	target_doc.append("accounts",{
		"account": "201070202 - DEPOSIT - PARTNER - PGLS",
		"debit": total_invoice,
		"debit_in_account_currency": total_invoice,
		"event_id": sumber_doc.event_id,
		"project": new_project_doc.name
	})

	target_doc.append("accounts",{
		
		"credit": total_invoice,
		"credit_in_account_currency": total_invoice,
		"event_id": sumber_doc.event_id,
		"project": new_project_doc.name
	})

	if total_invoice == 0:
		frappe.throw("Invoice sudah sepenuhnya terbayar.")

	return target_doc.as_dict()


class RekapEvent(Document):
	@frappe.whitelist()
	def get_data(self):
		if self.event_id:
			list_invoice = frappe.db.sql("""
				SELECT si.name,si.grand_total
				FROM `tabSales Invoice` si 
				JOIN `tabSales Invoice Item` sii ON sii.parent=si.name 
				WHERE sii.event_id = "{}" and si.docstatus = 1 
				GROUP BY si.name
				""".format(self.event_id))

			list_pur_invoice = frappe.db.sql("""
				SELECT si.name,si.grand_total
				FROM `tabPurchase Invoice` si 
				JOIN `tabPurchase Invoice Item` sii ON sii.parent=si.name 
				WHERE sii.event_id = "{}" and si.docstatus = 1 
				GROUP BY si.name
				""".format(self.event_id))

			list_journal = frappe.db.sql("""
				SELECT si.name,SUM(sii.credit)
				FROM `tabJournal Entry` si 
				JOIN `tabJournal Entry Account` sii ON sii.parent=si.name AND sii.account = "201070202 - DEPOSIT - PARTNER - PGLS"
				WHERE si.custom_event_id = "{}" 
				and si.docstatus = 1 
				AND (sii.custom_closing_document_log IS NOT NULL OR sii.custom_closing_document_log != "")
				GROUP BY si.name
				""".format(self.event_id))

			self.list_sales_invoice = []
			self.list_purchase_invoice = []
			self.list_journal_entry = []

			total_invoice = 0
			total_pur_invoice = 0
			total_journal = 0

			for row in list_invoice:
				self.append("list_sales_invoice",{
					"no_invoice": row[0],
					"event_total": row[1]
				})
				total_invoice = total_invoice + frappe.utils.flt(row[1])

			self.total_piutang = total_invoice

			for row in list_pur_invoice:
				self.append("list_purchase_invoice",{
					"no_invoice": row[0],
					"event_total": row[1]
				})
				total_pur_invoice = total_pur_invoice + frappe.utils.flt(row[1])

			self.total_hutang = total_pur_invoice

			for row in list_journal:
				self.append("list_journal_entry",{
					"no_invoice": row[0],
					"event_total": row[1]
				})
				total_journal = total_journal + frappe.utils.flt(row[1])

			self.total_uang_ticket = total_journal

	@frappe.whitelist()
	def onload(self):
		if self.event_id:
			list_invoice = frappe.db.sql("""
				SELECT si.name,si.grand_total
				FROM `tabSales Invoice` si 
				JOIN `tabSales Invoice Item` sii ON sii.parent=si.name 
				WHERE sii.event_id = "{}" and si.docstatus = 1 
				GROUP BY si.name
				""".format(self.event_id))

			list_pur_invoice = frappe.db.sql("""
				SELECT si.name,si.grand_total
				FROM `tabPurchase Invoice` si 
				JOIN `tabPurchase Invoice Item` sii ON sii.parent=si.name 
				WHERE sii.event_id = "{}" and si.docstatus = 1 
				GROUP BY si.name
				""".format(self.event_id))

			list_journal = frappe.db.sql("""
				SELECT si.name,SUM(sii.credit)
				FROM `tabJournal Entry` si 
				JOIN `tabJournal Entry Account` sii ON sii.parent=si.name AND sii.account = "201070202 - DEPOSIT - PARTNER - PGLS"
				WHERE si.custom_event_id = "105008" 
				and si.docstatus = 1 
				AND (sii.custom_closing_document_log IS NOT NULL OR sii.custom_closing_document_log != "")
				GROUP BY si.name
				""".format(self.event_id))

			list_journal_terpakai = frappe.db.sql("""
				SELECT si.name,SUM(sii.debit)
				FROM `tabJournal Entry` si 
				JOIN `tabJournal Entry Account` sii ON sii.parent=si.name AND sii.account = "201070202 - DEPOSIT - PARTNER - PGLS"
				WHERE si.custom_event_id = "{}" 
				and si.docstatus = 1 
				and si.custom_rekap_event = "{}"
				AND (sii.custom_closing_document_log IS NULL OR sii.custom_closing_document_log = "")
				GROUP BY si.name
				""".format(self.event_id,self.name))

			self.list_sales_invoice = []
			self.list_purchase_invoice = []
			self.list_journal_entry = []
			self.list_journal_pelunasan = []

			total_invoice = 0
			total_pur_invoice = 0
			total_journal = 0
			total_journal_terpakai = 0

			for row in list_invoice:
				self.append("list_sales_invoice",{
					"no_invoice": row[0],
					"event_total": row[1]
				})
				total_invoice = total_invoice + frappe.utils.flt(row[1])

			self.total_piutang = total_invoice

			for row in list_pur_invoice:
				self.append("list_purchase_invoice",{
					"no_invoice": row[0],
					"event_total": frappe.utils.flt(row[1])
				})
				total_pur_invoice = total_pur_invoice + frappe.utils.flt(row[1])

			self.total_hutang = total_pur_invoice

			for row in list_journal:
				self.append("list_journal_entry",{
					"no_invoice": row[0],
					"event_total": frappe.utils.flt(row[1])
				})
				total_journal = total_journal + frappe.utils.flt(row[1])

			self.total_uang_ticket = total_journal

			for row in list_journal_terpakai:
				self.append("list_journal_pelunasan",{
					"no_invoice": row[0],
					"event_total": frappe.utils.flt(row[1])
				})
				total_journal_terpakai = total_journal_terpakai + frappe.utils.flt(row[1])

			for row in self.list_journal_pelunasan:
				row.db_update()
			self.total_uang_ticket_terpakai = total_journal_terpakai
			self.db_update()
