# -*- coding: utf-8 -*-
# Copyright (c) 2015, helio and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr, flt, getdate, encode
from frappe.model.document import Document
import frappe.model
import frappe.utils
import datetime

import sys

@frappe.whitelist()
def get_lista_retencoes():
	j= frappe.db.sql(""" SELECT name, descricao, percentagem from `tabRetencoes` """,as_dict=True)
	return j



@frappe.whitelist()
#TO BE REMOVED IF Client ERPNEXT v8
def set_faltas1(mes,ano,empresa):
	for tra in frappe.db.sql(""" SELECT name,status from tabEmployee where status = 'Active' and company = %s """,(empresa), as_dict=True):

		j= frappe.db.sql(""" SELECT count(status)
		from `tabAttendance` where employee = %s and status = 'Absent' and month(att_date) = %s and year(att_date) = %s and docstatus=1 """,(tra.name,mes,ano), as_dict=False)

		j4= frappe.db.sql(""" SELECT count(status) from `tabAttendance` where employee = %s and status = 'Half Day' and month(attendance_date) = %s and year(attendance_date) = %s and docstatus=1 """,(tra.name,mes,ano), as_dict=False)

		#save on Employee record
		j1 = frappe.get_doc("Employee",tra.name)
		j1.numer_faltas = flt(j[0][0]) + (flt(j4[0][0])/2)
		j1.save()
	return j

@frappe.whitelist()
def set_faltas(mes,ano,empresa):
	for tra in frappe.db.sql(""" SELECT name,status from tabEmployee where status = 'Active' and company = %s """,(empresa), as_dict=True):

		#Faltas Injustificadas
		j= frappe.db.sql(""" SELECT count(status)
		from `tabAttendance` where employee = %s and status = 'Absent' and tipo_de_faltas = 'Falta Injustificada' and processar_mes_seguinte = 0 and month(attendance_date) = %s and year(attendance_date) = %s and docstatus=1 """,(tra.name,mes,ano), as_dict=False)

		#Faltas Justificadas C/Salario
		ja= frappe.db.sql(""" SELECT count(status)
		from `tabAttendance` where employee = %s and status = 'Absent' and tipo_de_faltas = 'Falta Justificada C/Salario' and month(attendance_date) = %s and year(attendance_date) = %s and docstatus=1 """,(tra.name,mes,ano), as_dict=False)

		j2 = frappe.db.sql(""" SELECT count(status)
		from `tabLeave Application` where status = 'Approved' and month(from_date) = %s and year(from_date) = %s and employee = %s and subsidio_de_ferias=1 and docstatus=1 """,(mes,ano,tra.name), as_dict=False)


		j3 = frappe.db.sql(""" SELECT sum(numero_de_horas) as horas from `tabAttendance` where employee = %s and status = 'Present' and month(attendance_date) = %s and year(attendance_date) = %s and docstatus=1 """,(tra.name,mes,ano), as_dict=False)

		#Half day Injustificado
		j4= frappe.db.sql(""" SELECT count(status)
		from `tabAttendance` where employee = %s and status = 'Half Day' and processar_mes_seguinte = 0 and tipo_de_faltas = 'Falta Injustificada' and month(attendance_date) = %s and year(attendance_date) = %s and docstatus=1 """,(tra.name,mes,ano), as_dict=False)

		#print j3
		

		#Gets Faltas do previous month
		j5 = frappe.db.sql(""" SELECT count(status) from `tabAttendance` where employee = %s and (status = 'Half Day' or status = 'Absent') and tipo_de_faltas = 'Falta Injustificada' and month(attendance_date) = %s and year(attendance_date) = %s and docstatus=1 and processar_mes_seguinte = 1  """,(tra.name,int(mes)-1,ano), as_dict=False)

		j1 = frappe.get_doc("Employee",tra.name)		


		if j[0][0] > 0 :	
			#save on Employee record
			#j1 = frappe.get_doc("Employee",tra.name
			
			j1.numer_faltas = j[0][0]
			#j1.save()
		else:		
			#save on Employee record
			#j1 = frappe.get_doc("Employee",tra.name)
			j1.numer_faltas = 0
			#j1.save()

		if j2[0][0] > 0:
			#save on Employee record
			#j1 = frappe.get_doc("Employee",tra.name)

			j1.subsidio_de_ferias = 1			
			#j1.save()
		else:
			#save on Employee record
			#j1 = frappe.get_doc("Employee",tra.name)
			j1.subsidio_de_ferias = 0
			#j1.save()

		if j3[0][0] > 0:
			#save on Employee record
			#j1 = frappe.get_doc("Employee",tra.name)

			j1.horas_extras = j3[0][0]			
			#j1.save()
		else:
			#save on Employee record
			#j1 = frappe.get_doc("Employee",tra.name)
			j1.horas_extras = 0
			#j1.save()


		if j4[0][0] > 0:
			#save on Employee record
			#j1 = frappe.get_doc("Employee",tra.name)
			j1.numer_faltas = flt(j[0][0])	+ (flt(j4[0][0])/2)
			#j1.save()
		else:
			#save on Employee record
			#j1 = frappe.get_doc("Employee",tra.name)
			if j[0][0]  < 0 :
				j1.numer_faltas = 0
			#j1.save()


		if j5[0][0] > 0:
			#save on Employee record
			#j1 = frappe.get_doc("Employee",tra.name)
			j1.numer_faltas = flt(j[0][0])	+ (flt(j4[0][0])/2) + flt(j5[0][0])
			#j1.save()
		else:
			#save on Employee record
			#j1 = frappe.get_doc("Employee",tra.name)
			if j5[0][0]  < 0 :
				j1.numer_faltas = 0
			#j1.save()

		j1.save()




	return j



@frappe.whitelist()
def set_salary_slip_pay_days(pag,emp,ano,mes):
	ret = {}
	j= frappe.db.sql(""" UPDATE `tabSalary Slip` SET payment_days = %s where employee = %s and fiscal_year = %s and month = %s """,(pag,emp,ano,mes), as_dict=False)



@frappe.whitelist()
def get_faltas(emp,mes,ano, empresa):

	#Falta Injustificada
	j= frappe.db.sql(""" SELECT count(status)
	from `tabAttendance` where employee = %s and status = 'Absent' and tipo_de_faltas = 'Falta Injustificada' and month(attendance_date) = %s and year(attendance_date) = %s and company = %s and docstatus=1 """,(emp,mes,ano, empresa), as_dict=False)

	j2 = frappe.db.sql(""" SELECT count(status)
	from `tabLeave Application` where status = 'Approved' and month(from_date) = %s and year(from_date) = %s and employee = %s and subsidio_de_ferias=1 and docstatus=1 """,(mes,ano,emp), as_dict=False)

	#Half day Falta Injustificada
	j3= frappe.db.sql(""" SELECT count(status) from `tabAttendance` where employee = %s and status = 'Half Day' and tipo_de_faltas = 'Falta Injustificada' and month(attendance_date) = %s and year(attendance_date) = %s and docstatus=1 and company = %s """,(emp,mes,ano,empresa), as_dict=False)

	
	#save on Employee record
	j1 = frappe.get_doc("Employee",emp)
	j1.numer_faltas = flt(j[0][0]) + (flt(j3[0][0])	/ 2)

	if j2[0][0] > 0:
		#save on Employee record
		j1.subsidio_de_ferias = 1
	else:
		#save on Employee record
		j1.subsidio_de_ferias = 0
	
	j1.save()
	return j


@frappe.whitelist()
def get_irt(start):
	ret = {}
	j= frappe.db.sql(""" SELECT valor_inicio, valor_fim, valor_percentual,parcela_fixa
	from `tabIRT` where valor_inicio <= %(start)s and valor_fim >=%(start)s """,{
	"start": start}, as_dict=True)
	# if J is ZERO than should get LAST RECORD.

	if not j:
		ret = frappe.db.sql("""SELECT valor_inicio, valor_fim, valor_percentual, parcela_fixa
		from `tabIRT` ORDER BY valor_inicio DESC LIMIT 1""")
	return j

@frappe.whitelist()
def get_lista_irt():
	j= frappe.db.sql(""" SELECT valor_inicio, valor_fim, valor_percentual,parcela_fixa
	from `tabIRT` """,as_dict=True)
	return j


@frappe.whitelist()
def get_inss():

	return frappe.db.get_value("INSS",None,"seguranca_social")


@frappe.whitelist()
def set_ded(ded,d_val):

#	jj= frappe.db.sql("UPDATE `tabSalary Detail` SET default_amount=%s where name =%s",(flt(d_val),ded))
	jj= frappe.db.sql("UPDATE `tabSalary Detail` SET amount=%s, default_amount=%s where name =%s",(flt(d_val),flt(d_val),ded))

	return jj




@frappe.whitelist()
def seguranca_social(jv_entry):
	pass
	#Read values from the JV created and get 72221 account value to calculate 8% and deposit on 7252 (Deb) and 3461 (Cre)


