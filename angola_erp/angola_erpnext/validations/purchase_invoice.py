# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from frappe import msgprint

import angola_erp
from angola_erp.util.cambios import cambios
from angola_erp.util.angola import get_lista_retencoes
from angola_erp.util.angola import get_compras_taxa_retencao
from angola_erp.util.angola import get_taxa_ipc
from angola_erp.util.angola import get_taxa_iva

import erpnext

from frappe.utils import money_in_words, flt, encode
from frappe.utils import cstr, getdate, date_diff
## from erpnext.setup.utils import get_company_currency
from num2words import num2words


def validate(doc,method):

	taxavenda= cambios("BNA")
	lista_retencoes = get_lista_retencoes()
	lista_retencao = get_compras_taxa_retencao()
	lista_impostos = get_taxa_ipc()

	lista_iva = get_taxa_iva()

	temretencao = False 
	temimpostoconsumo = False 
	retencaofonte =0
	retencaopercentagem =0
	totalpararetencao = 0
	totalgeralimpostoconsumo = 0
	totalgeralretencaofonte = 0
	totalbaseretencaofonte = 0
	retencaofonteDESC = ""
	totalservicos_retencaofonte =0
	totaldespesas_noretencaofonte =0

	percentagem = 0
	msg_item = []
	if (taxavenda[1] !=0 and doc.taxa_cambio == 0):
		doc.taxa_cambio = taxavenda[1]
				

	ii=0

	for x in lista_retencoes:
		if x.descricao =='Retencao na Fonte':
			#print ('pertagem ', x.percentagem)
			retencaopercentagem = x.percentagem
		elif (x.descricao =='IPC') or (x.descricao =='Imposto de Consumo'):
			print ('IPC % ', x.percentagem)
			percentagem = x.percentagem

		elif (x.descricao.upper() =='IVA'.upper()) or ("Imposto Valor Acrescentado".upper() == x.descricao.upper() or 'Acrescentado'.upper() in x.descricao.upper()):
			print ('IVA % ', x.percentagem)
			percentagem = x.percentagem



	for i in doc.get("items"):
		if i.item_code != None:			
			print (i.item_code).encode('utf-8')
			prod = frappe.db.sql("""SELECT item_code,imposto_de_consumo,retencao_na_fonte,que_retencao, has_batch_no FROM `tabItem` WHERE item_code = %s """, i.item_code , as_dict=True)
			if prod[0].imposto_de_consumo ==1:
				print ("IMPOSTO CONSUMO")
				if percentagem == 0:
					i.imposto_de_consumo = (i.amount * 5) / 100
				else:
					i.imposto_de_consumo = (i.amount * percentagem) / 100
				
			if prod[0].retencao_na_fonte ==1:
				print ("RETENCAO FONTE")
				print (prod[0].item_code).encode('utf-8')
				for x in lista_retencoes:
					if x.descricao == prod[0].que_retencao:
						print ('pertagem ', x.percentagem)
						retencaopercentagem = x.percentagem


				i.retencao_na_fonte = (i.amount * retencaopercentagem) / 100
				totalbaseretencaofonte += i.amount
				totalservicos_retencaofonte += totalbaseretencaofonte
			else:
				totaldespesas_noretencaofonte += i.amount		

			totalgeralimpostoconsumo += i.imposto_de_consumo					
			totalgeralretencaofonte +=  i.retencao_na_fonte

			#Verifica se tem Batch ...
			#print (prod[0].has_batch_no)
			if prod[0].has_batch_no == 1:
				itembatch = frappe.db.sql("""SELECT batch_id, count(batch_id) as contar FROM `tabBatch` WHERE item = %s """, i.item_code , as_dict=True)		
				#print (itembatch)
				#print (itembatch[0].batch_id)
				#print (itembatch[0].contar)
				if itembatch[0].contar == 1 and i.batch_no == None:
					#default Batch added
					i.batch_no = itembatch[0].batch_id
				elif itembatch[0].contar > 1 and i.batch_no == None:
					#Mais que um batch
					msg_item.append(i.item_code)

	if msg_item != []:
		frappe.throw(("Items {0} tem mais quem um Lote. Por favor selecionar").format(msg_item))


	#Save retencao na INVoice 
	doc.total_retencao_na_fonte = totalgeralretencaofonte
	doc.base_retencao_fonte = totalbaseretencaofonte

	#Calcula_despesas Ticked
	iii=0
	print ("Despesas")
	for ai in doc.get("taxes"):
		if ai.parent == doc.name and ai.charge_type !="":
			if ai.calcula_despesas:
				if totaldespesas_noretencaofonte ==0:
					#recalcula
					print ("RECALCULA")
					if (ai.rate == 0) and (percentagem == 0) :
						percentagem = 5
					else:
						percentagem = ai.rate

					for aii in doc.get("items"):
						if aii.parent == doc.name:
							prod = frappe.db.sql("""SELECT item_code,imposto_de_consumo,retencao_na_fonte FROM `tabItem` WHERE item_code = %s """, aii.item_code , as_dict=True)					

							#if (iii==0){iii=0}
							
							if prod[0].imposto_de_consumo == 1:

								if aii.imposto_de_consumo == 0:
									pass
								
								if aii.retencao_na_fonte == 1:
										
									totalgeralretencaofonte +=  (aii.amount * retencaopercentagem) / 100
									totalbaseretencaofonte += aii.amount
									totalservicos_retencaofonte += totalbaseretencaofonte

								totalgeralimpostoconsumo += aii.imposto_de_consumo					


								despesas = (percentagem * totaldespesas_noretencaofonte)/100
								ai.charge_type="Actual"
								ai.tax_amount=despesas
							else:
								ai.tax_amount = 0




				else:
					print ("CALCULA DESPESAS")
					if (ai.rate == 0) and (percentagem == 0) :
						percentagem = 5
					else:
						percentagem = ai.rate

					despesas = (ai.rate * totaldespesas_noretencaofonte)/100

					if despesas != totalgeralimpostoconsumo:

						ai.charge_type = "Actual"
						ai.tax_amount = totalgeralimpostoconsumo

					else:
						ai.charge_type = "Actual"
						ai.tax_amount = despesas
			elif "34220000" in ai.account_head: #IVA
				pass

			else:
				ai.charge_type = "Actual"
				ai.tax_amount = totalgeralimpostoconsumo

	company_currency = erpnext.get_company_currency(doc.company)
	if (company_currency =='KZ'):
		doc.in_words = num2words(doc.grand_total, lang='pt_BR').title()	+ ' Kwanzas.'
	else:
		doc.in_words = money_in_words(doc.grand_total, company_currency)



