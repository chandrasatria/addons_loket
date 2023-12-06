import frappe,erpnext
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.item.item import get_item_defaults
from frappe.utils import cstr, flt, getdate, new_line_sep, nowdate, add_days, get_link_to_form, cint
from frappe.model.document import Document
from frappe.event_streaming.doctype.event_producer.event_producer import get_producer_site,get_config,get_updates,get_mapped_update,sync
import json
from frappe import msgprint, _

from frappe.utils.background_jobs import get_jobs
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
from erpnext.controllers.stock_controller import StockController
from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries, process_gl_map, ClosedAccountingPeriod, merge_similar_entries
from erpnext.stock import get_warehouse_account_map
from frappe.model.naming import make_autoname, revert_series_if_last

from frappe.utils.data import get_url, get_link_to_form
import datetime

from six import iteritems, itervalues, string_types
import os
from os import listdir
from os.path import isfile, join
from datetime import datetime,timedelta
from frappe.frappeclient import FrappeClient


@frappe.whitelist()
def buat_project_dari_cld():
	list_cld = frappe.db.sql(""" SELECT cld.event_id,cld.provit_segment,cle.event_name_long 
		FROM `tabCLD Log` cld JOIN `tabCLD Entry` cle ON cle.parent = cld.name 
		GROUP BY cld.event_id
		 """)
	for row in list_cld:
		try:
			new_project_doc = frappe.get_doc("Project",{"project_name":str(row[2]).replace('"','')})
			new_project_doc.custom_event_id = row[0]
			new_project_doc.project_type = row[1]
			new_project_doc.save()
			frappe.db.commit()
			print("sudah ada {}".format(row[0]))
		except:
			print("create baru {}".format(row[0]))
			new_project_doc = frappe.new_doc("Project")
			new_project_doc.custom_event_id = row[0]
			new_project_doc.project_type = row[1]
			new_project_doc.project_name = str(row[2]).replace('"','')
			new_project_doc.save()
			frappe.db.commit()
		try:
			event_doc = frappe.get_doc("Event ID", row[0])
			event_doc.project = new_project_doc.name
			event_doc.project_name = new_project_doc.project_name
			event_doc.save()
		except:
			event_doc = frappe.new_doc("Event ID")
			event_doc.event_id = row[0]
			event_doc.event_name = row[2]
			event_doc.project = new_project_doc.name
			event_doc.project_name = new_project_doc.project_name
			event_doc.save()



@frappe.whitelist()
def debug_patch_cost_center():

	list_closing = frappe.db.sql(""" SELECT name FROM `tabJournal Entry` WHERE  custom_provit_segment IS NOT NULL """)

	for row_bari in list_closing:
		
		closing_doc = frappe.get_doc("Journal Entry", row_bari[0])
		for row in closing_doc.accounts:
			account_doc = frappe.get_doc("Account", row.account)
			if account_doc.report_type == "Profit and Loss":
				if closing_doc.custom_provit_segment == "EN":
					row.cost_center = "Event Business Enterprise - PGLS"

				elif closing_doc.custom_provit_segment == "SS":
					row.cost_center = "Digital Business - PGLS"

				elif closing_doc.custom_provit_segment == "GB":
					row.cost_center = "Gotix Business - PGLS"

				row.db_update()

				if closing_doc.docstatus == 1:
					frappe.db.sql(""" UPDATE `tabGL Entry` SET cost_center = "{}" WHERE voucher_no = "{}" and account = "{}" """.format(row.cost_center,closing_doc.name,row.account))
					print(row_bari[0])

@frappe.whitelist()
def patch_cost_center(self,method):
	for row in self.accounts:
		account_doc = frappe.get_doc("Account", row.account)
		if account_doc.report_type == "Profit and Loss":
			if self.custom_provit_segment == "EN":
				row.cost_center = "Event Business Enterprise - PGLS"

			elif self.custom_provit_segment == "SS":
				row.cost_center = "Digital Business - PGLS"

			elif self.custom_provit_segment == "GB":
				row.cost_center = "Gotix Business - PGLS"

@frappe.whitelist()
def patch_je():

	list_je = frappe.db.sql(""" SELECT name FROM `tabJournal Entry` WHERE name LIKE "%NEO%" """)
	for row in list_je:
		je_doc = frappe.get_doc("Journal Entry",row[0])
		for account in je_doc.accounts:
			if account.account == "103010102 - TRADE RECEIVABLES ST - THIRD PARTIES - PGLS":
				cld_doc = frappe.get_doc("CLD Log",account.custom_closing_document_log)
				for detail in cld_doc.detail_list:
					if detail.account == "TRADE RECEIVABLES ST - THIRD PARTIES":
						if detail.acquiring_code == "MIDMID":
							account.party = "PT. MIDTRANS"
							account.db_update()
						if detail.acquiring_code == "FSPFAS":
							account.party = "PT. MEDIA INDONUSA"
							account.db_update()
						if detail.acquiring_code == "GJKDAB":
							account.party = "PT DOMPET ANAK BANGSA"
							account.db_update()
						if detail.acquiring_code == "MIDBCA":
							account.party = "PT. BANK CENTRAL ASIA TBK."
							account.db_update()
						if detail.acquiring_code == "MIDPER":
							account.party = "PT. BANK PERMATA, Tbk"
							account.db_update()
						if detail.acquiring_code == "OFLEMP":
							account.party = "OFFLINE EMPLOYEE"
							account.db_update()
						if detail.acquiring_code == "OFLEOU":
							account.party = "OFFLINE EMPLOYEE"
							account.db_update()



@frappe.whitelist()
def return_item(item_code):
	return frappe.db.sql(""" SELECT name,item_name FROM `tabItem` WHERE name = "{}" """.format(item_code))

@frappe.whitelist()
def return_account(expense_account):
	return frappe.db.sql(""" SELECT name FROM `tabAccount` WHERE name = "{}" """.format(expense_account))

@frappe.whitelist()
def return_customer(customer_name):
	return frappe.db.sql(""" SELECT name,customer_name FROM `tabCustomer` WHERE name = "{}" """.format(customer_name))
	
@frappe.whitelist()
def en_lakukan_pull_node():
	frappe.enqueue(method="addons.custom_method.lakukan_pull_node",timeout=18000, queue='long')

@frappe.whitelist()
def lakukan_pull_node():
	url = get_url().replace(":8000","")
	print(str(url))
	
	list_event_producer = frappe.db.sql(""" SELECT name FROM `tabEvent Producer` """)
	for row in list_event_producer:
		command = """ cd /home/frappe/frappe-bench/ && bench --site p-erp.intra.loket.id execute addons.custom_method.custom_pull_from_node --args "{{'{0}'}}" """.format(row[0])
		os.system(command)
		print(row[0])
		frappe.db.commit()


@frappe.whitelist()
def get_producer_site2():
	event_pro = frappe.db.sql(""" 
		SELECT ec.name 
		FROM `tabEvent Producer` ec 
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

			return producer_site

	return None

@frappe.whitelist()
def get_cld_not_exist():
	producer_site = get_producer_site2()
	if producer_site:

		sql_cld = frappe.db.sql(""" SELECT GROUP_CONCAT(name) FROM `tabCLD Log` GROUP BY name """)
		array_cld = []
		for row in sql_cld:
			array_cld.append(row[0])
		
		docs = producer_site.post_request(
			{
				"cmd": "interface_loket.custom.return_cld_not_exist",
				"array_cld": str(array_cld)
			}
		)
		if docs:
			print("{}1".format(docs))
			
@frappe.whitelist()
def check_cld(cld):
	hasil = frappe.db.sql(""" SELECT name FROM `tabCLD Log` WHERE name = "{}" """.format(cld))
	if len(hasil) > 0:
		return 1
	else:
		return 0



@frappe.whitelist()
def custom_pull_from_node(event_producer):
	"""pull all updates after the last update timestamp from event producer site"""
	# custom chandra
	# requires for ssl

	# event_producer = event_producer.replace("http://","https://")
			
	event_producer = frappe.get_doc('Event Producer', event_producer)
	user = event_producer.user
	producer_site = get_producer_site(event_producer.producer_url)
	
	last_update = event_producer.get_last_update()
	print(str(last_update))
	get_last_cld = frappe.db.sql(""" SELECT creation FROM `tabCLD Log` ORDER BY creation LIMIT 1 """)
	print('mau get config')
	(doctypes, mapping_config, naming_config) = get_config(event_producer.producer_doctypes)
	nama_db = "_c2138d7e24008804"
	# updates = get_updates(producer_site, get_last_cld[0][0], doctypes)
	updates = get_updates(producer_site, last_update, doctypes)
	# updates =  frappe.db.sql(""" SELECT 
	# 		`update_type`, 
	# 		`ref_doctype`,
	# 		`docname`, `data`, `name`, `creation` 
	# 		FROM `{}`.`tabEvent Update Log`  
	# 		WHERE
	# 		creation >= "{}"
	# 		GROUP BY docname, `data`
			
			
	# 		ORDER BY creation ASC
	# """.format(nama_db,last_update), as_dict=1,debug=1)

		
	for update in updates:
		print(str(update))

		update.use_same_name = naming_config.get(update.ref_doctype)
		mapping = mapping_config.get(update.ref_doctype)
		if mapping:
			update.mapping = mapping
			update = get_mapped_update(update, producer_site)
		if not update.update_type == 'Delete':
			update.data = json.loads(update.data)


			if "letter_head" in update.data:
				if update.data["letter_head"] != "":
					update.data["letter_head"] = ""
					
			if "docstatus" in update.data:
				if update.data["docstatus"] == "0":
					update.data["docstatus"] = 0

			if "additional_costs" in update.data:
				if update.data["additional_costs"] == "[]":
					update.data["additional_costs"] = []	

			if "amended_from" in update.data:
				if update.data["doctype"] == "Stock Entry":
					update.data["amended_from"] = ""
			
			if "workflow_state" in update.data:
				if update.data["doctype"] == "Stock Entry" and update.data["workflow_state"] == "Draft":
					update.data["workflow_state"] = "Pending"
					
			if "items" in update.data and update.data["doctype"] == "Stock Entry":
				for row in update.data["items"] :
					if "basic_rate" in row:
						if row["basic_rate"] == 0:
							row["allow_zero_valuation_rate"] = 1
						else:
							row["allow_zero_valuation_rate"] = 0
				
		print(str(update.docname))
		sync(update, producer_site, event_producer)
		frappe.db.commit()

@frappe.whitelist()
def debug_closing_doc():


	list_raw_data = frappe.db.sql(""" 
		SELECT name FROM `tabCLD Log` WHERE source_data = "G0tix"
	""")
	for row in list_raw_data:
		
		new_doc = frappe.get_doc("CLD Log",row[0])
		for row_baris in new_doc.detail_list:
			row_baris.event_id = new_doc.event_id
			row_baris.db_update()
		print(row[0])
		frappe.db.commit()