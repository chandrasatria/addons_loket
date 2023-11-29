# Copyright (c) 2023, DAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname, revert_series_if_last

class CLDLog(Document):
	pass

@frappe.whitelist()
def get_url_2():
	check = frappe.db.sql(""" SELECT name FROM `tabEvent Producer` LIMIT 1 """)
	if len(check) > 0:
		from frappe.utils import cstr
		site_name = cstr(frappe.local.site)
		return site_name
	else:
		return "http://10.20.0.3"



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
	frappe.enqueue(method="addons.addons.doctype.cld_log.cld_log.create_saldo_awal",timeout=60000, queue='long')

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
	if get_url_2() == "p-erp.intra.loket.id":
		# create JE

		event_id = self.detail_list[0].event_id
		acquiring_code = self.detail_list[0].acquiring_code

		try:
			je_doc = frappe.get_doc("Journal Entry",{"custom_closing_document_log":self.name})
		except:
			je_doc = frappe.new_doc("Journal Entry")
			je_doc.posting_date = self.date
			je_doc.custom_event_id = event_id
			je_doc.custom_closing_document_log = self.name
			je_doc.custom_source_data = self.source_data
			je_doc.custom_acquiring_code = acquiring_code
			je_doc.custom_provit_segment = self.provit_segment

		for row in self.detail_list:
			get_account = frappe.get_doc("Loket Account",row.account)
			if get_account.account_link:
				account_doc = frappe.get_doc("Account",get_account.account_link)
				company_doc = frappe.get_doc("Company", account_doc.company)
				# check apakah ada event id
				# try:
				# 	new_project_doc = frappe.get_doc("Project",row.event_id)
				# except:
				# 	new_project_doc = frappe.new_doc("Project")
				# 	new_project_doc.project_name = row.event_id
				# 	new_project_doc.product_type = self.provit_segment
				# 	new_project_doc.save()
				# 	frappe.db.commit()

				# # check apakah ada event id
				# try:
				# 	event_doc = frappe.get_doc("Event ID",row.event_id)
				# except:
				# 	new_event_doc = frappe.new_doc("Event ID")
				# 	new_event_doc.event_name = row.event_name_long
				# 	new_event_doc.event_id = row.event_id
				# 	new_event_doc.save()
				# 	frappe.db.commit()

				cost_center = ""

				if je_doc.custom_provit_segment == "EN":
					cost_center = "Event Business Enterprise - PGLS"

				elif je_doc.custom_provit_segment == "SS":
					cost_center = "Digital Business - PGLS"

				elif je_doc.custom_provit_segment == "GB":
					cost_center = "Gotix Business - PGLS"


				try:
					new_project_doc = frappe.get_doc("Project",{"custom_event_id":row.event_id})
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

					if row.customer and row.account == "TRADE RECEIVABLES ST - THIRD PARTIES":
						customer_doc = frappe.get_doc("Customer", row.customer)

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
							"cost_center": cost_center,
							"custom_closing_document_log" : self.name,
							"project" : new_project_doc.name
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
							"cost_center": cost_center,
							"custom_closing_document_log" : self.name,
							"project" : new_project_doc.name
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
							"cost_center": cost_center,
							"custom_closing_document_log" : self.name,
							"project" : new_project_doc.name
						})

		je_doc.flags.ignore_mandatory = True
		je_doc.flags.ignore_validate = True
		je_doc.set_total_debit_credit()
		je_doc.naming_series = "SUMBER-CLD-.DD..MM..YYYY.-.#####"
		je_doc.save()
		if je_doc.docstatus == 1:
			repair_gl_entry_untuk_je(je_doc.name)
		else:
			je_doc.submit()
		

@frappe.whitelist()
def create_je_autoname(self,method):
	if self.naming_series == "SUMBER-CLD-.DD..MM..YYYY.-.#####":
		self.naming_series = "SUMBER-CLD-.DD..MM..YYYY.-.#####"
		day = frappe.utils.formatdate(frappe.utils.getdate(self.posting_date),"dd")
		month = frappe.utils.formatdate(frappe.utils.getdate(self.posting_date),"MM")
		year = frappe.utils.formatdate(frappe.utils.getdate(self.posting_date),"YYYY")
		sumber = ""
		if self.custom_source_data == "Neo":
			sumber = "NEO"
		else:
			sumber = "G0TIX"
		self.name = make_autoname(self.naming_series.replace("CLD",self.custom_closing_document_log).replace(".YYYY.",year).replace(".MM.",month).replace(".DD.",day).replace("SUMBER",sumber), doc=self)


@frappe.whitelist()
def repair_gl_entry_untuk_je(docname):
	doctype = "Journal Entry"
	docu = frappe.get_doc(doctype, docname)	
	delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(docname))
	docu.make_gl_entries()

@frappe.whitelist()
def debug_create_je():

	list_je = frappe.db.sql(""" SELECT name FROM `tabCLD Log` 
		where name in 
		("CLD-1512") """)

	for row in list_je:
		self = frappe.get_doc("CLD Log",row[0])
		# create JE
		create_je(self,"validate")
		frappe.db.commit()


@frappe.whitelist()
def debug_project_je():
	list_je = frappe.db.sql(""" 
		SELECT parent FROM `tabJournal Entry Account` 
		WHERE parent LIKE "%NEO%" or parent LIKE "%G0TIX%"
		AND parent IN (SELECT name FROM `tabEvent ID` WHERE project IS NOT NULL) GROUP BY parent
		 """)
	for row in list_je:
		print(row[0])
		je_doc = frappe.get_doc("Journal Entry",row[0])
		for baris in je_doc.accounts:
			if baris.event_id:
				event_id_doc = frappe.get_doc("Event ID",baris.event_id)
				if event_id_doc.get("project"):
					baris.project = event_id_doc.get("project")
				else:
					baris.project = ""
				baris.db_update()

		if je_doc.docstatus == 1:
			frappe.db.sql(""" UPDATE `tabGL Entry` SET project = "{}" WHERE voucher_no = "{}" """.format(baris.project,je_doc.name))
