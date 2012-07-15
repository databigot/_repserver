#! /usr/bin/python

import os
import txn_detail_def
from report_query_framework import *
from flask import Response, render_template_string, render_template, request, make_response,g
from forms_and_fields import *
import datetime

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
	q = Q_Test_Args2()
	class MyForm(SuperCoolForm):
		pass
	myForm = MyForm(q.to_fieldlist(), 'Test Args2','a form to test the parsing of different types of fields')
#	for field in q.to_fieldlist():
#		myForm + field
	
	if myForm.redisplay_me(request): #handle GET vs.POST, and form validation
		return make_response(myForm.render_me())

	q.from_form(myForm)
	q.qualify()
	return debug_0(q)

#		print q.sql	
#		result_set = q.load_dataset()
#	#	META = build_meta(args, r, q)	
#		return render_template("report2.html", COLS=r.COLS_OUT , ROWS=result_set["ROWS"] , TITLE=r.title , SUBTITLE=r.subtitle );



def msn_detail_4():
	q = txn_detail_def.Q_MSN_Detail()
	class MyForm(SuperCoolForm):
		pass
	myForm = MyForm()
	for field in q.to_fieldlist():
		myForm + field

	if myForm.redisplay_me(request):
		return make_response(myForm.render_me())

#	q.post_pull_qualifiers(request.form)
	q.from_form(myForm)
	q.qualify()
	return debug_0(q)
	
#TODO #1:
def msn_detail_view_2():
	q = txn_detail_def.Q_MSN_Detail()

	myForm = q.as_webform()

	if myForm.redisplay_me(request):
		return make_response(myForm.render_me())

	q.from_form(myForm)
	q.qualify()
	return debug_0(q)

#TODO #2:
def msn_detail_view_3():
	q = txn_detail_def.Q_MSN_Detail()

	response = q.qualify_via_webform(request, template=None) #build form to collect qualifiers, present until valid,
	if response: return response				
							#note: will return None if all ok. 
							#the qualifiers will be properly loaded and the query will be 
	return debug_0(q)

#TODO #2:
def pmt_detail_view():
	r = txn_detail_def.R_TXNPayment_Detail() #R_MSN_Detail()
	q = txn_detail_def.Q_TXNPayment_Detail() #Q_MSN_Detail()

	#*****************************Present Form of the Qualifiers for the Report
	myForm = q.as_webform(SuperCoolForm, title=r.name, description=r.__doc__)
	myForm  + InputField('limit', dtype=int, label='LIMIT', size=5, default=100, 
			help='Limit the query to ## rows only.  Set to 0 or blank for ALL') \
		+ CheckboxField('sql_only', dtype=bool, default=False, label='SQL only (no run!)', 
			help='Just show generated SQL, do NOT throw at the database.') 
	try: 
		if myForm.process_me(request): #build form to collect qualifiers, present until valid,
			q.from_form(myForm)
			q.limit = myForm['limit']
			sql_only = myForm['sql_only']
	except (ErrorFormNew, ErrorFormInvalid):
		return make_response(myForm.render_me())
	#*****************************Done, Qualifiers are set to the User's input

#	return debug_0(q)
	q.qualify()
	if sql_only:
		return make_response("<body><pre>%s</pre></body>"%q.sql)
	
	result_set = q.load_dataset()
	DOC_OUT, MIME_TYPE, CON_TYPE = (utils.data_to_texttable)(result_set["ROWS"], r.COLS_OUT, CONTEXT={'title':'payments report'})		
	response = Response(status=200, mimetype=MIME_TYPE, content_type=CON_TYPE)
	response.data = DOC_OUT
	return response



def lr_request_rpt():
	PICK_REPORT = [txn_detail_def.R_Txn_Detail(), txn_detail_def.R_MSN_Detail(), txn_detail_def.R_TXNPayment_Detail()]
	PICK_FORMAT = {
        	'json': utils.data_to_json
        	, 'csv': utils.data_to_csv
        	, 'html-table': utils.data_to_htmltable
        	, 'text-table': utils.data_to_texttable}
	PICK_FORMAT_DEFAULT = 'text-table'
	OUTPUT_OPTS = ['S3' 
			#,'LOCAL'
			#,'STDOUT'
			,'EMAIL-ATTACH'
			,'EMAIL-EMBED']
	OUTPUT_OPTS_DEFAULT = 'EMAIL-EMBED'	

#class PickReportForm(BaseForm): #TODO: create BASEFORM class
#	"""request a report"""

	class MyForm(SuperCoolForm):  #initiate with a list of args that inherit type BaseField or BaseValidate, it will know what to do with them.
		#nb. THIS WILL NOT keep it in order, but it will pass the names in, and not use metaclass (yet).
		request_by = InputField('request_by', size=42, disabled=True, label='Requestor', dtype=str, default=g.user)
		request_at = InputField('request_at', size=30,disabled=True, label='&nbsp;&nbsp;at', dtype=str, default=datetime.datetime.now().strftime('%h-%d-%Y %I:%M%P'))

		report = DropChoiceField('report', label='Report', required=True, default='', option_prefix='--pick one--', 
			options=[(r.slug, r.title) for r in PICK_REPORT])
	#TODO: load these dynamically from query definition:
		publisher = DropChoiceField('publisher', label='Publisher', default='', option_prefix ='--ALL--', 
			options = sql_pull_lookup("""SELECT name, title 
						FROM core_publisher
						WHERE status = 'active'
						ORDER BY title;""")
			) 
		start_dt = DateField('start_dt', label='Start date', size=15, dtype=lambda x:datetime.datetime.strptime(x, r'%m/%d/%Y').date(), default=None,
			help='Include transactions after (or on) this starting date; format is MM/DD/YYYY')  
		end_dt = DateField('end_dt', label='End date', size=15, dtype=lambda x:datetime.datetime.strptime(x, r'%m/%d/%Y').date(), default=None,
			help='Include transactions before (or on) this ending date; format is MM/DD/YYYY') 
		
#				is_valid() = function(form.fields**) {
			#try the coerce first, to check if valid date at all
#			#NOTE: will ONLY be called if non-zero, and valid coercion, if blank NOT validated.
#			if end_dt > today:
#				raise "Sorry, date is in future"
#			if start_dt and end_dt < start_dt:
#				raise "End date must be on or after Start date"
#			return True 

	myForm = MyForm(title="Request A Long-Running Report", description='The report will be run and sent to you when ready.')

	myForm.addField( #whoops forgot one.
		format = RadioChoiceField('format', label='Format',required=True, options=zip(PICK_FORMAT.keys(),PICK_FORMAT.keys()), 
			default=None, help= 'Pick the layout format'))
	myForm  + InputField('limit', dtype=int, label='LIMIT', size=5, default=100, 
			help='Limit the query to ## rows only.  Set to 0 or blank for ALL') \
		+ CheckboxField('sql_only', dtype=bool, default=False, label='SQL only (no run!)', 
			help='Just show generated SQL, do NOT throw at the database.') \
		+ RadioChoiceField('out', label='Output As', options=zip(OUTPUT_OPTS, OUTPUT_OPTS),
			default=OUTPUT_OPTS_DEFAULT, help='Pick the output option') \
		+ InputField('audience', label='Audience', size=100, default=g.user, dtype=str, 
			help='recipients of the report, seperate multiple by comma or space.')
		
		

	def datesbad(start_dt=None, end_dt=None, **otherkwargs):
		if start_dt and end_dt:
			if start_dt > end_dt:
				return "%(start_dt)s can't be after %(end_dt)s!"
		if start_dt and start_dt > datetime.date.today():
			return "%(start_dt)s can't be after today!"
#		return False/ or None, or 

	myForm.validators += [datesbad]
		
		
	if myForm.redisplay_me(request): #can be not valid because first GET, or invalid data on POST.
		return make_response(myForm.render_me())
	else: #ok, fields are filled in, and are valid, and form is valid, do Magic()
			#can still include form if desired in rendered page, (e.g.at top)
#		return make_response(myForm.render_me())
		#return make_response("<body><h2>Success</h2></body>")
		
		template ="""
			~/Dashboard/invoke_report.py \
				{% if REQUESTOR %} --requestor {{REQUESTOR}}{% endif %} \
				{% if LIMIT %} --limit {{LIMIT}}{% endif %} \
				--format {{FORMAT}} \
				{% if AUDIENCE %} --audience {{AUDIENCE}} {% endif %} \
				-out {{OUT}} \
				{{REPORT}} \
				{% if PUBLISHER %} --publisher {{PUBLISHER}} {% endif %} \
				{% if START_DT %} --start {{START_DT }} {% endif %} \
				{% if END_DT %} --end {{END_DT }} {% endif %} \
				&
			"""
		commandline = Template(template).render(
			REQUESTOR=myForm['request_by']
			,LIMIT=myForm['limit']
			,FORMAT=myForm['format']
			,AUDIENCE=myForm['audience']
			,OUT=myForm['out']
			,REPORT=myForm['report']
			,PUBLISHER=myForm['publisher']
			,START_DT=myForm['start_dt']
			,END_DT=myForm['end_dt']
			)
		
		os.system(commandline)
		
		return make_response("<body><code>%s</code></body>"%commandline)		 
		



