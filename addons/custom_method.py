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

@frappe.whitelist()
def en_lakukan_pull_node():
	frappe.enqueue(method="addons.custom_method.lakukan_pull_node",timeout=18000, queue='long')

@frappe.whitelist()
def lakukan_pull_node():
	url = get_url().replace(":8000","")
	print(str(url))
	
	list_event_producer = frappe.db.sql(""" SELECT name FROM `tabEvent Producer` """)
	for row in list_event_producer:
		command = """ cd /home/frappe/frappe-bench/ && bench --site site1.local execute addons.custom_method.custom_pull_from_node --args "{{'{0}'}}" """.format(row[0])
		os.system(command)
		print(row[0])
		frappe.db.commit()

@frappe.whitelist()
def custom_pull_from_node(event_producer):
	"""pull all updates after the last update timestamp from event producer site"""
	# custom chandra
	# requires for ssl

	# event_producer = event_producer.replace("http://","https://")
			
	event_producer = frappe.get_doc('Event Producer', event_producer)
	user = event_producer.user
	producer_site = get_producer_site(event_producer.producer_url)
	print(event_producer.producer_url)
	last_update = event_producer.get_last_update()
	print(str(last_update))
	print('mau get config')
	(doctypes, mapping_config, naming_config) = get_config(event_producer.producer_doctypes)
	nama_db = "_a2f4a9ab74539819"
	# updates = get_updates(producer_site, last_update, doctypes)
	updates =  frappe.db.sql(""" SELECT 
			`update_type`, 
			`ref_doctype`,
			`docname`, `data`, `name`, `creation` 
			FROM `{}`.`tabEvent Update Log`  
			WHERE
			creation >= "{}"
			GROUP BY docname, `data`
			
			
			ORDER BY creation ASC
	""".format(nama_db,last_update), as_dict=1,debug=1)

		
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
