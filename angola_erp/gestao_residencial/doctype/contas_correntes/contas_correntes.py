# -*- coding: utf-8 -*-
# Copyright (c) 2015, Helio de Jesus and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr, flt, getdate
from frappe.model.document import Document
from frappe.model.naming import make_autoname
import sys


class ContasCorrentes(Document):

	def autoname(self):
		self.name = self.cc_nome_cliente


@frappe.whitelist()
def ordem_idx(cliente):

	numero = 1
	for t in frappe.db.sql(""" SELECT idx,name,parent,status_conta_corrente from tabCC_detalhes where parent =%s ORDER BY status_conta_corrente ASC  """,cliente,as_dict=True):
#		print t.parent
		reset_idx = frappe.get_doc("CC_detalhes",t.name)


		reset_idx.idx = numero
		numero = numero + 1
		reset_idx.save()


@frappe.whitelist()
def set_bar_restaurante_cc():

#	for clientes in frappe.db.sql("""SELECT name, cliente_tipo from tabCLIENTES where cliente_tipo ='Membro' """,as_dict=True):
	for clientes in frappe.db.sql("""SELECT name from tabCustomer  """,as_dict=True):
		#Cria o Cliente no CONTAS_CORRENTES ....as already exists records...
		
		if (frappe.db.sql("""select cc_nome_cliente from `tabContas Correntes` WHERE cc_nome_cliente =%s """,clientes.name, as_dict=False)) == ():

			ccorrente = frappe.new_doc("Contas Correntes")
			ccorrente.cc_nome_cliente = clientes.name
			ccorrente.name = clientes.name
			ccorrente.cc_status_conta_corrente = "Não Pago"
			ccorrente.insert()
		get_bar_restaurante_cc(clientes.name)


@frappe.whitelist()
def get_bar_restaurante_cc(cliente):

	for cc in frappe.db.sql("""select name,status_atendimento,conta_corrente,conta_corrente_status,total_servicos,hora_atendimento from `tabAtendimento Bar` where conta_corrente = %s """,cliente,as_dict=True):

		ccdetalhes = frappe.db.get_value("CC_detalhes",cc.name,"numero_registo")

		if ccdetalhes:
			#Registo existe
			totalextra = 0
			cc_detalhes = frappe.get_doc("CC_detalhes",ccdetalhes)	

			if cc_detalhes.total != cc.total_servicos: 
				cc_detalhes.total = cc.total_servicos #extras.total_extra

			if cc_detalhes.status_conta_corrente != cc.conta_corrente_status:
				cc_detalhes.status_conta_corrente = cc.conta_corrente_status #"Não Pago"

			totalextra = totalextra + flt(cc.total_servicos) #extras.total_extra
					
			cc_detalhes.save()

		else:
			#Nao exist
			totalextra = 0

			cc_detalhes = frappe.new_doc("CC_detalhes")
			cc_detalhes.parent = cliente
			cc_detalhes.parentfield = "cc_table_detalhes"
			cc_detalhes.parenttype = "Contas Correntes"

			cc_detalhes.descricao_servico = cc.name

			cc_detalhes.numero_registo = cc.name
			cc_detalhes.total = cc.total_servicos #extras.total_extra
			cc_detalhes.data_registo = cc.hora_atendimento
			cc_detalhes.status_conta_corrente = cc.conta_corrente_status #"Não Pago"
			cc_detalhes.tipo = "Bar"
#			cc_detalhes.name = cc.name #self.name
			cc_detalhes.idx += 1	
					
			cc_detalhes.insert()

			totalextra = totalextra + flt(cc.total_servicos) #extras.total_extra


	#Update Quartos records too
	get_quartos_cc(cliente)

	#Call Ordem IDX
	ordem_idx(cliente)
			


@frappe.whitelist()
def get_quartos_cc(cliente):
	for cc in frappe.db.sql("""select name,status_quarto,conta_corrente,conta_corrente_status,total,total_servicos,hora_entrada from `tabGestao de Quartos` where conta_corrente = %s and status_quarto='Fechado' """,cliente,as_dict=True):
		ccdetalhes = frappe.db.get_value("CC_detalhes",cc.name,"numero_registo")

		if ccdetalhes:
			#Registo existe
			totalextra = 0
			cc_detalhes = frappe.get_doc("CC_detalhes",ccdetalhes)	

			if cc_detalhes.total != cc.total: 
				cc_detalhes.total = cc.total #extras.total_extra

			if cc_detalhes.total_servicos != cc.total_servicos: 
				cc_detalhes.total_servicos = cc.total_servicos #extras.total_extra


			if cc_detalhes.status_conta_corrente != cc.conta_corrente_status:
				cc_detalhes.status_conta_corrente = cc.conta_corrente_status #"Não Pago"

			totalextra = totalextra + flt(cc.total_servicos)  + flt(cc.total) #extras.total_extra
					
			cc_detalhes.save()

		else:
			totalextra = 0

			cc_detalhes = frappe.new_doc("CC_detalhes")
			cc_detalhes.parent = cliente
			cc_detalhes.parentfield = "cc_table_detalhes"
			cc_detalhes.parenttype = "Contas Correntes"

			cc_detalhes.descricao_servico = cc.name

			cc_detalhes.numero_registo = cc.name
			cc_detalhes.total = cc.total #extras.total_extra
			cc_detalhes.total_servicos = cc.total_servicos #extras.total_extra
			cc_detalhes.data_registo = cc.hora_entrada
			cc_detalhes.status_conta_corrente = cc.conta_corrente_status #"Não Pago"
			cc_detalhes.tipo = "Quarto"

			cc_detalhes.idx += 1	
					
			cc_detalhes.insert()

			totalextra = totalextra + flt(cc.total_servicos) + flt(cc.total) #extras.total_extra


		#Call Ordem IDX
		ordem_idx(cliente)	

@frappe.whitelist()
def set_quartos_cc(cliente):
	quarto = frappe.get_doc("Gestao de Quartos",cliente)
	quarto.conta_corrente_status = "Pago"
	quarto.save()
		
@frappe.whitelist()
def set_bar_cc(cliente):
	bar = frappe.get_doc("Atendimento Bar",cliente)
	bar.conta_corrente_status = "Pago"
	bar.save()

@frappe.whitelist()
def set_bar_quartos_cc(cliente):
	for client in frappe.db.sql("""SELECT name,parent,numero_registo,descricao_servico,status_conta_corrente,cc_tipo from tabCC_detalhes where parent = %s """,cliente,as_dict=True):

		if client.cc_tipo == "Bar":
			bar = frappe.get_doc("Atendimento Bar",client.name)
			bar.conta_corrente_status = "Pago"
			bar.save()

		elif client.cc_tipo == "Quarto":
			quarto = frappe.get_doc("Gestao de Quartos",client.name)
			quarto.conta_corrente_status = "Pago"
			quarto.save()

		cc = frappe.get_doc("CC_detalhes",client.name)
		cc.status_conta_corrente = "Pago"
		cc.save()
