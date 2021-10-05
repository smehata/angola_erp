# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys



import frappe
from frappe import _
from frappe.utils import cint, random_string
from frappe.utils import cstr, flt, getdate, nowdate, formatdate
import requests



#OPENCBS entry 
#Read People, Savings, Contracts, SavingEvents .... 
#Entries to Account JV

@frappe.whitelist()
def opencbs_get_dados():
	#fonte should be the Page

	empresa = 'AngolaERP2'
	centrocusto = frappe.db.sql("""SELECT name from `tabCost Center` where company = %s and is_group=0 """,(empresa),as_dict=True)
	#print "CENTRO "
	#print centrocusto[0]['name']
	centrocusto = centrocusto[0]['name'] # look for based on the Empresa


	#Has to create the Clients or check if exist first due to the loop ...
	page0=requests.get('http://192.168.229.138:8080/api/people')
	if page0.status_code == 200:
		#clie = page2.json()	
		for clie in page0.json():
			#Found on CBS now look on ours
			cliente = frappe.db.sql("""SELECT name from `tabCustomer` where customer_name like %s """,(str(clie['firstName']) + '%'),as_dict=True)

			print (cliente == [])
			if (cliente == []):
				#Creates the Cliente
			  	response = frappe.get_doc({
					"doctype":"Customer",
					"customer_name": str(clie['firstName']) + ' ' + str(clie['lastName']),
					"customer_type": "Company",
					"customer_group": "Individual",
					"territory": "Angola",
					"customer_details": str(clie),
					"tax)id":str(clie['identificationData']),
					"company": empresa
				})
				response.insert()



	try:
		page=requests.get('http://192.168.229.138:8080/api/savingevents')
	except Exception as e:
		if frappe.message_log: frappe.message_log.pop()
		return 0,0

	#print page
	if page.status_code == 200:
		#Json reading
		num =0
		registo = page.json()
		for reg in page.json()['items']:
			#SAVING EVENTS GetbyID
			page1=requests.get('http://192.168.229.138:8080/api/savings/' + str(reg['contractid']))
			if page1.status_code == 200:
				num1 =0
				registo1 = page1.json()
				#for reg1 in registo1.keys():

				#Gets Client info ... should add on local DB?????
				page2=requests.get('http://192.168.229.138:8080/api/people/' + str(registo1['tiersid']))
				if page2.status_code == 200:
					clie = page2.json()
					#Found on CBS now look on ours
					cliente = frappe.db.sql("""SELECT name from `tabCustomer` where customer_name like %s """,(str(clie['firstName']) + '%'),as_dict=True)

					print (cliente == [])
					if (cliente == []):
						pass
						#Creates the Cliente
#					  	response = frappe.get_doc({
#							"doctype":"Customer",
#							"customer_name": str(clie['firstName']) + ' ' + str(clie['lastName']),
#							"customer_type": "Company",
#							"customer_group": "Individual",
#							"territory": "Angola",
#							"customer_details": str(clie),
#							"company": empresa
#						})
#						response.insert()


				#Lancamento Accounts ERPNEXt
				jv_name = ""

				journal_entry = frappe.new_doc('Journal Entry')
				journal_entry.voucher_type = 'Journal Entry'		#To see what type of entry to add
				journal_entry.user_remark = str(reg['description']) + ' #' + str(registo1['code']) + '-' + str(registo1['id'])
				journal_entry.cheque_no = str(registo1['code'])
				journal_entry.cheque_date = formatdate(reg['creationdate'],"dd-MM-YYYY") 

				journal_entry.company = empresa
				journal_entry.posting_date =nowdate()

				account_amt_list = []
				adjustment_amt = 0
				contasal = 0


				#DEBIT
				#if CODE SVDE (Deposit
				#IF CODE SCTE (Transfer
				acc = '1.10.10.10' #1.10.10.10 default
				if str(reg['code']) == "SCTE":
					acc = '2.10.10' #1.10.10.10 default
				#if str(registo['items'][num]['code']) == "SVDE":

#				if str(reg['code']) == "SCTE":
#					acc = '2.10.10' #2.10.10 default

				accs = frappe.db.sql("""SELECT name from tabAccount where account_name like %s and company = %s """,(acc + '%',empresa),as_dict=True)

				acc = accs[0]['name']

				amt =float(reg['amount'])

				adjustment_amt = adjustment_amt+amt

				account_amt_list.append({
					"account": acc,	
					"debit_in_account_currency": amt,
					"cost_center": centrocusto

				})


				#CREDIT

				acc = '2.10.10' #2.10.10 default
				if str(reg['code']) == "SCTE":
					acc = '2.10.80' #2.10.10 default
				accs = frappe.db.sql("""SELECT name from tabAccount where account_name like %s and company = %s """,(acc + '%',empresa),as_dict=True)
				acc = accs[0]['name']

				amt =float(reg['amount'])

				adjustment_amt = adjustment_amt-amt

				account_amt_list.append({
					"account": acc,
					"credit_in_account_currency": amt,
					"cost_center": centrocusto

				})

				conta = acc;

				journal_entry.set("accounts", account_amt_list)
				journal_entry.save()
				try:
					journal_entry.submit()
					jv_name = journal_entry.name

				except Exception as e:
					frappe.msgprint(e)
			num += 1


