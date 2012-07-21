#! /usr/bin/python

#import run_rpt_fromdef
import txn_detail_def #incl: txn-credits, and msn-txn
import report_query_framework as f

import datetime
import sys
import traceback
import utils
from jinja2 import Template

formatter_jumptable = {
	'json': utils.data_to_json
	, 'csv': utils.data_to_csv
	, 'html-table': utils.data_to_htmltable
	, 'text-table': utils.data_to_texttable}
formatter_default = 'text-table'

FORMATS_AVAIL = formatter_jumptable.keys()      
FORMATS_DEFAULT = formatter_default


#QUERIES = [txn_detail_def.Q_Txn_Detail(), txn_detail_def.Q_MSN_Detail(), txn_detail_def.Q_TXNPayment_Detail()]
REPORTS = [f.R_Test_Args(), f.R_Test_Report(), txn_detail_def.R_Txn_Detail(), txn_detail_def.R_MSN_Detail(), txn_detail_def.R_TXNPayment_Detail()]
PROG = sys.argv[0]
DEBUG = False #True

def init_parser(PROG, QUERIES): #uses QUERIES & PROG
    	import argparse
	# load late to avoid version conflict
    	parser = argparse.ArgumentParser(
			formatter_class=argparse.ArgumentDefaultsHelpFormatter
			, prog=PROG
			, description="A command-line tester for running reports."
			, epilog="---c.2012 tippr.com---\n\n"
			, usage='%(prog)s [options] <report-name> [report-options]')

	def parser_add_arg(*args, **kwargs):
		if DEBUG:
			print " BASE sp.add_argument("+','.join(args)+','+ \
				','.join(["%s='%s'"%(k,v) for k,v in kwargs.iteritems()])+ \
				" )"
		parser.add_argument(*args, **kwargs)

#	parser.add_argument('report', default=None, help='Report to run')
	#add_argument('-l','--list', help='List available Reports')
	parser_add_arg('--debug', dest='DEBUG', action='store_true', default=False, help='Turn on Debugging info')

	parser_add_arg('--requestor', dest='requestor', help='Required for restricted reports, provide your email address')

	parser_add_arg('--sql-only', dest='sqlonly', action='store_true', default=False, help='Generate the sql only')

	parser_add_arg('--limit', dest='limit', default=100, type=int,  help='Limit the query to ## rows only -- NOTE:defaults always to 100!! so clear it in production!')

	sub_mountpoint=parser.add_subparsers(
		title='Available Reports', 
		description='Long-running Reports that are defined in the Reporting System.  \nUse %s <report-name> --help, for help on a specific report'%PROG, 
#		help='use "%s <query-name> --help" to get help on a specific query'%PROG,) 
		help='report-specific qualifiers can include e.g.: start-dt=YYYYMMDD, end-dt=YYYYMMDD, publisher=MSN',) 
	for r in REPORTS:
		r.subparser_add(sub_mountpoint)
	#for q in QUERIES:
	#	q.subparser_add(sub_mountpoint)

	parser_add_arg('-f','--format', dest='format', default=FORMATS_DEFAULT,
		choices=(FORMATS_AVAIL), help='Pick the layout format. If no format will be in raw.')

	
#Notification:
	#TODO: below: make handle comma-sep list:
	parser_add_arg('-to', '--audience', nargs='+', dest='audience', default=[], metavar='email-list',
		help='Set of people allowed access to this report.  Used as email-list for email delivery (-o option).  Currently _only_ used to email the results; but _future_ will restrict access.')
	parser_add_arg('-n','--notify', nargs='+', dest='notify', default=[], metavar='email-list',
		help='Send an email notification (but no report) to this email addr/list, after the report runs.  Seperate multiple emails by a space.  ')
#	parser_add_arg('-cs','--custom', dest='subject', default=None,
#		help='Custom email subject line')

	parser_add_arg('-out', '--output-to', dest='storage',default='STDOUT', 
		choices=('S3','LOCAL','STDOUT','EMAIL-ATTACH','EMAIL-EMBED'),
		help='Pick the output sink. ')

	return parser

def parse_commandline_args(parser, argv):
	args_obj = parser.parse_args(argv[1:])
	if DEBUG:	print args_obj
	return args_obj

def build_qualified_query(report_obj, args_obj):
	print "you have picked: %s"% report_obj.name

	query_obj = report_obj.require_query()

	query_obj.parser_pull_qualifiers(args_obj)

	if args_obj.limit:
		query_obj.limit = getattr(args_obj,'limit')

	query_obj.qualify()

	return query_obj


def build_meta(args, report, query):
	
	META = {#TODO: META data should ALWAYS be attached to the run-report!! to have an audit-trail of what generated this report.
			# for JSON, we could have a META-block
			# for csv file, we could have a seperate *.meta file
			# for web-pages, there could be mouse-over or special pop-up modal
			# for printed it should always say above the footer 
		'requestor'	: args.requestor,
		'user'		: args.requestor,
		'requested_at'	: datetime.datetime.now(),
		'request_format': args.format,
		'request_flags'	: args.storage,

		'run_at' 	: datetime.datetime.now(),
		'report'	: report.name,
		'rpt_v'		: report.version,
		'slug'		: report.slug,
		'title'		: report.title,
		'subtitle'	: report.subtitle,
		'lpp'		: None,
		'base_query'	: query.base_query,
		'qry_v'		: query.version,
		'dataset_pulled_at': query.dataset['pulled_at'],
		'dataset_row_count': query.dataset['row_count'],
		'dataset_pull_time': query.dataset['query_response_secs'],
		'dataset_db'	: query.DB,
		'query_qualifiers': query.qualifiers,
			#{'publisher':publisher, 'start_dt':start_dt, 'end_dt':end_dt, 'credits_only':credits_only}, 
		# ideas: incl_titles, best_width, best_height, is_use_color?, is_html_interactive? 
		# new idea: checksums (that we can't put in the csv), e.g. #rows, sum(<field>), MD5
		# other idea: profiling: it took x long for x rows, started at, finished at, against server X
		}
	return META
	
def main():
	""" 
	A command-line REPORT runner, that uses the optargs library, 
	especially the cut-out passthrough from the query-def to define the qualifiers
	"""
	#QUERIES=[x.require_query() for x in REPORTS]
	parser = init_parser(PROG, REPORTS)
	args_obj = parse_commandline_args(parser, sys.argv)

	report_obj = args_obj.func
									#Build Query:		
	query_obj = build_qualified_query(report_obj, args_obj); 
	#at this point the query_obj is fully qualified successfully, and ready for throwing at the db.

	if DEBUG: print query_obj.debug_qualifiers()
#	return 

	#args = vars(args_obj)
	if args_obj.sqlonly:
		print query_obj.sql
		return 								####
	 									#Load DataSet:
	result_set = query_obj.load_dataset()	
	#print result_set
	#print arguments
										####
	META = build_meta(args_obj, report_obj, query_obj) 			#Render Report:
	addr_from='reporting@tippr.com'
	subject_prefix = '[TipprReportServer] '

	try:
		formatter = formatter_jumptable[args_obj.format]
		DOC_OUT, MIME_TYPE, CON_TYPE = (formatter)(result_set["ROWS"], report_obj.COLS_OUT, CONTEXT=META)

										####		
										#Store it:
		if not args_obj.storage == 'STDOUT':
			file_locator = None
			file_name = utils.unique_filename(format=args_obj.format, report=report_obj.slug, by=args_obj.requestor)
			if args_obj.storage =='S3':
				file_locator = utils.store_doc_to_s3(DOC_OUT, file_name, 
					headers = {'Content-Type':CON_TYPE})
	#can't get it to work yet: 
	#			file_locator = utils.url_to_tiny(file_locator)
			if args_obj.storage =='LOCAL':
				file_locator = utils.store_doc_to_local(DOC_OUT, file_name)
			META['file_locator'] = file_locator
										####
										#Send it out to audience:
			if args_obj.audience: #TODO: add in requestor in here or in notify.
				deliver_to = args_obj.audience
				if args_obj.storage=='EMAIL-ATTACH':
					subject = 'Here is your Report'
					body = Template(email_body_template('attach')).render(DOC_OUT=DOC_OUT, **META)
					utils.email_senddoc(addr_from=addr_from, addr_to=deliver_to, 
						subject=subject_prefix+subject, 
						body=body, 
						ctype=CON_TYPE, doc=DOC_OUT, fname=file_name)
				else:
					if args_obj.storage=='EMAIL-EMBED':
						subject = 'Here is your Report'
						body = Template(email_body_template('embed')).render(DOC_OUT=DOC_OUT, **META)
					elif file_locator: 
						#No point in sending if we can't send it (ATTACH, EMBED)
						# or send a link to it
						subject = 'Your Report is ready to be viewed'
						body = Template(email_body_template('link')).render(DOC_OUT=DOC_OUT, **META)
					utils.email_simple(addr_from=addr_from, addr_to=deliver_to, 
						subject=subject_prefix+subject , body=body)
										####
										#Output Report-run info to STDOUT 
			print Template(email_body_template('link')).render(DOC_OUT=DOC_OUT, **META)
		else: #if STDOUT:
			print Template(email_body_template('embed')).render(DOC_OUT=DOC_OUT, **META)

										####
										#Notify interested parties:
		if (args_obj.requestor not in args_obj.audience): #if i'm not already sending the requestor the report, then send him/her the notification.			
			args_obj.notify = (args_obj.notify or []) + [args_obj.requestor,]	#Notify Requestor (+notify) of success:
		if args_obj.notify:  #TODO: add in requestor too.
			subject = 'Notification: Report has run'
			body = Template(email_body_template('notify')).render(DOC_OUT=DOC_OUT, **META)
			utils.email_simple(addr_from=addr_from, 
				addr_to=args_obj.notify, 
				subject=subject_prefix+subject,
				body= body)
	except:
		exc_info = sys.exc_info()
		error_text = """
ERROR: %s: %s
Traceback: 
%s
		"""%(exc_info[0],exc_info[1], traceback.format_exc()) 
		subject = 'ERROR in Report run'
		body = Template(email_body_template('embed')).render(DOC_OUT=error_text, **META)
		utils.email_simple(addr_from=addr_from,
			addr_to=[args_obj.requestor,],
			subject=subject_prefix+subject,
			body= body)
		print body							#Echo any errors locally to STDOUT


def email_body_template(selector):
	if selector == 'attach':
		body = '''
Report:         {{ report }} [version {{rpt_v}}]
Requested by:   {{ requestor }} on {{ requested_at }}
Request Details:out_format={{request_format}}, flags={{request_flags}}
Dataset: #TODO:/or Fixture 
        Query:  {{ base_query }} [version {{qry_v}}]
        Qualifiers:
		{%- for k,v in query_qualifiers.iteritems() %}                
		{{k}}: \t{{ v.value_raw | string }}
		{%- endfor %}
-------------
Dataset:
        Base Query: {{base_query }}
        pulled at {{dataset_pulled_at}} 
        {{dataset_row_count}} rows
	[timespent: {{dataset_pull_time}} secs]
Report Run:
        at {{ run_at }}
{% if file_locator %} Output URL: {{ file_locator }} {% endif %}

        Thank you, 
                Your Report Server
		'''	
	if selector == 'notify':
		body = '''
Report:         {{ report }} [version {{rpt_v}}]
Requested by:   {{ requestor }} on {{ requested_at }}
Request Details:out_format={{request_format}}, flags={{request_flags}}
Dataset: #TODO:/or Fixture 
        Query:  {{ base_query }} [version {{qry_v}}]
        Qualifiers:
		{%- for k,v in query_qualifiers.iteritems() %}                
		{{k}}: \t{{ v.value_raw | string }}
		{%- endfor %}

-------------
Dataset:
        Base Query: {{base_query }}
        pulled at {{dataset_pulled_at}} 
        {{dataset_row_count}} rows
	[timespent: {{dataset_pull_time}} secs]
Report Run:
        at {{ run_at }}
{% if file_locator %} Output URL: {{ file_locator }} {% endif %}

        Thank you, 
                Your Report Server

		'''
	if selector == 'embed':
		body = '''

---------
{{DOC_OUT}}
---------

Report:         {{ report }} [version {{rpt_v}}]
Requested by:   {{ requestor }} on {{ requested_at }}
Request Details:out_format={{request_format}}, flags={{request_flags}}
Dataset: #TODO:/or Fixture 
        Query:  {{ base_query }} [version {{qry_v}}]
        Qualifiers:
		{%- for k,v in query_qualifiers.iteritems() %}                
		{{k}}: \t{{ v.value_raw | string }}
		{%- endfor %}

-------------
Dataset:
        Base Query: {{base_query }}
        pulled at {{dataset_pulled_at}} 
        {{dataset_row_count}} rows
	[timespent: {{dataset_pull_time}} secs]
Report Run:
        at {{ run_at }}

        Thank you, 
                Your Report Server
		'''
	if selector == 'link':
		body = '''
Report:         {{ report }} [version {{rpt_v}}]
Requested by:   {{ requestor }} on {{ requested_at }}
Request Details:out_format={{request_format}}, flags={{request_flags}}
Dataset: #TODO:/or Fixture 
        Query:  {{ base_query }} [version {{qry_v}}]
        Qualifiers:
		{%- for k,v in query_qualifiers.iteritems() %}                
		{{k}}: \t{{ v.value_raw | string }}
		{%- endfor %}

-------------
Dataset:
        Base Query: {{base_query }}
        pulled at {{dataset_pulled_at}} 
        {{dataset_row_count}} rows
	[timespent: {{dataset_pull_time}} secs]
Report Run:
        at {{ run_at }}
{% if file_locator %} Output URL: {{ file_locator }} {% endif %}

        Thank you, 
                Your Report Server
		'''
	return body
if __name__ == '__main__':
    main()
		
# vim: ai et sts=4 sw=4 ts=4
