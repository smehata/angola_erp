# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe.utils import nowdate, cstr, flt, cint, now, getdate
from frappe import throw, _
from frappe.utils import formatdate

# imported to enable erpnext.accounts.utils.get_account_currency
from erpnext.accounts.doctype.account.account import get_account_currency
import frappe.defaults
from erpnext.accounts.report.financial_statements import sort_root_accounts

class FiscalYearError(frappe.ValidationError): pass

@frappe.whitelist()
def get_fiscal_year(date=None, fiscal_year=None, label="Date", verbose=1, company=None, as_dict=False):
	return get_fiscal_years(date, fiscal_year, label, verbose, company, as_dict=as_dict)[0]

def get_fiscal_years(transaction_date=None, fiscal_year=None, label="Date", verbose=1, company=None, as_dict=False):
	# if year start date is 2012-04-01, year end date should be 2013-03-31 (hence subdate)
	cond = " disabled = 0"
	if fiscal_year:
		cond += " and fy.name = %(fiscal_year)s"
	else:
		cond += " and %(transaction_date)s >= fy.year_start_date and %(transaction_date)s <= fy.year_end_date"

	if company:
		cond += """ and (not exists(select name from `tabFiscal Year Company` fyc where fyc.parent = fy.name)
			or exists(select company from `tabFiscal Year Company` fyc where fyc.parent = fy.name and fyc.company=%(company)s ))"""

	fy = frappe.db.sql("""select fy.name, fy.year_start_date, fy.year_end_date from `tabFiscal Year` fy
		where %s order by fy.year_start_date desc""" % cond, {
			"fiscal_year": fiscal_year,
			"transaction_date": transaction_date,
			"company": company
		}, as_dict=as_dict)

	if not fy:
		error_msg = _("""{0} {1} not in any active Fiscal Year. For more details check {2}.""").format(label, formatdate(transaction_date), "https://frappe.github.io/erpnext/user/manual/en/accounts/articles/fiscal-year-error")
		if verbose==1: frappe.msgprint(error_msg)
		raise FiscalYearError
		return fy

def validate_fiscal_year(date, fiscal_year, label=_("Date"), doc=None):
	years = [f[0] for f in get_fiscal_years(date, label=label)]
	if fiscal_year not in years:
		if doc:
			doc.fiscal_year = years[0]
		else:
			throw(_("{0} '{1}' not in Fiscal Year {2}").format(label, formatdate(date), fiscal_year))

@frappe.whitelist()
def get_balance_on(account=None, date=None, party_type=None, party=None, company=None, in_account_currency=True):
	if not account and frappe.form_dict.get("account"):
		account = frappe.form_dict.get("account")
	if not date and frappe.form_dict.get("date"):
		date = frappe.form_dict.get("date")
	if not party_type and frappe.form_dict.get("party_type"):
		party_type = frappe.form_dict.get("party_type")
	if not party and frappe.form_dict.get("party"):
		party = frappe.form_dict.get("party")

	cond = []
	if date:
		cond.append("posting_date <= '%s'" % frappe.db.escape(cstr(date)))
	else:
		# get balance of all entries that exist
		date = nowdate()

	try:
		year_start_date = get_fiscal_year(date, verbose=0)[1]
	except FiscalYearError:
		if getdate(date) > getdate(nowdate()):
			# if fiscal year not found and the date is greater than today
			# get fiscal year for today's date and its corresponding year start date
			year_start_date = get_fiscal_year(nowdate(), verbose=1)[1]
		else:
			# this indicates that it is a date older than any existing fiscal year.
			# hence, assuming balance as 0.0
			return 0.0

	if account:
		acc = frappe.get_doc("Account", account)

		if not frappe.flags.ignore_account_permission:
			acc.check_permission("read")

		# for pl accounts, get balance within a fiscal year
		if acc.report_type == 'Profit and Loss':
			cond.append("posting_date >= '%s' and voucher_type != 'Period Closing Voucher'" \
				% year_start_date)

		# different filter for group and ledger - improved performance
		if acc.is_group:
			cond.append("""exists (
				select name from `tabAccount` ac where ac.name = gle.account
				and ac.lft >= %s and ac.rgt <= %s
			)""" % (acc.lft, acc.rgt))

			# If group and currency same as company,
			# always return balance based on debit and credit in company currency
			if acc.account_currency == frappe.db.get_value("Company", acc.company, "default_currency"):
				in_account_currency = False
		else:
			cond.append("""gle.account = "%s" """ % (frappe.db.escape(account, percent=False), ))

	if party_type and party:
		cond.append("""gle.party_type = "%s" and gle.party = "%s" """ %
			(frappe.db.escape(party_type), frappe.db.escape(party, percent=False)))
			
	if company:
		cond.append("""gle.company = "%s" """ % (frappe.db.escape(company, percent=False)))

	if account or (party_type and party):
		if in_account_currency:
			select_field = "sum(debit_in_account_currency) - sum(credit_in_account_currency)"
		else:
			select_field = "sum(debit) - sum(credit)"
		bal = frappe.db.sql("""
			SELECT {0}
			FROM `tabGL Entry` gle
			WHERE {1}""".format(select_field, " and ".join(cond)))[0][0]

		# if bal is None, return 0
		return flt(bal)

@frappe.whitelist()
def add_ac(args=None):
	if not args:
		args = frappe.local.form_dict
		args.pop("cmd")
	
	ac = frappe.new_doc("Account")

	if args.get("ignore_permissions"):
		ac.flags.ignore_permissions = True
		args.pop("ignore_permissions")

	ac.update(args)

	if not ac.parent_account:
		ac.parent_account = args.get("parent")
	
	ac.old_parent = ""
	ac.freeze_account = "No"
	if cint(ac.get("is_root")):
		ac.parent_account = None
		ac.flags.ignore_mandatory = True

	ac.insert()

	return ac.name

@frappe.whitelist()
def add_cc(args=None):
	if not args:
		args = frappe.local.form_dict
		args.pop("cmd")

	cc = frappe.new_doc("Cost Center")
	cc.update(args)

	if not cc.parent_cost_center:
		cc.parent_cost_center = args.get("parent")

	cc.old_parent = ""
	cc.insert()
	return cc.name

def reconcile_against_document(args):
	"""
		Cancel JV, Update aginst document, split if required and resubmit jv
	"""
	for d in args:
		
		check_if_advance_entry_modified(d)			
		validate_allocated_amount(d)
		
		# cancel advance entry
		doc = frappe.get_doc(d.voucher_type, d.voucher_no)

		doc.make_gl_entries(cancel=1, adv_adj=1)

		# update ref in advance entry
		if d.voucher_type == "Journal Entry":
			update_reference_in_journal_entry(d, doc)
		else:
			update_reference_in_payment_entry(d, doc)

		# re-submit advance entry
		doc = frappe.get_doc(d.voucher_type, d.voucher_no)
		doc.make_gl_entries(cancel = 0, adv_adj =1)

def check_if_advance_entry_modified(args):
	"""
		check if there is already a voucher reference
		check if amount is same
		check if jv is submitted
	"""
	ret = None
	if args.voucher_type == "Journal Entry":
		ret = frappe.db.sql("""
			select t2.{dr_or_cr} from `tabJournal Entry` t1, `tabJournal Entry Account` t2
			where t1.name = t2.parent and t2.account = %(account)s
			and t2.party_type = %(party_type)s and t2.party = %(party)s
			and (t2.reference_type is null or t2.reference_type in ("", "Sales Order", "Purchase Order"))
			and t1.name = %(voucher_no)s and t2.name = %(voucher_detail_no)s
			and t1.docstatus=1 """.format(dr_or_cr = args.get("dr_or_cr")), args)
	else:
		party_account_field = "paid_from" if args.party_type == "Customer" else "paid_to"
		if args.voucher_detail_no:
			ret = frappe.db.sql("""select t1.name 			
				from `tabPayment Entry` t1, `tabPayment Entry Reference` t2 
				where
					t1.name = t2.parent and t1.docstatus = 1 
					and t1.name = %(voucher_no)s and t2.name = %(voucher_detail_no)s
					and t1.party_type = %(party_type)s and t1.party = %(party)s and t1.{0} = %(account)s
					and t2.reference_doctype in ("", "Sales Order", "Purchase Order") 
					and t2.allocated_amount = %(unadjusted_amount)s
			""".format(party_account_field), args)
		else:
			ret = frappe.db.sql("""select name from `tabPayment Entry`
				where
					name = %(voucher_no)s and docstatus = 1
					and party_type = %(party_type)s and party = %(party)s and {0} = %(account)s
					and unallocated_amount = %(unadjusted_amount)s
			""".format(party_account_field), args)

	if not ret:
		throw(_("""Payment Entry has been modified after you pulled it. Please pull it again."""))

def validate_allocated_amount(args):
	if args.get("allocated_amount") < 0:
		throw(_("Allocated amount can not be negative"))
	elif args.get("allocated_amount") > args.get("unadjusted_amount"):
		throw(_("Allocated amount can not greater than unadjusted amount"))

def update_reference_in_journal_entry(d, jv_obj):
	"""
		Updates against document, if partial amount splits into rows
	"""
	jv_detail = jv_obj.get("accounts", {"name": d["voucher_detail_no"]})[0]
	jv_detail.set(d["dr_or_cr"], d["allocated_amount"])
	jv_detail.set('debit' if d['dr_or_cr']=='debit_in_account_currency' else 'credit',
		d["allocated_amount"]*flt(jv_detail.exchange_rate))

	original_reference_type = jv_detail.reference_type
	original_reference_name = jv_detail.reference_name

	jv_detail.set("reference_type", d["against_voucher_type"])
	jv_detail.set("reference_name", d["against_voucher"])

	if d['allocated_amount'] < d['unadjusted_amount']:
		jvd = frappe.db.sql("""
			select cost_center, balance, against_account, is_advance,
				account_type, exchange_rate, account_currency
			from `tabJournal Entry Account` where name = %s
		""", d['voucher_detail_no'], as_dict=True)

		amount_in_account_currency = flt(d['unadjusted_amount']) - flt(d['allocated_amount'])
		amount_in_company_currency = amount_in_account_currency * flt(jvd[0]['exchange_rate'])

		# new entry with balance amount
		ch = jv_obj.append("accounts")
		ch.account = d['account']
		ch.account_type = jvd[0]['account_type']
		ch.account_currency = jvd[0]['account_currency']
		ch.exchange_rate = jvd[0]['exchange_rate']
		ch.party_type = d["party_type"]
		ch.party = d["party"]
		ch.cost_center = cstr(jvd[0]["cost_center"])
		ch.balance = flt(jvd[0]["balance"])

		ch.set(d['dr_or_cr'], amount_in_account_currency)
		ch.set('debit' if d['dr_or_cr']=='debit_in_account_currency' else 'credit', amount_in_company_currency)

		ch.set('credit_in_account_currency' if d['dr_or_cr']== 'debit_in_account_currency'
			else 'debit_in_account_currency', 0)
		ch.set('credit' if d['dr_or_cr']== 'debit_in_account_currency' else 'debit', 0)

		ch.against_account = cstr(jvd[0]["against_account"])
		ch.reference_type = original_reference_type
		ch.reference_name = original_reference_name
		ch.is_advance = cstr(jvd[0]["is_advance"])
		ch.docstatus = 1

	# will work as update after submit
	jv_obj.flags.ignore_validate_update_after_submit = True
	jv_obj.save(ignore_permissions=True)
	
def update_reference_in_payment_entry(d, payment_entry):
	reference_details = {
		"reference_doctype": d.against_voucher_type,
		"reference_name": d.against_voucher,
		"total_amount": d.grand_total,
		"outstanding_amount": d.outstanding_amount,
		"allocated_amount": d.allocated_amount,
		"exchange_rate": d.exchange_rate
	}
		
	if d.voucher_detail_no:
		existing_row = payment_entry.get("references", {"name": d["voucher_detail_no"]})[0]
		original_row = existing_row.as_dict().copy()
		existing_row.update(reference_details)
		
		if d.allocated_amount < original_row.allocated_amount:
			new_row = payment_entry.append("references")
			new_row.docstatus = 1
			for field in reference_details.keys():
				new_row.set(field, original_row[field])
			
			new_row.allocated_amount = original_row.allocated_amount - d.allocated_amount
	else:
		new_row = payment_entry.append("references")
		new_row.docstatus = 1
		new_row.update(reference_details)
		
	payment_entry.flags.ignore_validate_update_after_submit = True
	payment_entry.setup_party_account_field()
	payment_entry.set_missing_values()
	payment_entry.set_amounts()
	payment_entry.save(ignore_permissions=True)
	
def unlink_ref_doc_from_payment_entries(ref_type, ref_no):
	remove_ref_doc_link_from_jv(ref_type, ref_no)
	remove_ref_doc_link_from_pe(ref_type, ref_no)
	
	frappe.db.sql("""update `tabGL Entry`
		set against_voucher_type=null, against_voucher=null,
		modified=%s, modified_by=%s
		where against_voucher_type=%s and against_voucher=%s
		and voucher_no != ifnull(against_voucher, '')""",
		(now(), frappe.session.user, ref_type, ref_no))

def remove_ref_doc_link_from_jv(ref_type, ref_no):
	linked_jv = frappe.db.sql_list("""select parent from `tabJournal Entry Account`
		where reference_type=%s and reference_name=%s and docstatus < 2""", (ref_type, ref_no))

	if linked_jv:
		frappe.db.sql("""update `tabJournal Entry Account`
			set reference_type=null, reference_name = null,
			modified=%s, modified_by=%s
			where reference_type=%s and reference_name=%s
			and docstatus < 2""", (now(), frappe.session.user, ref_type, ref_no))

		frappe.msgprint(_("Journal Entries {0} are un-linked".format("\n".join(linked_jv))))
		
def remove_ref_doc_link_from_pe(ref_type, ref_no):
	linked_pe = frappe.db.sql_list("""select parent from `tabPayment Entry Reference`
		where reference_doctype=%s and reference_name=%s and docstatus < 2""", (ref_type, ref_no))

	if linked_pe:
		frappe.db.sql("""update `tabPayment Entry Reference`
			set allocated_amount=0, modified=%s, modified_by=%s
			where reference_doctype=%s and reference_name=%s
			and docstatus < 2""", (now(), frappe.session.user, ref_type, ref_no))
			
		for pe in linked_pe:
			pe_doc = frappe.get_doc("Payment Entry", pe)
			pe_doc.set_total_allocated_amount()
			pe_doc.set_unallocated_amount()
			pe_doc.clear_unallocated_reference_document_rows()
			
			frappe.db.sql("""update `tabPayment Entry` set total_allocated_amount=%s, 
				base_total_allocated_amount=%s, unallocated_amount=%s, modified=%s, modified_by=%s 
				where name=%s""", (pe_doc.total_allocated_amount, pe_doc.base_total_allocated_amount, 
					pe_doc.unallocated_amount, now(), frappe.session.user, pe))
		
		frappe.msgprint(_("Payment Entries {0} are un-linked".format("\n".join(linked_pe))))

@frappe.whitelist()
def get_company_default(company, fieldname):
	value = frappe.db.get_value("Company", company, fieldname)

	if not value:
		throw(_("Please set default {0} in Company {1}").format(frappe.get_meta("Company").get_label(fieldname), company))

	return value

def fix_total_debit_credit():
	vouchers = frappe.db.sql("""select voucher_type, voucher_no,
		sum(debit) - sum(credit) as diff
		from `tabGL Entry`
		group by voucher_type, voucher_no
		having sum(debit) != sum(credit)""", as_dict=1)

	for d in vouchers:
		if abs(d.diff) > 0:
			dr_or_cr = d.voucher_type == "Sales Invoice" and "credit" or "debit"

			frappe.db.sql("""update `tabGL Entry` set %s = %s + %s
				where voucher_type = %s and voucher_no = %s and %s > 0 limit 1""" %
				(dr_or_cr, dr_or_cr, '%s', '%s', '%s', dr_or_cr),
				(d.diff, d.voucher_type, d.voucher_no))

def get_stock_and_account_difference(account_list=None, posting_date=None):
	from erpnext.stock.utils import get_stock_value_on

	if not posting_date: posting_date = nowdate()

	difference = {}

	account_warehouse = dict(frappe.db.sql("""select name, warehouse from tabAccount
		where account_type = 'Stock' and (warehouse is not null and warehouse != '') and is_group=0
		and name in (%s)""" % ', '.join(['%s']*len(account_list)), account_list))

	for account, warehouse in account_warehouse.items():
		account_balance = get_balance_on(account, posting_date, in_account_currency=False)
		stock_value = get_stock_value_on(warehouse, posting_date)
		if abs(flt(stock_value) - flt(account_balance)) > 0.005:
			difference.setdefault(account, flt(stock_value) - flt(account_balance))

	return difference

def get_currency_precision(currency=None):
	if not currency:
		currency = frappe.db.get_value("Company",
			frappe.db.get_default("Company"), "default_currency", cache=True)
	currency_format = frappe.db.get_value("Currency", currency, "number_format", cache=True)

	from frappe.utils import get_number_format_info
	return get_number_format_info(currency_format)[2]

def get_stock_rbnb_difference(posting_date, company):
	stock_items = frappe.db.sql_list("""select distinct item_code
		from `tabStock Ledger Entry` where company=%s""", company)

	pr_valuation_amount = frappe.db.sql("""
		select sum(pr_item.valuation_rate * pr_item.qty * pr_item.conversion_factor)
		from `tabPurchase Receipt Item` pr_item, `tabPurchase Receipt` pr
	    where pr.name = pr_item.parent and pr.docstatus=1 and pr.company=%s
		and pr.posting_date <= %s and pr_item.item_code in (%s)""" %
	    ('%s', '%s', ', '.join(['%s']*len(stock_items))), tuple([company, posting_date] + stock_items))[0][0]

	pi_valuation_amount = frappe.db.sql("""
		select sum(pi_item.valuation_rate * pi_item.qty * pi_item.conversion_factor)
		from `tabPurchase Invoice Item` pi_item, `tabPurchase Invoice` pi
	    where pi.name = pi_item.parent and pi.docstatus=1 and pi.company=%s
		and pi.posting_date <= %s and pi_item.item_code in (%s)""" %
	    ('%s', '%s', ', '.join(['%s']*len(stock_items))), tuple([company, posting_date] + stock_items))[0][0]

	# Balance should be
	stock_rbnb = flt(pr_valuation_amount, 2) - flt(pi_valuation_amount, 2)

	# Balance as per system
	stock_rbnb_account = "Stock Received But Not Billed - " + frappe.db.get_value("Company", company, "abbr")
	sys_bal = get_balance_on(stock_rbnb_account, posting_date, in_account_currency=False)

	# Amount should be credited
	return flt(stock_rbnb) + flt(sys_bal)

def get_outstanding_invoices(party_type, party, account, condition=None):
	outstanding_invoices = []
	precision = frappe.get_precision("Sales Invoice", "outstanding_amount")

	if party_type=="Customer":
		dr_or_cr = "debit_in_account_currency - credit_in_account_currency"
		payment_dr_or_cr = "payment_gl_entry.credit_in_account_currency - payment_gl_entry.debit_in_account_currency"
	else:
		dr_or_cr = "credit_in_account_currency - debit_in_account_currency"
		payment_dr_or_cr = "payment_gl_entry.debit_in_account_currency - payment_gl_entry.credit_in_account_currency"

	invoice_list = frappe.db.sql("""
		select
			voucher_no,	voucher_type, posting_date, ifnull(sum({dr_or_cr}), 0) as invoice_amount,
			(
				select ifnull(sum({payment_dr_or_cr}), 0)
				from `tabGL Entry` payment_gl_entry
				where payment_gl_entry.against_voucher_type = invoice_gl_entry.voucher_type
					and payment_gl_entry.against_voucher = invoice_gl_entry.voucher_no
					and payment_gl_entry.party_type = invoice_gl_entry.party_type
					and payment_gl_entry.party = invoice_gl_entry.party
					and payment_gl_entry.account = invoice_gl_entry.account
					and {payment_dr_or_cr} > 0
			) as payment_amount
		from
			`tabGL Entry` invoice_gl_entry
		where
			party_type = %(party_type)s and party = %(party)s 
			and account = %(account)s and {dr_or_cr} > 0
			{condition}
			and ((voucher_type = 'Journal Entry'
					and (against_voucher = '' or against_voucher is null))
				or (voucher_type not in ('Journal Entry', 'Payment Entry')))
		group by voucher_type, voucher_no
		having (invoice_amount - payment_amount) > 0.005
		order by posting_date, name""".format(
			dr_or_cr = dr_or_cr,
			payment_dr_or_cr = payment_dr_or_cr,
			condition = condition or ""
		), {
			"party_type": party_type,
			"party": party,
			"account": account,
		}, as_dict=True)

	for d in invoice_list:
		outstanding_invoices.append(frappe._dict({
			'voucher_no': d.voucher_no,
			'voucher_type': d.voucher_type,
			'posting_date': d.posting_date,
			'invoice_amount': flt(d.invoice_amount),
			'payment_amount': flt(d.payment_amount),
			'outstanding_amount': flt(d.invoice_amount - d.payment_amount, precision),
			'due_date': frappe.db.get_value(d.voucher_type, d.voucher_no, "due_date"),
		}))
		
	outstanding_invoices = sorted(outstanding_invoices, key=lambda k: k['due_date'] or getdate(nowdate()))
	
	return outstanding_invoices


def get_account_name(account_type=None, root_type=None, is_group=None, account_currency=None, company=None):
	"""return account based on matching conditions"""
	return frappe.db.get_value("Account", {
		"account_type": account_type or '',
		"root_type": root_type or '',
		"is_group": is_group or 0,
		"account_currency": account_currency or frappe.defaults.get_defaults().currency,
		"company": company or frappe.defaults.get_defaults().company
	}, "name")

@frappe.whitelist()
def get_companies():
	"""get a list of companies based on permission"""
	return [d.name for d in frappe.get_list("Company", fields=["name"],
		order_by="name")]

@frappe.whitelist()
def get_children():
	args = frappe.local.form_dict
	doctype, company = args['doctype'], args['company']
	fieldname = frappe.db.escape(doctype.lower().replace(' ','_'))
	doctype = frappe.db.escape(doctype)

	# root
	if args['parent'] in ("Accounts", "Cost Centers"):
		fields = ", descricao, root_type, report_type, account_currency" if doctype=="Account" else ""
		acc = frappe.db.sql(""" select
			name as value, is_group as expandable {fields}
			from `tab{doctype}`
			where ifnull(`parent_{fieldname}`,'') = ''
			and `company` = %s	and docstatus<2
			order by name""".format(fields=fields, fieldname = fieldname, doctype=doctype),
				company, as_dict=1)

		if args["parent"]=="Accounts":
			sort_root_accounts(acc)
	else:
		# other
		fields = ", descricao, account_currency" if doctype=="Account" else ""
		acc = frappe.db.sql("""select
			name as value, is_group as expandable, parent_{fieldname} as parent {fields}
			from `tab{doctype}`
			where ifnull(`parent_{fieldname}`,'') = %s
			and docstatus<2
			order by name""".format(fields=fields, fieldname=fieldname, doctype=doctype),
				args['parent'], as_dict=1)

	if doctype == 'Account':
		company_currency = frappe.db.get_value("Company", company, "default_currency")
		for each in acc:
			each["company_currency"] = company_currency
			each["balance"] = flt(get_balance_on(each.get("value"), in_account_currency=False))

			if each.account_currency != company_currency:
				each["balance_in_account_currency"] = flt(get_balance_on(each.get("value")))

	return acc
