# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import frappe.utils
import frappe.sessions
import frappe.utils.file_manager
import frappe.desk.form.run_method
from frappe.utils.response import build_response
from werkzeug.wrappers import Response
from six import string_types

import json
from sys import argv

import time

# from pymessenger.bot import Bot
from lxml import html
import requests

from frappe.utils import encode

def handle1():
	"""handle request"""
	cmd = frappe.local.form_dict.cmd
	data = None

	if cmd!='login':
		pass
		# data = execute_cmd(cmd)

	if data:
		if isinstance(data, Response):
			# method returns a response object, pass it on
			return data

		# add the response to `message` label
		frappe.response['message'] = data

	return build_response("json")

def execute_cmd1(cmd, from_async=False):
	"""execute a request as python module"""
	for hook in frappe.get_hooks("override_whitelisted_methods", {}).get(cmd, []):
		# override using the first hook
		cmd = hook
		break

	try:
		method = frappe.get_attr(cmd)
	except:
		frappe.respond_as_web_page(title='Invalid Method', html='Method not found',
			indicator_color='red', http_status_code=404)
		return

	if from_async:
		method = method.queue

	# is_whitelisted(method)

	return frappe.call(method, **frappe.form_dict)


def is_whitelisted1(method):
	# check if whitelisted
	if frappe.session['user'] == 'Guest':
		if (method not in frappe.guest_methods):
			frappe.msgprint(_("Not permitted"))
			raise frappe.PermissionError('Not Allowed, {0}'.format(method))

		if method not in frappe.xss_safe_methods:
			# strictly sanitize form_dict
			# escapes html characters like <> except for predefined tags like a, b, ul etc.
			for key, value in frappe.form_dict.items():
				if isinstance(value, string_types):
					frappe.form_dict[key] = frappe.utils.sanitize_html(value)

	else:
		if not method in frappe.whitelisted:
			frappe.msgprint(_("Not permitted"))
			raise frappe.PermissionError('Not Allowed, {0}'.format(method))

@frappe.whitelist()
def runserverobj1(method, docs=None, dt=None, dn=None, arg=None, args=None):
	frappe.desk.form.run_method.runserverobj(method, docs=docs, dt=dt, dn=dn, arg=arg, args=args)

@frappe.whitelist(allow_guest=True)
def logout1():
	frappe.local.login_manager.logout()
	frappe.db.commit()

@frappe.whitelist(allow_guest=True)
def web_logout1():
	frappe.local.login_manager.logout()
	frappe.db.commit()
	frappe.respond_as_web_page(_("Logged Out"), _("You have been successfully logged out"),
		indicator_color='green')

@frappe.whitelist(allow_guest=True)
def run_custom_method1(doctype, name, custom_method):
	"""cmd=run_custom_method&doctype={doctype}&name={name}&custom_method={custom_method}"""
	doc = frappe.get_doc(doctype, name)
	if getattr(doc, custom_method, frappe._dict()).is_whitelisted:
		frappe.call(getattr(doc, custom_method), **frappe.local.form_dict)
	else:
		frappe.throw(_("Not permitted"), frappe.PermissionError)

@frappe.whitelist()
def uploadfile1():
	try:
		if frappe.form_dict.get('from_form'):
			try:
				ret = frappe.utils.file_manager.upload()
			except frappe.DuplicateEntryError:
				# ignore pass
				ret = None
				frappe.db.rollback()
		else:
			if frappe.form_dict.get('method'):
				method = frappe.get_attr(frappe.form_dict.method)
				# is_whitelisted(method)
				ret = method()
	except Exception:
		frappe.errprint(frappe.utils.get_traceback())
		frappe.response['http_status_code'] = 500
		ret = None

	return ret


def get_attr1(cmd):
	"""get method object from cmd"""
	if '.' in cmd:
		method = frappe.get_attr(cmd)
	else:
		method = globals()[cmd]
	frappe.log("method:" + cmd)
	return method

@frappe.whitelist()
def ping1():
	return "pong"



@frappe.whitelist(allow_guest=True)
def fbtoken(**kwargs):

	clientID = '467986423542306'
	clientSecret = '2a8ee5a2df2701d062246b4546dbc1e3'
	fbaccess_token = 'EAAGpoZASI8iIBAPpWSmlMyYoGZA8ZBDwf4YbToK9YHZCCEbRZB15nGdqMmH981eBdLdgUtZCVUnY6ZChUlKyONoKQYNumzMTkMZBQcamkYGJ359P4fmHebZCIjUCJEnNKpxKFZBQwxVt5XHdZBftxtQTk8XeCBBpEJZBvr8SBuZCVEAtHkAZDZD'

	appLink = 'https://graph.facebook.com/oauth/access_token?client_id=' + clientID + '&client_secret=' + clientSecret + '&grant_type=client_credentials'
	appToken = requests.get(appLink).json()['access_token']

	# bot = Bot(fbaccess_token)
	metodo = frappe.local.request.method
	# print "METODO"
	# print metodo
	cmd = frappe.local.form_dict.cmd
	# print time.localtime()
	data =  frappe.local.form_dict.data
	# print "API FBTOKEN"
	# print "CMD"
	# print cmd
	# print "DATA..."
	# print type(data)
	# print data
	# print "DATA ENTRY"
	try:
		data1 = json.loads(data)
		# print data1['entry']
	except ValueError as e:
		pass
		# print False

	# print "ARGS"
	# if kwargs:
	# 	print kwargs


	#{'hub.verify_token': u'token', 'hub.challenge': u'1600257574', 'cmd': u'angola_erp.handler.fbtoken', 'hub.mode': u'subscribe', 'data': u''}
	if kwargs.get('hub.verify_token'):
		fb_verifyToken = kwargs['hub.verify_token']
		fb_challenge = kwargs['hub.challenge']
		fb_hub = kwargs['hub.mode']


		# print "FBTOKEN"
		# print fb_verifyToken
		# print fb_hub
		# print "Challenge"
		# print type(kwargs)
		# print kwargs.get('hub.challenge')


		if fb_hub == 'subscribe' and fb_verifyToken == 'token':
		        # print "TOKEN CORRETA"
	    		frappe.local.response['http_status_code'] = 200
		        return Response(kwargs.get('hub.challenge'))


	# print "DATA OBJECTs, MESSAGE, SENDER"

	if data1['object'] == 'page':

		# print "PAGE MESSAGE"
		# print data1['entry']
		# print "PAGE ENTRY 0"
		# print data1['entry'][0].get('changes')
		# print 'PAGE  Changes'
		# print data1['entry'][0]['changes'][0].get('field')
		#print 'PAGE Messagin'
		#print data1['entry'][0].get('messaging')



		if data1['entry'][0].get('messaging'):
		        # print "MESSAGING"
		        # print data1['entry'][0]['messaging'][0]['message']
		        # print data1['entry'][0]['messaging'][0]['message']['text']
		        # print "PAGE SENDER"
		        # print data1['entry'][0]['messaging'][0]['sender']
		        # print data1['entry'][0]['messaging'][0]['recipient']

	    		recipient_id = data1['entry'][0]['messaging'][0]['sender']['id'] 


		        if data1['entry'][0]['messaging'][0]['message']['text'].startswith('This is a test message from the Facebook team.'):
		                #reply the message
		                # print "RESPOSTA FACEBOOK TEAM"
				# bot.send_text_message(recipient_id, "AngolaERP BOT working")
				frappe.local.response['http_status_code'] = 200
		                return Response("AngolaERP Bot Working.")
			elif data1['entry'][0]['messaging'][0]['message'].get('text'):
				resposta_sent_text = "AngolaERP BOT! Obrigado pelo seu contacto"
				# bot.send_text_message(recipient_id, resposta_sent_text)
				frappe.local.response['http_status_code'] = 200
				return Response("Resposta enviada")

		elif data1['entry'][0]['changes']:
		        # print "ENTRY CHANGES"
		        # print data1['entry'][0]['changes'][0]['field']
		        # print data1['entry'][0]['changes'][0]['value']
			
			if data1['entry'][0]['changes'][0]['field'] == 'conversations':
				pass
				# print "CONVERSAS "
				# print data1['entry'][0]['changes'][0]['value']
			elif data1['entry'][0]['changes'][0]['field'] == 'messages':
				pass
				# print "Mensagens"
				# print  data1['entry'][0]['changes'][0]['value']

			# elif data1['entry'][0]['changes'][0]['field'] == 'feed':
			# 	print "FEEDS na Pagina"
			# 	print data1['entry'][0]['changes'][0]['value']


	elif data1['object'] == 'user':
		# print "OJECT USER"
		# print data1['entry'][0]['changes'][0].get('field')
		if data1['entry'][0]['changes'][0]['field'] == 'message_sends':
			pass
		    # print 'MESSAGE SENDS'
		    # print data1['entry'][0]['changes'][0]['value']
		    # print data1['entry'][0]['changes'][0]['value']['from']
		    # print data1['entry'][0]['changes'][0]['value']['from']['email']
		    # print data1['entry'][0]['changes'][0]['value']['from']['name']
		    # print data1['entry'][0]['changes'][0]['value']['message']
		elif data1['entry'][0]['changes'][0]['field'] == 'feed':
		    # print "Feed"
		    # print data1['entry'][0]['id']
		    meID = data1['entry'][0]['id'] 
		    feedsID = requests.get('https://graph.facebook.com/v2.12/' + meID + '/feed?access_token=' + fbaccess_token)
		    # print "FEEDSID"
		    # print feedsID
		    # print feedsID.status_code

		    if feedsID.status_code == 200:
			for feeds_id in json.loads(feedsID.content)['data']:
				pass
			    # print "Feeds"
			    # print  feeds_id

	frappe.local.response['http_status_code'] = 200
	return Response('AngolaERP Bot v0')


@frappe.whitelist(allow_guest=True)
def aerpversion():
	# print frappe.get_attr("angola_erp"+".__version__")
	return frappe.get_attr("angola_erp"+".__version__")


