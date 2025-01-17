# -*- coding: utf-8 -*-
# Copyright (c) 2015, Helio de Jesus and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint, throw
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from datetime import datetime, timedelta
from frappe.utils import cstr, get_datetime, getdate, cint, get_datetime_str

class FichadeProcesso(Document):

	def autoname(self):

		print(self.process_number)
		print(len(self.serie_tipo))
		#print(make_autoname(self.serie_tipo))
		#print('Serie ', make_autoname(self.serie_tipo)[0:len(self.serie_tipo)-1])
		if len(self.serie_tipo) == 10:
			self.process_number = make_autoname(self.serie_tipo)[0:len(self.serie_tipo)-2] + self.process_number
		else:
			if (self.serie_tipo == "ASTXXXX-"):
				#replace xxx by YEAR
				self.process_number = self.serie_tipo[0:3] + self.process_number + "-" + format(datetime.now(),"%Y")
			else:
				self.process_number = make_autoname(self.serie_tipo)[0:len(self.serie_tipo)-1] + self.process_number
		print ('numero ', self.process_number)
		self.name = self.process_number	#make_autoname(self.numero_de_processo + '/' + '.YYYY./.#####')

		#self.name = make_autoname(self.process_number + '-' + '.###')
		#self.usuario= frappe.session.user


	def validate(self):

		#Check numero processo is Number and 4 digits.
		if len(self.process_number) < 4:
			if len(self.process_number) == 1:
				self.process_number = '000' + self.process_number
			elif len(self.process_number) == 2:
				self.process_number ='00' + self.process_number
			elif len(self.process_number) == 3:
				self.process_number ='0' + self.process_number
	
		elif len(self.process_number) > 4:
			if len(self.serie_tipo) == 10:
				if len(self.process_number) != ((len(self.serie_tipo)-2)+4):
					msgprint('Numero de Processo tem que ter somente 4 digitos')
					self.process_number =None
					frappe.validated = False

			else:
				if (self.serie_tipo == "ASTXXXX-"):
					pass
				elif len(self.process_number) != ((len(self.serie_tipo)-1)+4):
					msgprint('Numero de Processo tem que ter somente 4 digitos')
					self.process_number =None
					frappe.validated = False

		elif len(self.process_number) == '0000':
			frappe.show('Numero de Processo nao pode ser 0000')
			self.process_number = None
			frappe.validated = False
		
		if len(self.servicos_processo) == 0:
			validation = False
			frappe.msgprint("Inserir pelo menos um Servico", raise_exception = 1)
	
		#if self.docstatus == 2:
		#	self.status_process = "Cancelado"

		#elif self.servicos_processo[0].servico_ficha_processo == None:
		#	validation = False
		#	frappe.msgprint("Inserir pelo menos um Servico", raise_exception = 1)
		if self.docstatus == 1 and self.status_process == 'Aberto' or self.status_process == 'Em Curso':
			self.status_process = 'Em Curso'
			self.criar_projecto()
			self.criar_salesorder()		

#		if self.docstatus == 0 and self.status_process =='Em Curso':
#			print " criarProjeto "
#			self.criar_projecto()


	def criar_projecto(self):
		criarprojeto = False
		if frappe.db.sql("""select name from `tabProject` WHERE name =%s """,(self.name), as_dict=False) ==():
			criarprojeto = True
		if criarprojeto == True:
			projecto = frappe.get_doc({
				"doctype": "Project",
				"project_name": self.name,
				"priority": "Medium",
				"status": "Open",
				"percent_complete_method": "Task Completion",
				"expected_start_date": get_datetime(frappe.utils.now()) + timedelta(days=1) ,
				"expected_end_date": get_datetime(frappe.utils.now()) + timedelta(days=5),  #self.et_delivery_process ,
				"is_active": "Yes",
				"project_type": "Internal",
				"estimated_costing": self.broker_funds,
				"customer": self.customer_reference
			})
			projecto.insert()
			frappe.msgprint('{0}{1}'.format("Ficha de Processo criado como Projeto ", self.name))

			self.project = self.name
			#create the Tasks

			for num_servicos in frappe.get_all("Servicos_Ficha_Processo",filters={'Parent':self.name},fields=['Parent','servico_ficha_processo','descricao_ficha_processo']):
#frappe.get_all("Servicos_Ficha_Processo",filters=[["Parent","like",self.process_number + "%"]],fields=["Parent","servico_ficha_processo","descricao_ficha_processo"]):

				if num_servicos.servico_ficha_processo:
		#			for num_avarias in fo_avarias:
					tarefas = frappe.get_doc({
						"doctype": "Task",
						"project": self.name,
						"subject": cstr(num_servicos.servico_ficha_processo) + ':' + cstr(num_servicos.descricao_ficha_processo),
						"status": "Open",
						"description": "Tarefa adicionada pelo Sistema",
						"exp_start_date": get_datetime(frappe.utils.now()) + timedelta(days=1),
						"exp_end_date": get_datetime(frappe.utils.now()) + timedelta(days=4), #self.et_delivery_process
						#"task_weight": 1

					})
					tarefas.insert()
					frappe.msgprint('{0}{1}'.format(num_servicos.servico_ficha_processo, " Criado como tarefa no Projecto ", self.name))


	def criar_salesorder(self):
		criarprojeto = False
		if frappe.db.sql("""select name from `tabSales Order` WHERE name =%s """,(self.name), as_dict=False) ==():
			criarprojeto = True
		if criarprojeto == True:
			projecto = frappe.get_doc({
				"doctype": "Sales Order",
				"delivery_date": get_datetime(frappe.utils.now()) + timedelta(days=2) ,
				"customer": self.customer_reference,
				"project":self.name
			})
			for num_servicos in frappe.get_all("Servicos_Ficha_Processo",filters={'Parent':self.name},fields=['Parent','servico_ficha_processo','descricao_ficha_processo','preco_ficha_processo']):
				projecto.append('items',{
					"item_code": num_servicos.servico_ficha_processo,
					"item_name": num_servicos.descricao_ficha_processo,
					"description": num_servicos.descricao_ficha_processo,
					"rate":num_servicos.preco_ficha_processo,					
					"qty": 1
				})

						
			projecto.insert()
			frappe.msgprint('{0}{1}'.format("Ficha de Processo criado como Ordem de Venda ", projecto.name))
			#create the Tasks
			self.sales_order = projecto.name


@frappe.whitelist()
def get_projecto_status(prj):
	return frappe.db.sql("""select name,status from `tabProject` WHERE name =%s """,(prj), as_dict=False)


@frappe.whitelist()
def get_projecto_status_completed():
	return frappe.db.sql("""select name from `tabProject` WHERE status = 'Completed' """, as_dict=False)


@frappe.whitelist()
def set_ficha_closed(ficha):
	frappe.db.sql("""update `tabFicha de Processo` set status_process = 'Fechado' where name = %s """,ficha, as_dict=False)



