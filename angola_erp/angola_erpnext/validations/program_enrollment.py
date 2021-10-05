# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.model.document import Document
from frappe.desk.reportview import get_match_cond, get_filters_cond
from frappe.utils import comma_and


def validate(doc,method):
	if doc.student:
		#Cartao numero no Student...
		student = frappe.get_doc('Student',doc.student)
		student.cartao_numero = doc.cartao_numero
		student.save()


