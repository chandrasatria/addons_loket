# Copyright (c) 2023, DAS and contributors
# For license information, please see license.txt

import frappe
from frappe.frappeclient import FrappeClient
from frappe.model.document import Document

class QuotationCommission(Document):
	@frappe.whitelist()
	def validate(self):
		event_pro = frappe.db.sql(""" 
			SELECT ec.name FROM `tabEvent Producer` ec
			JOIN `tabEvent Producer Document Type` ecdt ON ec.name = ecdt.parent
			WHERE ecdt.ref_doctype = "CLD Log"
			""")
		if len(event_pro) > 0:
			for row in event_pro:
				doc_event_pro = frappe.get_doc("Event Producer", row[0])
				url = doc_event_pro.name
				api_key = doc_event_pro.api_key
				api_secret = doc_event_pro.get_password("api_secret")

				producer_site = FrappeClient(
					url=url,
					api_key=api_key,
					api_secret=api_secret,
				)

				for row_item in self.commission_item:
					docs = producer_site.post_request(
						{
							"cmd": "interface_loket.custom.return_acquiring_code",
							"item_code": row_item.item
						}
					)
					if not docs:
						frappe.throw(""" Item "{}" is not assigned to Acquiring Code in Interface.""".format(row_item.item))
					else:
						row_item.acquiring_code = docs[0][0]

	@frappe.whitelist()
	def before_submit(self):
		cld_doc = frappe.new_doc("QC Entry")
		cld_doc.posting_date = self.posting_date
		cld_doc.quotation_name = self.name
		cld_doc.customer = self.customer
		for row in self.commission_item:
			cld_doc.append("commission_item",{
				"item": row.item,
				"acquiring_code": row.acquiring_code,
				"event_id": row.event_id,
				"qty": row.qty,
				"uom": row.uom,
				"amount": row.amount,
				"percent": row.percent
			})
		cld_doc.save()
