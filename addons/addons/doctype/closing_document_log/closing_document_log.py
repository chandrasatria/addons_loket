# Copyright (c) 2023, DAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ClosingDocumentLog(Document):
	pass

@frappe.whitelist()
def get_url_2():
	check = frappe.db.sql(""" SELECT name FROM `tabEvent Producer` LIMIT 1 """)
	if len(check) > 0:
		for row in check:
			if row[0] == "http://10.20.0.4:81":
				return row[0].replace(":81","")
			elif row[0] == "http://10.20.0.4":
				return row[0] + ":81"
	else:
		return "http://10.20.0.4:81"


@frappe.whitelist()
def patch_saldo_awal():
	list_data = frappe.db.sql("""select name,REPLACE(credit,",",".") FROM `tabJE Temp` WHERE credit LIKE "%,%";""")
	for row in list_data:
		frappe.db.sql("""update `tabGL Entry` SET credit = {}, credit_in_account_currency = {} WHERE voucher_no = "SALDO-AWAL-0{}"; """.format(row[1],row[1],row[0]))
		frappe.db.sql("""update `tabJournal Entry Account` SET credit = {}, credit_in_account_currency = {} WHERE parent = "SALDO-AWAL-0{}"; """.format(row[1],row[1],row[0]))
		frappe.db.sql("""update `tabJournal Entry` SET total_credit = {}, difference = {} WHERE name = "SALDO-AWAL-0{}"; """.format(row[1],0-frappe.utils.flt(row[1]),row[0]))
		print(row[0])

@frappe.whitelist()
def enqueue_create_saldo_awal():
	frappe.enqueue(method="addons.addons.doctype.closing_document_log.closing_document_log.create_saldo_awal",timeout=60000, queue='long')

@frappe.whitelist()
def create_saldo_awal():
	list_yang_mau_dibuat = frappe.db.sql("""
		SELECT
		`account`, `account_type`, `party_type`, `party`, `event_id`, `debit`, `credit`, `user_remark`,`name`
		FROM `tabJE Temp`

		WHERE name NOT IN (SELECT cheque_no FROM `tabJournal Entry` )
		ORDER BY ABS(`name`)
	""",as_dict=1)

	
	
	for row in list_yang_mau_dibuat:



		je_doc = frappe.new_doc("Journal Entry")
		je_doc.posting_date = "2023-07-31"
		je_doc.naming_series = "SALDO-AWAL-.#######"
		je_doc.company = "PT Global Loket Sejahtera"
		je_doc.cheque_no = row.name
		je_doc.cheque_date = je_doc.posting_date
		je_doc.user_remark = row.user_remark

		account_doc = frappe.get_doc("Account", row.account)
		if not row.party and not row.party_type and (account_doc.account_type == "Receivable" or account_doc.account_type == "Payable"):
			account_doc.account_type = ""
			account_doc.save()

		je_doc.append("accounts",{
			"account" : row.account,
			"debit" : row.debit,
			"debit_in_account_currency" : row.debit,
			"credit" : row.credit,
			"credit_in_account_currency" : row.credit,
			"event_id" : row.event_id,
			"party": row.party,
			"party_type": row.party_type,
			"user_remark":row.user_remark
		})

		je_doc.save()
		je_doc.submit()

		print(je_doc.cheque_no)

		frappe.db.commit()



@frappe.whitelist()
def create_je(self,method):
	if get_url_2() == "http://10.20.0.4":
		# create JE

		event_id = self.detail_list[0].event_id

		try:
			je_doc = frappe.get_doc("Journal Entry",{"custom_event_id":event_id})
			print("1")
		except:
			je_doc = frappe.new_doc("Journal Entry")
			je_doc.posting_date = self.date
			je_doc.custom_event_id = event_id
			print(event_id)

		for row in self.detail_list:
			get_account = frappe.get_doc("Loket Account",row.account)
			if get_account.account_link:
				account_doc = frappe.get_doc("Account",get_account.account_link)
				company_doc = frappe.get_doc("Company", account_doc.company)
				cost_center = company_doc.cost_center

				if frappe.get_doc("Account",get_account.account_link).account_type == "Receivable":

					# check apakah ada customer
					try:
						customer_doc = frappe.get_doc("Customer",{"event_owner_id":row.event_owner_code})
					except:
						new_customer_doc = frappe.new_doc("Customer")
						new_customer_doc.event_owner_id = row.event_owner_code
						new_customer_doc.customer_name = row.event_owner_code
						new_customer_doc.territory = "Indonesia"
						new_customer_doc.tax_id = "-"
						new_customer_doc.save()
						frappe.db.commit()

					finally:
						customer_doc = frappe.get_doc("Customer",{"event_owner_id":row.event_owner_code})

					if row.debit or row.credit:
						je_doc.append("accounts",{
							"account" : get_account.account_link,
							"debit" : row.debit,
							"debit_in_account_currency" : row.debit,
							"credit" : row.credit,
							"credit_in_account_currency" : row.credit,
							"event_id" : row.event_id,
							"party": customer_doc.name,
							"party_type": "Customer",
							"cost_center": cost_center
						})
				elif frappe.get_doc("Account",get_account.account_link).account_type == "Payable":

					# check apakah ada customer
					try:
						customer_doc = frappe.get_doc("Supplier",{"custom_event_owner_idneo_organization_id":row.event_owner_code})
					except:
						new_customer_doc = frappe.new_doc("Supplier")
						new_customer_doc.custom_event_owner_idneo_organization_id = row.event_owner_code
						new_customer_doc.supplier_name = row.event_owner_code
						new_customer_doc.supplier_group = "All Supplier Groups"
						new_customer_doc.territory = "Indonesia"
						new_customer_doc.tax_id = "-"
						new_customer_doc.save()
						frappe.db.commit()

					finally:
						customer_doc = frappe.get_doc("Supplier",{"custom_event_owner_idneo_organization_id":row.event_owner_code})

					if row.debit or row.credit:
						je_doc.append("accounts",{
							"account" : get_account.account_link,
							"debit" : row.debit,
							"debit_in_account_currency" : row.debit,
							"credit" : row.credit,
							"credit_in_account_currency" : row.credit,
							"event_id" : row.event_id,
							"party": customer_doc.name,
							"party_type": "Supplier",
							"cost_center": cost_center
						})
				else:
					if row.debit or row.credit:
						je_doc.append("accounts",{
							"account" : get_account.account_link,
							"debit" : row.debit,
							"debit_in_account_currency" : row.debit,
							"credit" : row.credit,
							"credit_in_account_currency" : row.credit,
							"event_id" : row.event_id,
							"cost_center": cost_center
						})

		je_doc.flags.ignore_mandatory = True
		je_doc.flags.ignore_validate = True
		
		je_doc.save()
		if je_doc.docstatus == 1:
			repair_gl_entry_untuk_je(je_doc.name)


@frappe.whitelist()
def repair_gl_entry_untuk_je(docname):
	doctype = "Journal Entry"
	docu = frappe.get_doc(doctype, docname)	
	delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(docname))
	docu.make_gl_entries()

@frappe.whitelist()
def debug_create_je():

	if get_url_2() == "http://10.20.0.4":
		self = frappe.get_doc("Closing Document Log","CLD-0004")
		# create JE
		create_je(self,"validate")
	
		self = frappe.get_doc("Closing Document Log","CLD-0003")
		# create JE
		create_je(self,"validate")