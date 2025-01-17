# -*- coding: utf-8 -*-
# Copyright (c) 2015, Helio de Jesus and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime, timedelta
from frappe.utils import cstr, get_datetime, getdate, cint, get_datetime_str, flt
from frappe.model.document import Document
from frappe.model.naming import make_autoname

import erpnext
from erpnext.controllers.stock_controller import update_gl_entries_after
from erpnext.controllers.selling_controller import SellingController
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.stock.get_item_details import get_pos_profile
from erpnext.accounts.utils import get_fiscal_year
from erpnext.controllers.accounts_controller import AccountsController #get_gl_dict
from erpnext.accounts.utils import get_account_currency
from erpnext.controllers.stock_controller import StockController #get_items_and_warehouses

#from erpnext.controllers.selling_controller import update_stock_ledger
#import erpnext.controllers.selling_controller
from idna import unicode

form_grid_templates = {
	"items": "templates/form_grid/gestao_quartos_list.html"
}

#class GestaodeQuartos(AccountsController):

class GestaodeQuartos(StockController):
	def __init__(self, arg1, arg2=None):
		super(GestaodeQuartos, self).__init__(arg1, arg2)

#class GestaodeQuartos(Document):

	def autoname(self):
		self.name = make_autoname(self.numero_quarto + '-' + '.#####')
		self.update_stock = 1
#		self.posting_time = frappe.utils.nowtime()

	def validate(self):

		super(GestaodeQuartos, self).validate()
		self.Validar_Numero_Dias()
		self.Check_ContaCorrente()
		self.Sethoras_Quarto()
		self.Contas_Correntes()

		self.validate_debit_to_acc()
		self.validate_stocks()
		self.set_against_income_account()


	def Validar_Numero_Dias(self):
		if self.horas <= 0:
			validated=False
			frappe.throw(_("Horas/Dias tem que ser 1 ou mais."))

		elif self.hora_entrada == self.hora_saida:
			validated=False
			frappe.throw(_("Hora de Saida tem que sair diferente que Hora de Entrada."))


	def on_update(self):
#		self.posting_time = frappe.utils.nowtime()

		#self.valor_pago = self.total_servicos
		print ("Doc Status ", self.docstatus)
		if self.status_quarto == "Fechado":
			print ("DEVE SER SUBMETIDO")
	
					
			self.on_submit()


		self.Quartos_Status()
		self.Reservas_Status()

	def before_save(self):

#		frappe.throw ("Doc Status ", self.docstatus == 0)
		if (self.total_servicos == 0) or (self.total_servicos != 0):
			#Adiciona o pagamento na Sales Invoice Payment
#			self.docstatus =0
			self.pagamentos_feitos()
#			frappe.throw ("Pagamentos pode ser AQUI")
#		set_account_for_mode_of_payment(self)

		if self.status_quarto == "Fechado":
			self.pagamentos_feitos1()
#		elif self.total_servicos != 0:
#			self.pagamentos_feitos1()


	def on_submit(self):
		#Deve submer para fazer pagamento ??????

		if self.servico_pago_por:
			for d in self.get('servicos'):
				if d.servico_produto:
					#Pagamentos
#					set_account_for_mode_of_payment(self)

	
					#deveria ser ao SUBMIT / Payment
					self.update_stock_ledger()
					print("TERMINA STOCK LEDGER")
					
					# this sequence because outstanding may get -ve
					self.make_gl_entries()
		self.docstatus=1
		self.save()

	def pagamentos_feitos(self):

		if self.pagamento_por =='Cash':
			pagopor ="Cash"

		elif self.pagamento_por =='TPA':
			pagopor ="Bank"

		x = 1
		for x in range(1,2):
			
			pagamento_feito = frappe.get_doc({
				"doctype": "Sales Invoice Payment",
				"parent": self.name,
				"parentfield": "pagamento",
				"parenttype": "Gestao de Quartos",
				"amount": self.total if (x == 1) else 0,
				"base_amount": self.total if (x == 1) else 0,
				"account": frappe.db.get_value("Mode of Payment Account", {"parent": "Cash" if (pagopor=="Cash") else "TPA", "company": self.company}, "default_account"),
				#self.return_against if cint(self.is_return) else self.name)
				"type": frappe.db.get_value("Mode of Payment", {"type": pagopor}, "type"),
				"mode_of_payment": frappe.db.get_value("Mode of Payment", {"type": pagopor}, "mode_of_payment"),
#				"name": self.name,
				"idx": +x
			})
			pagamento_feito.insert()
			print (x)
			print("Parece que CRIOU O PAYMENT DOC")

	def pagamentos_feitos1(self):

		#adds only the second payment for the Services added
		if self.total_servicos:
			#if self.servico_pago_por =='1-Cash':
			if self.pagamento_por =='Cash':
				pagopor ="Cash"
			#elif self.servico_pago_por =='2-TPA':
			elif self.pagamento_por =='TPA':
				pagopor ="Bank"

			pagamento_feito = frappe.get_doc({
				"doctype": "Sales Invoice Payment",
				"parent": self.name,
				"parentfield": "pagamento",
				"parenttype": "Gestao de Quartos",
				"amount": 0,
				"base_amount": 0,
				"account": frappe.db.get_value("Mode of Payment Account", {"parent": "Cash" if (pagopor=="Cash") else "TPA", "company": self.company}, "default_account"),
				#self.return_against if cint(self.is_return) else self.name)
				"type": frappe.db.get_value("Mode of Payment", {"type": pagopor}, "type"),
				"mode_of_payment": frappe.db.get_value("Mode of Payment", {"type": pagopor}, "mode_of_payment"),
				"idx": 2
			})
			print(pagamento_feito.idx)
			print(pagamento_feito.parent)
			print(pagamento_feito.amount)

			pagamento_feito.amount = self.total_servicos

			pagamento_feito.base_amount = self.total_servicos
			pagamento_feito.account = frappe.db.get_value("Mode of Payment Account", {"parent": "Cash" if (pagopor=="Cash") else "TPA", "company": self.company}, "default_account")

				#"account": frappe.db.get_value("Mode of Payment Account", {"parent": pagopor, "company": self.company}, "default_account"),
			pagamento_feito.type = frappe.db.get_value("Mode of Payment", {"type": pagopor}, "type")
			pagamento_feito.mode_of_payment = frappe.db.get_value("Mode of Payment", {"type": pagopor}, "mode_of_payment")
#				"name": frappe.utils.now(),

#			})
#			print(pagamento_feito)
			pagamento_feito.save()

			print(pagamento_feito.amount)
			print("CRIOU O SEGUNDO PAYMENT DOC")
			print("CRIOU O SEGUNDO PAYMENT DOC")
			print("CRIOU O SEGUNDO PAYMENT DOC")
			print("CRIOU O SEGUNDO PAYMENT DOC")
			print("CRIOU O SEGUNDO PAYMENT DOC")
			print("CRIOU O SEGUNDO PAYMENT DOC")
			print("CRIOU O SEGUNDO PAYMENT DOC")
			print("CRIOU O SEGUNDO PAYMENT DOC")
			print("CRIOU O SEGUNDO PAYMENT DOC")
			print("CRIOU O SEGUNDO PAYMENT DOC")

	def pagamentos_feitos2(self):

		if self.pagamento_por =='Cash':
			pagopor ="Cash"
		#elif self.servico_pago_por =='2-TPA':
		elif self.pagamento_por =='TPA':
			pagopor ="Bank"
		#TO DELETE
#		pagamento_feito = frappe.new_doc("Sales Invoice Payment")
		pagamento_feito = self.append('pagamento',{})
		
#		pagamento_feito.docstatus = 0
		pagamento_feito.parent = self.name
		pagamento_feito.parentfield = "pagamento"
		pagamento_feito.parenttype = "Gestao de Quartos"
		pagamento_feito.amount = self.total_servicos
		pagamento_feito.base_amount = self.total_servicos
		pagamento_feito.account = frappe.db.get_value("Mode of Payment Account", {"parent": "Cash" if (pagopor=="Cash") else "TPA", "company": self.company}, "default_account"),

				#"account": frappe.db.get_value("Mode of Payment Account", {"parent": pagopor, "company": self.company}, "default_account"),
		pagamento_feito.type = frappe.db.get_value("Mode of Payment", {"type": pagopor}, "type"),
		pagamento_feito.mode_of_payment = frappe.db.get_value("Mode of Payment", {"type": pagopor}, "mode_of_payment")


		#NEEDS TO GET THE PAYMENTS AVAILABE ON THE SYSTEM 
		print ("PAGAMENTOS")
		print ("PAGAMENTOS")
		print ("PAGAMENTOS")
		print ("PAGAMENTOS")
		print ("PAGAMENTOS")
		print ("PAGAMENTOS")
		print ("PAGAMENTOS")

		pagamento_feito.idx = 2
				
#		pagamento_feito.insert()
		pagamento_feito.save()


	def Quartos_Status(self):

		# Change Quarto status 
		quarto = frappe.get_doc("Quartos", self.numero_quarto)
		
		if self.status_quarto == "Ocupado":
			quarto.status_quarto = "Ocupado"
		elif self.status_quarto == "Ativo":
			quarto.status_quarto = "Ocupado"
		elif self.status_quarto == "Livre":
			quarto.status_quarto = "Livre"
		elif self.status_quarto == "Fechado":
			quarto.status_quarto = "Livre"

		quarto.save()		

	def Reservas_Status(self):
		#Change Reservas status
		if (self.status_quarto == "Fechado") and  (self.reserva_numero != None) :
			reserva = frappe.get_doc("Reservas",self.reserva_numero)
			reserva.reservation_status = "Fechada"
			reserva.save()
			
			

	def Check_ContaCorrente(self):

		if (self.servico_pago_por=="Conta-Corrente"):
			self.nome_cliente = self.conta_corrente
			if (self.conta_corrente == "") or (self.conta_corrente == "nome do cliente"):
				validated= False
				frappe.throw(_("Nao foi selecionado o Cliente para Conta-Corrente."))

#			validated= False
#			frappe.throw(_("Modulo nao funcional de momento."))

		if (self.pagamento_por=="Conta-Corrente"):
			if (self.conta_corrente == "") or (self.conta_corrente == "nome do cliente"):
				validated= False
				frappe.throw(_("Nao foi selecionado o Cliente para Conta-Corrente."))


	def Sethoras_Quarto(self):
		
		if self.hora_diaria_noite == "Noite":			
			self.hora_saida= get_datetime(self.hora_entrada) + timedelta(hours=12)			
		elif self.hora_diaria_noite == "Diaria":
			self.hora_saida= get_datetime(self.hora_entrada) + timedelta(days=self.horas)
		elif self.hora_diaria_noite == "Hora":
			self.hora_saida = get_datetime(self.hora_entrada) + timedelta(hours=self.horas)


	def Contas_Correntes(self):
				#aproveita criar ja o registo no Conta-correntes
		if (self.conta_corrente !="nome do cliente") and (self.conta_corrente !=None) and (self.status_quarto == "Fechado") and (self.conta_corrente_status == "Não Pago") :
			if (frappe.db.sql("""select cc_nome_cliente from `tabContas Correntes` WHERE cc_nome_cliente =%s """,self.conta_corrente, as_dict=False)) != ():
				#existe faz os calculos da divida
				ccorrente = frappe.get_doc("Contas Correntes", self.conta_corrente)

				totalextra = 0

				cc_detalhes = frappe.new_doc("CC_detalhes")
				cc_detalhes.parent = ccorrente.name
				cc_detalhes.parentfield = "cc_table_detalhes"
				cc_detalhes.parenttype = "Contas Correntes"
					
				cc_detalhes.descricao_servico = self.name #extras.nome_servico
				cc_detalhes.name = self.name
				cc_detalhes.numero_registo = self.name
				cc_detalhes.total = self.total #extras.total_extra
				cc_detalhes.total_servicos = self.total_servicos #extras.total_extra
				cc_detalhes.data_registo = self.hora_entrada
				totalextra = totalextra + self.total_servicos  + self.total #extras.total_extra

				cc_detalhes.status_conta_corrente = "Não Pago"
				cc_detalhes.tipo = "Quarto"
				cc_detalhes.idx += 1	
					
				cc_detalhes.insert()

				print (ccorrente.cc_valor_divida + totalextra)
				ccorrente.cc_valor_divida = flt(ccorrente.cc_valor_divida) + totalextra
				#ccorrente.save()

			else:
				ccorrente = frappe.new_doc("Contas Correntes")
				ccorrente.cc_nome_cliente = self.conta_corrente
				ccorrente.name = self.conta_corrente
				ccorrente.cc_status_conta_corrente = "Não Pago"
				ccorrente.insert()
				totalextra = 0

				cc_detalhes = frappe.new_doc("CC_detalhes")
				cc_detalhes.parent =ccorrente.name
				cc_detalhes.parentfield = "cc_table_detalhes"
				cc_detalhes.parenttype = "Contas Correntes"

					#print extras.nome_servico
				cc_detalhes.descricao_servico = self.name #extras.nome_servico
				cc_detalhes.name = self.name
				cc_detalhes.numero_registo = self.name
				cc_detalhes.total = self.total #extras.total_extra
				cc_detalhes.total_servicos = self.total_servicos #extras.total_extra
				cc_detalhes.data_registo = self.hora_entrada
				totalextra = totalextra + self.total_servicos  + self.total #extras.total_extra

				cc_detalhes.status_conta_corrente = "Não Pago"
				cc_detalhes.tipo = "Quarto"
				cc_detalhes.insert()

				ccorrente.cc_valor_divida = flt(ccorrente.cc_valor_divida) + totalextra

	def validate_debit_to_acc(self):
		account = frappe.db.get_value("Account", self.debit_to,
			["account_type", "report_type", "account_currency"], as_dict=True)

		if not account:
			frappe.throw(_("Debit To is required"))

		if account.report_type != "Balance Sheet":
			frappe.throw(_("Debit To account must be a Balance Sheet account"))

		if self.nome_cliente and account.account_type != "Receivable":
			frappe.throw(_("Debit To account must be a Receivable account"))

		self.party_account_currency = account.account_currency

	def validate_stocks(self):
#		if cint(self.update_stock):
		print ("Validar os Stocks")
#		self.validate_dropship_item()
#		self.validate_item_code()
		self.validate_warehouse()
		self.actualiza_stock_corrente()
#		self.validate_delivery_note()



	def set_against_income_account(self):
		"""Set against account for debit to account"""
		against_acc = []
		for d in self.get('servicos'):
			if d.income_account not in against_acc:
				against_acc.append(d.income_account)
		#return against_acc
		self.against_income_account = ','.join(against_acc)

	def actualiza_stock_corrente(self):
			print ("Atualizar Stocks")
			for d in self.get('servicos'):
				if d.servico_produto:
					bin = frappe.db.sql("select actual_qty from `tabBin` where item_code = %s and warehouse = %s", (d.servico_produto,d.warehouse), as_dict = 1)
					d.actual_qty = bin and flt(bin[0]['actual_qty']) or 0

	def validate_warehouse(self):
		pos_profile = get_pos_profile(self.company) or {}
		print ("POS Perfil ",pos_profile)

		if not pos_profile:
			frappe.throw(_("Este usuario nao tem perfil para vendas\n Deve configurar no POS (Ponto de Venda)."))
			validated = False
		
		for d in self.get('servicos'):
			print (unicode(d.servico_produto).encode('utf-8'))
			artigo = frappe.get_doc("Item", d.servico_produto)
			d.warehouse = pos_profile['warehouse'] or artigo.default_warehouse
			d.income_account = pos_profile['income_account'] or artigo.income_account
			d.cost_center = pos_profile['cost_center'] or artigo.selling_cost_center
#			d.save()
	

	def update_stock_ledger(self):
#		self.update_reserved_qty()

		sl_entries = []
		for d in self.get('servicos'): # self.get_item_list():
			print("upd stock ledger ",d.servico_produto)
			if frappe.db.get_value("Item", d.servico_produto, "is_stock_item") == 1 and flt(d.quantidade):
				return_rate = 0
#				if cint(self.is_return) and self.return_against and self.docstatus==1:
#					return_rate = self.get_incoming_rate_for_sales_return(d.item_code, self.return_against)
				print ("servicos nome ",d.name)
				print (unicode(d.servico_produto).encode('utf-8'))
				print ("doctstatus ", self.docstatus)
				if d.warehouse and self.docstatus==0:
						sl_entries.append(self.get_sl_entries(d, {
							"actual_qty": -1*flt(d.quantidade),
							"incoming_rate": return_rate
						}))

		print ("Upd stock SL ENTRIES")
		print (sl_entries)
		self.make_sl_entries(sl_entries)

	def get_items_and_warehouses(self):
		items, warehouses = [], []

		if hasattr(self, "servicos"):
			item_doclist = self.get("servicos")
		elif self.doctype == "Stock Reconciliation":
			import json
			item_doclist = []
			data = json.loads(self.reconciliation_json)
			for row in data[data.index(self.head_row)+1:]:
				d = frappe._dict(zip(["item_code", "warehouse", "qty", "valuation_rate"], row))
				item_doclist.append(d)

		if item_doclist:
			for d in item_doclist:
				if d.servico_produto and d.servico_produto not in items:
					items.append(d.servico_produto)

				if d.get("warehouse") and d.warehouse not in warehouses:
					warehouses.append(d.warehouse)

				if self.doctype == "Stock Entry":
					if d.get("s_warehouse") and d.s_warehouse not in warehouses:
						warehouses.append(d.s_warehouse)
					if d.get("t_warehouse") and d.t_warehouse not in warehouses:
						warehouses.append(d.t_warehouse)

		return items, warehouses


	def get_sl_entries(self, d, args):
		print ("produto ",d.get("servico_produto", None))
		print ("armazem ",d.get("warehouse", None))
		print ("hora ", self.hora_entrada)
		print ("fiscal ", get_fiscal_year(self.posting_date, company=self.company)[0])



		sl_dict = frappe._dict({
			"item_code": d.get("servico_produto", None),
			"warehouse": d.get("warehouse", None),
			"posting_date": self.posting_date,
			"posting_time": self.posting_time,
			'fiscal_year': get_fiscal_year(self.posting_date, company=self.company)[0],
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"voucher_detail_no": d.name,
			"actual_qty": (self.docstatus==1 and 1 or -1)*flt(d.get("stock_qty")),
			"stock_uom": frappe.db.get_value("Item", args.get("item_code") or d.get("servico_produto"), "stock_uom"),
			"incoming_rate": 0,
			"company": self.company,
#			"batch_no": cstr(d.get("batch_no")).strip(),
#			"serial_no": d.get("serial_no"),
#			"project": d.get("project"),
			"is_cancelled": self.docstatus==2 and "Yes" or "No"
		})

		sl_dict.update(args)
		print ("SL Dict")
		print (sl_dict)

		return sl_dict

	def make_sl_entries(self, sl_entries, is_amended=None, allow_negative_stock=False, via_landed_cost_voucher=False):
		#from erpnext.stock.stock_ledger import make_sl_entries
		print("SL ENTRIES 1")
		print(sl_entries)
		self.make_slentries(sl_entries, is_amended, allow_negative_stock, via_landed_cost_voucher)




	def make_slentries(self,sl_entries, is_amended=None, allow_negative_stock=False, via_landed_cost_voucher=False):
		if sl_entries:
			from erpnext.stock.utils import update_bin

			cancel = True if sl_entries[0].get("is_cancelled") == "Yes" else False
			if cancel:
				pass
				# set_as_cancel(sl_entries[0].get('voucher_no'), sl_entries[0].get('voucher_type'))

			for sle in sl_entries:
				sle_id = None
				if sle.get('is_cancelled') == 'Yes':
					sle['actual_qty'] = -flt(sle['actual_qty'])
				print("actual_qtd ",sle.actual_qty)
				if sle.get("actual_qty") or sle.get("voucher_type")=="Stock Reconciliation":
					print ("FAZ Entry")
					print (sle)
					print (via_landed_cost_voucher)
					sle_id = self.make_entry(sle, allow_negative_stock, via_landed_cost_voucher)

				args = sle.copy()
				args.update({
					"sle_id": sle_id,
					"is_amended": is_amended
				})
				update_bin(args, allow_negative_stock, via_landed_cost_voucher)

			if cancel:
				pass
				# delete_cancelled_entry(sl_entries[0].get('voucher_type'), sl_entries[0].get('voucher_no'))

	def make_entry(self,args, allow_negative_stock=False, via_landed_cost_voucher=False):
		print ("inicio make Entry")
		args.update({"doctype": "Stock Ledger Entry"})
		sle = frappe.get_doc(args)
		sle.flags.ignore_permissions = 1
		sle.allow_negative_stock=allow_negative_stock
		sle.via_landed_cost_voucher = via_landed_cost_voucher
		sle.insert()
		sle.submit()
		print ("make Entry OK")
		return sle.name

	def make_gl_entries(self, repost_future_gle=True):
		if not self.total_servicos:
			return
		gl_entries = self.get_gl_entries()

		if gl_entries:
			from erpnext.accounts.general_ledger import make_gl_entries

			# if POS and amount is written off, updating outstanding amt after posting all gl entries
			update_outstanding = "No"  #if (cint(self.is_pos) or self.write_off_account) else "Yes"
			print("UPDATE GL ENTRIES")
			make_gl_entries(gl_entries, cancel=(self.docstatus == 2),
				update_outstanding=update_outstanding, merge_entries=False)

#			if update_outstanding == "No":
#				from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
#				update_outstanding_amt(self.debit_to, "Customer", self.customer,
#					self.doctype, self.return_against if cint(self.is_return) else self.name)

			if repost_future_gle and cint(self.update_stock) \
				and cint(frappe.defaults.get_global_default("auto_accounting_for_stock")):
					items, warehouses = self.get_items_and_warehouses()
					print("GL ENTRY")
					print("items  ",items)
					print("warehouse ", warehouses)

					update_gl_entries_after(self.posting_date, self.posting_time, warehouses, items)

		elif self.docstatus == 2 and cint(self.update_stock) \
			and cint(frappe.defaults.get_global_default("auto_accounting_for_stock")):
				from erpnext.accounts.general_ledger import delete_gl_entries
				delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

	def get_gl_entries(self, warehouse_account=None):
		from erpnext.accounts.general_ledger import merge_similar_entries

		gl_entries = []
		print ("custom GL Entries ")
		self.make_customer_gl_entry(gl_entries)
		print ("custom GL Entries ",gl_entries)

		print ("TAX GL Entries ")		
		self.make_tax_gl_entries(gl_entries)
		print ("TAX GL Entries ",gl_entries)

		print ("ITEM GL Entries ")
		self.make_item_gl_entries(gl_entries)
		print ("ITEM GL Entries ",gl_entries)

		# merge gl entries before adding pos entries
		gl_entries = merge_similar_entries(gl_entries)
		print ("MERGED GL Entries ",gl_entries)

		print ("POS GL Entries ")
		self.make_pos_gl_entries(gl_entries)
		print ("POS GL Entries ",gl_entries)

#pensa		self.make_gle_for_change_amount(gl_entries)

#pensa		self.make_write_off_gl_entry(gl_entries)

		return gl_entries

	def make_customer_gl_entry(self, gl_entries):
#		if self.grand_total:
		if self.total_servicos:
			# Didnot use base_grand_total to book rounding loss gle
			grand_total_in_company_currency = flt(self.total_servicos,
				self.precision("total_servicos"))

			gl_entries.append(
				self.get_gl_dict({
					"account": self.debit_to,
					"party_type": "Customer",
					"party": self.nome_cliente,
					"against": self.against_income_account,
					"debit": grand_total_in_company_currency,
					"debit_in_account_currency": grand_total_in_company_currency \
						if self.party_account_currency==self.company_currency else self.total_servicos,
					"against_voucher": self.name, #self.return_against if cint(self.is_return) else self.name,
					"against_voucher_type": self.doctype
				}, self.party_account_currency)
			)

	def make_tax_gl_entries(self, gl_entries):
		for tax in self.get("taxes"):
			if flt(tax.base_tax_amount_after_discount_amount):
				account_currency = get_account_currency(tax.account_head)
				gl_entries.append(
					self.get_gl_dict({
						"account": tax.account_head,
						"against": self.nome_cliente,
						"credit": flt(tax.base_tax_amount_after_discount_amount),
						"credit_in_account_currency": flt(tax.base_tax_amount_after_discount_amount) \
							if account_currency==self.company_currency else flt(tax.tax_amount_after_discount_amount),
						"cost_center": tax.cost_center
					}, account_currency)
				)

	def make_item_gl_entries(self, gl_entries):
		# income account gl entries
		for item in self.get("servicos"):
			if flt(item.total_servico_produto):

				account_currency = get_account_currency(item.income_account)
				gl_entries.append(
					self.get_gl_dict({
						"account": item.income_account,
						"against": self.nome_cliente,
						"credit": item.total_servico_produto,
						"credit_in_account_currency": item.total_servico_produto \
							if account_currency==self.company_currency else item.total_servico_produto,
						"cost_center": item.cost_center
					}, account_currency)
				)

		# expense account gl entries
		if cint(frappe.defaults.get_global_default("auto_accounting_for_stock")) \
				and cint(self.update_stock):
			print ("algo por saber")
			#To check how this words ....
			# gl_entries += super(GestaodeQuartos, self).get_gl_entries()

	def make_pos_gl_entries(self, gl_entries):
		#if cint(self.is_pos):
			for payment_mode in self.pagamento:
				if payment_mode.amount:
					# POS, make payment entries
					gl_entries.append(
						self.get_gl_dict({
							"account": self.debit_to,
							"party_type": "Customer",
							"party": self.nome_cliente,
							"against": payment_mode.account,
							"credit": payment_mode.base_amount,
							"credit_in_account_currency": payment_mode.base_amount \
								if self.party_account_currency==self.company_currency \
								else payment_mode.amount,
							"against_voucher": self.name, #self.return_against if cint(self.is_return) else self.name,
							"against_voucher_type": self.doctype,
						}, self.party_account_currency)
					)

					payment_mode_account_currency = get_account_currency(payment_mode.account)
					gl_entries.append(
						self.get_gl_dict({
							"account": payment_mode.account,
							"against": self.nome_cliente,
							"debit": payment_mode.base_amount,
							"debit_in_account_currency": payment_mode.base_amount \
								if payment_mode_account_currency==self.company_currency \
								else payment_mode.amount
						}, payment_mode_account_currency)
					)
				
	def make_gle_for_change_amount(self, gl_entries):
		if cint(self.is_pos) and self.change_amount:
			if self.account_for_change_amount:
				gl_entries.append(
					self.get_gl_dict({
						"account": self.debit_to,
						"party_type": "Customer",
						"party": self.customer,
						"against": self.account_for_change_amount,
						"debit": flt(self.base_change_amount),
						"debit_in_account_currency": flt(self.base_change_amount) \
							if self.party_account_currency==self.company_currency else flt(self.change_amount),
						"against_voucher": self.return_against if cint(self.is_return) else self.name,
						"against_voucher_type": self.doctype
					}, self.party_account_currency)
				)
				
				gl_entries.append(
					self.get_gl_dict({
						"account": self.account_for_change_amount,
						"against": self.customer,
						"credit": self.base_change_amount
					})
				)
			else:
				frappe.throw(_("Select change amount account"), title="Mandatory Field")
		
	def make_write_off_gl_entry(self, gl_entries):
		# write off entries, applicable if only pos
		if self.write_off_account and self.write_off_amount:
			write_off_account_currency = get_account_currency(self.write_off_account)
			default_cost_center = frappe.db.get_value('Company', self.company, 'cost_center')

			gl_entries.append(
				self.get_gl_dict({
					"account": self.debit_to,
					"party_type": "Customer",
					"party": self.customer,
					"against": self.write_off_account,
					"credit": self.base_write_off_amount,
					"credit_in_account_currency": self.base_write_off_amount \
						if self.party_account_currency==self.company_currency else self.write_off_amount,
					"against_voucher": self.return_against if cint(self.is_return) else self.name,
					"against_voucher_type": self.doctype
				}, self.party_account_currency)
			)
			gl_entries.append(
				self.get_gl_dict({
					"account": self.write_off_account,
					"against": self.customer,
					"debit": self.base_write_off_amount,
					"debit_in_account_currency": self.base_write_off_amount \
						if write_off_account_currency==self.company_currency else self.write_off_amount,
					"cost_center": self.write_off_cost_center or default_cost_center
				}, write_off_account_currency)
			)


def set_account_for_mode_of_payment(self):
	for data in self.payments:
		if not data.account:
			data.account = get_bank_cash_account(data.mode_of_payment, self.company).get("account")

@frappe.whitelist()
def get_bank_cash_account(mode_of_payment, company):
	account = frappe.db.get_value("Mode of Payment Account",
		{"parent": mode_of_payment, "company": company}, "default_account")
	if not account:
		frappe.throw(_("Please set default Cash or Bank account in Mode of Payment {0}")
			.format(mode_of_payment))
	return {
		"account": account
	}

@frappe.whitelist()
def mode_of_payment(company):
	return frappe.db.sql(""" select mpa.default_account, mpa.parent, mp.type as type from `tabMode of Payment Account` mpa,
		 `tabMode of Payment` mp where mpa.parent = mp.name and mpa.company = %(company)s""", {'company': company}, as_dict=True)


@frappe.whitelist()
def lista_clientes():

	return frappe.db.sql("""select name from `tabCustomer` """, as_dict=False)


@frappe.whitelist()
def quartos_reservados():

	return frappe.db.sql("""select name,numero_quarto,check_in,reservation_status from `tabReservas` where reservation_status = 'Nova' """, as_dict=True)



@frappe.whitelist()
def atualiza_ccorrente(cliente,recibo):
	for ccorrente1 in frappe.db.sql("""SELECT name,numero_registo,parent,status_conta_corrente from `tabCC_detalhes` where numero_registo = %s and parent = %s """, (recibo,cliente), as_dict=True):
		reset_idx = frappe.get_doc("CC_detalhes",ccorrente1.name)
		reset_idx.status_conta_corrente = "Pago"
		reset_idx.save()


@frappe.whitelist()
def debit_to_acc(company):
	return frappe.db.sql("""select name from `tabAccount` where account_type='Receivable' and is_group=0 and company = %s """,company, as_dict=False)


def alert(param):
	pass


@frappe.whitelist()
def get_perfil_pos(doc):

	pos_profile = get_pos_profile(doc.company) or {}
	if not pos_profile:
		alert("Este usuario nao tem perfil para vendas\n Deve configurar no POS (Ponto de Venda).")

	return {
#		'doc': doc,
#		'default_customer': pos_profile.get('customer'),
#		'items': get_items_list(pos_profile),
#		'customers': get_customers_list(pos_profile),
#		'serial_no_data': get_serial_no_data(pos_profile, doc.company),
#		'batch_no_data': get_batch_no_data(),
#		'tax_data': get_item_tax_data(),
#		'price_list_data': get_price_list_data(doc.selling_price_list),
#		'bin_data': get_bin_data(pos_profile),
#		'pricing_rules': get_pricing_rule_data(doc),
#		'print_template': print_template,
		'pos_profile': pos_profile
#		'meta': get_meta()
	}
