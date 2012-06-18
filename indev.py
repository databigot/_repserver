#! /usr/bin/python

import txn_detail_def
from report_query_framework import *
from flask import render_template_string, render_template, request, make_response,g
from forms_and_fields import *

def debug_0(q):
#		out = """
#		Qualifiers:
#			{%- for k,v in query_qualifiers|dictsort %}
#				{{k}}: \t{{ v.value_raw | string }}
#			{%- endfor %}
#		"""
#		render_template_string(out, query_qualifiers=q.qualifiers))
		resp = make_response(q.debug_qualifiers())
		resp.mimetype='text/plain'
		return resp

def test_args():
	q = Q_Test_Args()
	if request.method == 'GET':
		x = """
		<head></head>
		<body>
				{{FORM}}
		</body>
		"""
		form = q.form(q.make_fieldlist())

		return render_template_string(x, FORM=form) #submit back to me.

	if request.method == 'POST':
		q.post_pull_qualifiers(request.form)
		q.qualify()
		return debug_0(q)
		
		print q.sql	
		result_set = q.load_dataset()
	#	META = build_meta(args, r, q)	
		return render_template("report2.html", COLS=r.COLS_OUT , ROWS=result_set["ROWS"] , TITLE=r.title , SUBTITLE=r.subtitle );


def lr_request_rpt():
	PICK_REPORT = [txn_detail_def.R_Txn_Detail(), txn_detail_def.R_MSN_Detail(), txn_detail_def.R_TXNPayment_Detail()]
	PICK_FORMAT = {
        	'json': utils.data_to_json
        	, 'csv': utils.data_to_csv
        	, 'html-table': utils.data_to_htmltable
        	, 'text-table': utils.data_to_texttable}

#class PickReportForm(BaseForm): #TODO: create BASEFORM class
#	"""request a report"""
	myForm = SuperCoolForm ( #initiate with a list of args that inherit type BaseField or BaseValidate, it will know what to do with them.
		#nb. THIS WILL NOT keep it in order, but it will pass the names in, and not use metaclass (yet).
		request_by = InputField('request_by', disabled=True, label='Requestor', dtype=str, default=g.user)
		,request_at = InputField('request_at', disabled=True, label='@', dtype=datetime, default=datetime.datetime.now())

		,report = DropChoiceField('report', label='Report', required=True, default='', option_prefix='--pick one--', 
			options=[(r.slug, r.title) for r in PICK_REPORT])
	#TODO: load these dynamically from query definition:
		,publisher = DropChoiceField('publisher', label='Publisher', default='', option_prefix ='--ALL--', 
			options = sql_pull_lookup("""SELECT name, title 
						FROM core_publisher
						WHERE status = 'active'
						ORDER BY title;""")
			) 
		,start_dt = InputField('start_dt', label='Start date', dtype=datetime.datetime, default=None,
			help='Include transactions after (or on) this starting date; format is MM/DD/YYYY') 
		,end_dt = InputField('end_dt', label='End date', dtype=datetime.datetime, default=None,
			help='Include transactions before (or on) this ending date; format is MM/DD/YYYY')

#				is_valid() = function(form.fields**) {
			#try the coerce first, to check if valid date at all
#			#NOTE: will ONLY be called if non-zero, and valid coercion, if blank NOT validated.
#			if end_dt > today:
#				raise "Sorry, date is in future"
#			if start_dt and end_dt < start_dt:
#				raise "End date must be on or after Start date"
#			return True 

		)
	myForm.addField( #whoops forgot one.
		format = RadioChoiceField('format', label='Format',required=True, options=zip(PICK_FORMAT.keys(),PICK_FORMAT.keys()), 
			default=None, help= 'Pick the layout format'))
	myForm  + InputField('limit', dtype=int, label='LIMIT', default=100, 
			help='Limit the query to ## rows only.  Set to 0 or blank for ALL') \
		+ CheckboxField('sql_only', dtype=bool, default=False, label='SQL only (no run!)', 
			help='Just show generated SQL, do NOT throw at the database.')

		
	if myForm.not_valid(request): #can be not valid because first GET, or invalid data on POST.
		return make_response(myForm.render_me())
	else: #ok, fields are filled in, and are valid, and form is valid, do Magic()
			#can still include form if desired in rendered page, (e.g.at top)
		return make_repsonse("<body><h2>Success</h2></body>")
		



