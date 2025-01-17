# -*- coding: utf-8 -*-
# Copyright (c) 2019, Helio de Jesus and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe import throw
from frappe.utils import nowdate, flt, now
from frappe.utils import formatdate, encode
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from datetime import datetime, timedelta
from frappe.utils import cstr, get_datetime, getdate, cint, get_datetime_str

# from angola_erp.util.angola import get_dominios_activos

class ContractosRent(Document):

	def autoname(self):

		self.contracto_numero = make_autoname('RaC/' + '.YYYY./.#####')
		self.name = self.contracto_numero
		self.docstatus = 0



	def validate(self):
		#validar data de nascimento, carta de conducao
		#if not self.data_nascimento_cliente:
		#	frappe.throw(_("Data de Nascimento é necessária!!!"))
			#validated = False
		
		if not self.carta_conducao_cliente:
			frappe.throw(_("Numero da Carta de Condução é necessária!!!"))
			validated = False

		#verifica se a viatura esta em Stand-by
		is_free = frappe.get_doc("Vehicle",self.matricula)
		if not is_free.entrada_ou_saida == "Stand-by":
			frappe.throw(_("Esta viatura já está alugada, não é possivel continuar!!!"))
			validated = False	
		
		#Teste
		#criar_faturavenda(self)	


	def on_submit(self):

		self.docstatus = 1

		
	def on_cancel(self):
		#set the car leased on Vehicle so no one can rent....
		self.docstatus = 2	#cancela o submeter

	def before_cancel(self):
		#only cancel if no Ficha Tecnica submitted

		has_ficha = frappe.model.frappe.get_all('Ficha Tecnica da Viatura',filters={'contracto_numero':['like', self.contracto_numero],'docstatus':1},fields=['matricula_veiculo','contracto_numero'])
		if has_ficha:
			frappe.throw(_('Ficha Tecnica da Viatura existente. Por favor cancelar primeiro'))
			validaded = False
		else:
			print("submeter .... tem que CANCeLAR leased no Vehicle ...")
			frappe.db.set_value("Vehicle",self.matricula, "veiculo_alugado", 0)
			frappe.db.set_value("Vehicle",self.matricula, "entrada_ou_saida", "Stand-by")
			frappe.db.commit()


	def before_submit(self):
		#set the car leased on Vehicle so no one can rent....
		print("submeter .... tem que set leased no Vehicle ...")
		#carro = frappe.get_doc("Vehicle",self.matricula)

		frappe.db.set_value("Vehicle",self.matricula, "veiculo_alugado", 1)
		frappe.db.set_value("Vehicle",self.matricula, "entrada_ou_saida", "Stand-by")
		frappe.db.commit()

		#Criar a Factura para pgar Caucao.
		print('CRIAR FACTURA PARA CAUCAO')
		print('CRIAR FACTURA PARA CAUCAO')
		print('CRIAR FACTURA PARA CAUCAO')
		print('CRIAR FACTURA PARA CAUCAO')
		print('CRIAR FACTURA PARA CAUCAO')
		#criar_faturavenda(self)


	def before_save(self):
	
		#procura a Ficha de SAIDA para por como 

		##### Nunca sera usado ... mas por enquanto fica aqui..
		fichasaida = frappe.model.frappe.get_all('Ficha Tecnica da Viatura',filters={'contracto_numero':self.contracto_numero,'docstatus':1,'entrada_ou_saida_viatura': 'Saida'},fields=['name','contracto_numero'])			

		print('status contract')
		print(self.status_contracto)
		print('status contract')

		
		print(fichasaida)

		if fichasaida:
			if self.status_contracto == "Terminou":
				frappe.db.set_value('Ficha Tecnica da Viatura',fichasaida[0].name)
				frappe.db.commit()



def criar_faturavenda(doc):

	
	#if NONE should ask to select or select the first one....
	#or maybe on the form should have the company to select....
	empresa = frappe.get_value("Global Defaults",None,"default_company")	

	if not empresa:		#Only for Testing ....
		empresa = '2MS - Comercio e Representacoes, Lda'

	empresa_abbr = frappe.get_value("Company",empresa,"abbr")

	centrocusto = frappe.get_value("Company",empresa,"cost_center")

	contalucro =  frappe.get_value("Company",empresa,"default_income_account")
	contadespesas =   frappe.get_value("Company",empresa,"default_expense_account")

	armazemdefault = frappe.get_value('Stock Settings',None,'default_warehouse')

	accs = frappe.db.sql("""SELECT name from tabAccount where account_name like '31121000%%' and company = %s """,(empresa),as_dict=True)
	acc = accs[0]['name']

	datalimite = frappe.utils.nowdate()	#Today Date

	#criarprojeto = False
	#if frappe.db.sql("""select name from `tabSales Invoice` WHERE propina =%s """,(doc.name), as_dict=False) ==():

	criarprojeto = True

	if criarprojeto == True:
		#print doc.components[0].fees_category.encode('utf-8')
		#print type(doc.components[0].amount)

		#get from Item ....
		
		valor = flt(200000)

		#print type(valor) #doc.round_floats_in(valor)

		# tem_Educa = get_dominios_activos()
		tem_educacao = False
		# for x in tem_Educa:
		# 	print(x.domain)
		# 	if x.domain == 'Education':
		# 		tem_educacao = True


		sales_invoice = frappe.new_doc("Sales Invoice")
		sales_invoice.customer = doc.nome_do_cliente
		sales_invoice.propina = doc.name
		sales_invoice.due_date = datalimite
		sales_invoice.company = empresa
		sales_invoice.is_pos = '0'
		sales_invoice.debit_to = acc
		sales_invoice.status = 'Draft'

		item_line = sales_invoice.append("items")
		item_line.item_code = "Pagamento Caucao"
		item_line.item_name = "Pagamento Caucao"
		item_line.description = "Pagamento Caucao "
		item_line.qty = 1
		item_line.uom = "Unidade"
		item_line.conversion_factor = 1
		item_line.income_account = contalucro.encode('utf-8')
		item_line.rate = valor
		item_line.amount = valor
		item_line.warehouse = armazemdefault
		item_line.expense_account = contadespesas
		item_line.cost_center = centrocusto
		#sales_invoice.set_missing_values()
		#return sales_invoice
		sales_invoice.save(ignore_permissions=True)



def criar_adiantamento_caucao(doc, self=None):
	
	#if NONE should ask to select or select the first one....
	#or maybe on the form should have the company to select....
	empresa = frappe.get_value("Global Defaults",None,"default_company")	

	if not empresa:		#Only for Testing ....
		empresa = '2MS - Comercio e Representacoes, Lda'

	empresa_abbr = frappe.get_value("Company",empresa,"abbr")

	centrocusto = frappe.get_value("Company",empresa,"cost_center")

	contalucro =  frappe.get_value("Company",empresa,"default_income_account")
	contadespesas =   frappe.get_value("Company",empresa,"default_expense_account")

	armazemdefault = frappe.get_value('Stock Settings',None,'default_warehouse')

	accs = frappe.db.sql("""SELECT name from tabAccount where account_name like '31121000%%' and company = %s """,(empresa),as_dict=True)
	acc = accs[0]['name']

	datalimite = frappe.utils.nowdate()	#Today Date

	#criarprojeto = False
	#if frappe.db.sql("""select name from `tabSales Invoice` WHERE propina =%s """,(doc.name), as_dict=False) ==():

	criarprojeto = True


	journal_entry = frappe.new_doc("Journal Entry")
	journal_entry.voucher_type = "Journal Entry"
	journal_entry.posting_date = frappe.datetime.now()
	journal_entry.company = empresa
	journal_entry.check_no = self.contracto_numero

	item_line = journal_entry.append("accounts")
	item_line.account = acc
	item_line.party_type = "Customer"
	item_line.party = self.nome_do_cliente
	item_line.cost_center = centrocusto
	item_line.credit_in_account_currency = 200000
	item_line.is_advance = "Yes"
	journal_entry.save(ignore_permissions=True)

