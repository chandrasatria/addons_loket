// Copyright (c) 2023, DAS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rekap Event', {
	refresh: function(frm) {
    
    	if(cur_frm.doc.total_uang_ticket_terpakai < cur_frm.doc.total_uang_ticket) {
	    	frm.add_custom_button(__("Create Pelunasan Sales Invoice"), function () {
		        frappe.xcall("addons.addons.doctype.rekap_event.rekap_event.create_je_si", {
		            rekap_event: cur_frm.doc.name,
		      
		        })
		        .then((journal_entry) => {
		            frappe.model.sync(journal_entry);
		            frappe.set_route("Form", journal_entry.doctype, journal_entry.name);
		        });
	      	},("Create"));
	      	frm.add_custom_button(__("Create Pelunasan Ticket"), function () {
		        frappe.xcall("addons.addons.doctype.rekap_event.rekap_event.create_je_ticket", {
		            rekap_event: cur_frm.doc.name,
		      
		        })
		        .then((journal_entry) => {
		            frappe.model.sync(journal_entry);
		            frappe.set_route("Form", journal_entry.doctype, journal_entry.name);
		        });
	      	},("Create"));
		}
	}
})

   