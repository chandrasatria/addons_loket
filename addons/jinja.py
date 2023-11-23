from num2words import num2words
import frappe
import datetime
from datetime import date

@frappe.whitelist()
def toTerbilang(num):
  indo = num2words(num, lang='id').title()
  return indo

@frappe.whitelist()
def hari(tanggal):
  days = ["Senin", "Selasa", "Rabu", "Kamis", "Jum'at", "Sabtu", "Minguu"]
  test = datetime.datetime.today().weekday()
  output = days[test]

  return output

@frappe.whitelist()
def tgl(name):
  today = date.today()

  return today.strftime("%d %B %Y")

@frappe.whitelist()
def cek_pinv(name):
  if frappe.db.exists("Purchase Invoice Item",{"purchase_receipt":name}):
    return True
  else:
    return False
