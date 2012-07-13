#import report_query_framework

from jinja2 import Template
from sqlhelpers import *
import datetime
import utils
import time
import argparse
import re


from forms_and_fields import *

class FixtureHelper():
#	FIXTURE_SCHEME = MONGO | S3 | LOCAL
#	def list_fixtures(
#	def save_as_fixture(
#		store_as_mongo_fixtures(
#	def load_from_fixture(
	pass		




class BaseQueryDef(object):
	#QueryDef defines a query, and a set of available qualifiers
	# a ReportDef will be tied to a specific QueryDef that can feed it.
	# 
	# the QueryDef class is the definition... a QueryDef object has the query params filled in 
	# 
	#	might want QueryDef <- Fixture, so that either one can be a datasource

	dataset = {}
	sql = ''
	DB = DB_PBT
	DB_name = 'DB_PBT'
	
	limit = None

	def qualify(self):
		self.sql = self.eval_query(self.SQL_template, 
			**{(q_obj.sql_name or q_name.upper()) : q_obj.value_raw 
				for q_name,q_obj in self.qualifiers.items()}
			)

	@property
	def SQL_template(self):
		return ""

	def eval_query(self, template, **qualifiers):
		# passed in the SQL_template, and a set of key=value for the qualifiers, in the form (PUBLISHER='tippr',...).
		# must return a usable sql query string.
		# this function may be overridden to do more sophisticated conditional logic to generate the SQL.

		return Template(template).render(LIMIT=self.limit,
			**qualifiers
			)		
		

	
	def debug_qualifiers(self):
		out = """ 
		Qualifiers: 
        		{%- for k,v in query_qualifiers.iteritems() %} 
                		{{k}}: \t{{ v.value_raw | string }} \t{{ v.value_raw|pprint(verbose=True) }} 
        		{%- endfor %} 
		"""
		 
                return Template(out).render(query_qualifiers=self.qualifiers)  

	def load_dataset(self):
		timestart = time.time()
		cols, resultset = throw_sql(self.sql, self.DB) #DB_PBT)

		ROWS = [dict(zip(cols,row)) for row in resultset]
		COLS = cols
		#	return render_template("debugging.html", SQL=sql);
		secselapsed = time.time()-timestart
		META = {
			'pulled_at'		: datetime.datetime.now()
			,'row_count'		: len(ROWS)
			,'query_response_secs'	: int(secselapsed)
			,'db'			: self.DB_name
			,'sql'			: self.sql
#			,'qualifiers'		: self.qualifiers
		}

		self.dataset = dict(ROWS=ROWS, COLS=COLS, qualifiers=self.qualifiers)
		self.dataset.update(META) #add in our META key-values
		return self.dataset

	def command_line(self): #initially written to build the arg-parser -- not used anymore.
		import argparse
		parser = argparser.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
		for qname, q in self.qualifiers.iteritems():
			z = {'dest':qname}
			for x,y in {'action':'action','choices':'pick', 'help':'help', 'default':'default',
					'metavar':'metavar', 'type':'type'}.iteritems():
				if y in q:
					z[x]=q[y]
			parser.add_argument(*q['args'],**z)
		arguments = parser.parse_args(sys.argv[1:])

	def subparsers_setup(self, parser):
		subparser_mount = parser.add_subparsers(title='Available Reports',description='Long-running Reports that have been defined in the Reporting System',help='use @@@ --help to get detail for a specific report.')	
		return subparser_mount

	def subparser_add(self, subparser_mount):
# see http://docs.python.org/library/argparse.html
		sp = subparser_mount.add_parser(
			self.base_query 
			,description='%s v.%s -- %s'%(self.base_query, self.version, self.descript) 
			,help=self.__doc__ or ""
                	,epilog="---c.2012 tippr.com---\n")
			#aliases=[]
		sp.add_argument('--version', action='version', help='show the version# of the query', version='%s v.%s'%(self.base_query, self.version))
		for (qname, q) in self.qualifiers.iteritems():
			z = {'dest':qname}
			#w = self.type_context(q['metatype']) #load any type-specific defaults
			for (x,y) in {'action':'action','choices':'pick', 
					'help':'help', 'default':'default', 
					'metavar':'metavar', 'type':'coerce', 
					'nargs':'nargs'}.iteritems():
				if hasattr(q,y): #overwrite with any overwrites
					z[x]=getattr(q,y)
#			print z
			sp.add_argument(*q.args,**z)
		sp.set_defaults(func=self)

	def parser_pull_qualifiers(self, ns_args):
		"""
		Makes a qualifier-set (useful for filling in the values for my qualifiers) 
		from the command-line argument list (parsed).
		"""
#		return dict([(k, getattr(ns_args,k)) for k in self.qualifiers.keys()])
		for k,q in self.qualifiers.iteritems():
			q.value_raw = getattr(ns_args,k)	
	
	def post_pull_qualifiers(self, args): #call with request.values
	# nb. use getlist(q, default)  for multis, get(q, default)
		#TOBE TESTED
		params = {}
		for key,qualifier in self.qualifiers.iteritems():
			param = (args.getlist 
				if getattr(qualifier,'multi_post',False) 
				else args.get)(key,
					getattr(qualifier,'default', None))		
			if param: #TODO: handle list of values to convert
				param = (getattr(qualifier,'ui_coerce', str) or str)(param)
			qualifier.value_raw = param
		return params

	def to_fieldlist(self):	 
		return [q.to_field(qname) for qname,q in self.qualifiers.iteritems()]

	def from_form(self, form):
		for qname,q in self.qualifiers.iteritems():
			q.set(form[qname])

	def as_webform(self, FormClass):
		return FormClass(self.to_fieldlist())

#TODO in future: make some mixin classes that can be used to make something be declarative.
#class DeclarativeItem(object): #Idea: an abstract class to use as mixin to make something a DeclarativeItem
#	creation_counter = 0
#	def __new__(self):
#		self.creation_counter = DeclarativeItem.creation_counter
#		DeclarativeItem.creation_counter += 1


#TODO: move this into a class to map types into different handling, perhaps the widget mapping too
class BaseQualifier(object):
	creation_counter = 0

	def __init__(self, attribs={}):
		# To keep the qualifiers in order, in case it matters (e.g. if we build a form from them)
		# we use a django trick.  see django/forms/fields.py

		self.creation_counter = BaseQualifier.creation_counter
		BaseQualifier.creation_counter += 1

		self.value_raw		= None
		self.value_cleaned	= None
		self.errors		= []
		self.sql_name		= None		#if NOT supplied, the SQL_name will default to the ucase(name)
		self.args		= None		# command-line args, e.g. -p|--publisher <publisher> 
		self.required		= False	
		self.ui_widget 		= BaseField 	#BaseWidget	# web ui-widget, use classes of BaseWidget.  e.g. DateWidget
		self.coerce 		= None 		# lambda converter to coerce input X into right datatype, error if fail
		self.ui_coerce		= None		# lambda converter to coerce web input X into right datatype
	#	self.validate		= None		# lambda to resolve to T|F, if valid.  Else will error out.
		self.metavar 		= ""		# word to show in place of input in help.  Eg. where matches <publisher> 
		self.allow_multi 	= False		# expect multiple values (form into a list) 
		self.multi_post		= False		# result comes in as multiple q-params.
								#NB>lists & other things have multi part,
								#resove to a list, and might have multi --email=x, --email=y
								#BUT WILL NOT have multi fields in UI! so single q-param.
		self.default 		= None		# @@@@!!!!!
		self.extra_opt_opts	= None		# for 'action', 'nargs', special args to the opt-parser	
	#	self.action 		= 	
	#	self.nargs 		= 	
		self.help		= ""

		self.dict_2_attr( attribs)
		return self

	def dict_2_attr(self, attribs={}):
		for k,v in attribs.items():
			setattr(self,k,v)
	
	def to_field(self,qname):
		try:
			q = self
			F = q.ui_widget #Note: is instance of BaseField (see forms_and_fields.py)
			args = { 'label'	: getattr(q,'label',None)
				,'default'	: getattr(q,'default',None)
				,'hidden'	: getattr(q,'hidden',False)
				,'disabled'	: getattr(q,'disabled',False)
				,'required'	: getattr(q,'required', False)
				,'dtype'	: getattr(q,'ui_coerce', None)
				,'help'		: getattr(q,'help', None)
				,}
	
#			args['label'] = ( q.label if hasattr(q,'label') else qname.replace('_',' ').capitalize())+""
#			args['value'] = getattr(q,'default', '')
			if hasattr(q,'pick') and q.pick: args['options']= zip(q.pick, q.pick)
			if hasattr(q,'pickkv') and q.pickkv: args['options']= q.pickkv

			print 'name = %s'%qname
			field = (F)(qname,**args)
			print field.__dict__
			return field
		except:
			return None

	def set(self, value): #Note: takes in a form field (instance of BaseField see forms_and_fields.py),
					# and loads me up with it's cleaned value
		self.value_raw = value
		return value
		
def get_declared_qualifiers(bases, attrs):
	qualifiers = [(qual_name, attrs.pop(qual_name)) for qual_name, obj in attrs.items() if isinstance(obj,BaseQualifier)] 
	qualifiers.sort(key=lambda x: x[1].creation_counter)

	for base in bases[::-1]:
		if hasattr(base, 'qualifiers'):
			qualifiers = base.qualifiers.items() + qualifiers

	return SortedDict(qualifiers)	

class DeclarativeQualifiersMeta(type):
	def __new__(cls, name, bases, attrs):
		attrs['qualifiers'] = get_declared_qualifiers(bases, attrs)
		new_class = super(DeclarativeQualifiersMeta, cls).__new__(cls, name, bases, attrs)
		return new_class

class QueryDef(BaseQueryDef):
	""" 
	Set up the declarative syntax for expressing Qualifiers
	"""
	__metaclass__ = DeclarativeQualifiersMeta

		
class RepDef(object):
		#RepDef is a report definition, the name, the layout, who can access it, what query it needs, 

	class Action_add_and_flatten(argparse.Action):
		def __call__(self, parser, namespace, values, option_string=None):
			cur_values = getattr(namespace, self.dest) or []
			cur_values.extend(values)
			setattr(namespace, self.dest, cur_values) 
	def subparser_add(self, subparser_mount):
		sp = subparser_mount.add_parser(
			self.slug
			,description='%s v.%s -- %s'%(self.name, self.version, self.descript) 
			,help=self.__doc__.strip() or None
                	,epilog="---c.2012 tippr.com---\n")
			#aliases=[]
		sp.add_argument('--version', action='version', help='show the version# of the report', version='%s v.%s'%(self.slug, self.version))
		query = self.require_query()
		for (qname, q) in query.qualifiers.iteritems():
			z = {'dest':qname}
			for (x,y) in {'action':'action','choices':'pick', 
					'help':'help', 'default':'default', 
					'metavar':'metavar', 'type':'coerce', 
					'nargs':'nargs', 'const':'const'}.iteritems():
				if hasattr(q,y):
					if getattr(q,y):
						z[x]=getattr(q,y)
			if getattr(q,'allow_multi',False):
				z['nargs']='+'
#				z['action']='append'
				z['action']=self.Action_add_and_flatten
#'append'

#			print z
			def debug_arg(*args,**kwargs):
				print self.slug+" sp.add_argument("+','.join(args)+','+ \
					','.join(["%s='%s'"%(k,v) for k,v in kwargs.iteritems()])+ \
					" )"
		#	if DEBUG: debug_arg(*q.args,**z)
			sp.add_argument(*q.args,**z)
		sp.set_defaults(func=self)


			
class BooleanQualifier(BaseQualifier):
# tried unsuccessfully to not use action=store_true, but instead use coerce=bool, but just couldn't get it to work.
	def __init__(self, attribs={}):
		super(BooleanQualifier, self).__init__()
		self.ui_widget 	= CheckboxField	#t if checked else f
				# 'input'	#validate T:yes,Y,T,true
		#self.coerce		= bool 
		self.ui_coerce		= bool 
		self.default		= False
		#self.action		= 'store_const'
		self.action 		= 'store_true'
		#self.nargs		= 0
		#self.const		= True

		self.dict_2_attr( attribs)

class IntQualifier(BaseQualifier):
# tried unsuccessfully to not use action=store_true, but instead use coerce=bool, but just couldn't get it to work.
	def __init__(self, attribs={}):
		super(IntQualifier, self).__init__()
		self.ui_widget 		= InputField
		self.coerce		= int
		self.ui_coerce		= self.coerce 
		self.default		= 0

		self.dict_2_attr( attribs)

class DateQualifier(BaseQualifier):
	def date_mask(self,x):
		if re.match(r'^\d\d?/\d\d?$',x):
			return x+'/%s'%datetime.datetime.today().year, '%m/%d/%Y'		#problem: it won't assume the current year!!!
		if re.match(r'^\d\d?/\d\d?/\d\d$',x):
			return x, '%m/%d/%y'
		if re.match(r'^\d\d?/\d\d?/\d\d\d\d$',x):
			return x, '%m/%d/%Y'
		if re.match(r'^\d\d\d\d-\d\d?-\d\d?$',x):
			return x, '%Y-%m-%d'
		return None

	def __init__(self, attribs={}):
		super(DateQualifier, self).__init__()
		self.ui_widget 		= DateField #input for now, popup calendar in future
		self.coerce 		=lambda x: datetime.datetime.strptime(*self.date_mask(x))
#m?m[-/]d?d[-/]((yy)?yy)?
		self.ui_coerce		= self.coerce 
		self.metavar 		='<mm/dd/yy>'
		self.help 		= 'form of m?m/d?d/(yy)?yy or yyyy-m?m-d?d'
		self.default 		= ''

		self.dict_2_attr( attribs)


class ChoiceQualifier(BaseQualifier):
	def __init__(self, attribs={}):
		super(ChoiceQualifier, self).__init__()
		self.ui_widget		= DropChoiceField #'drop-down'
					# RadioChoiceField # 'radio-buttons'
		self.metavar		='<name>'
		self.pick		= None #[]
		self.pickkv 		= None	
		self.help 		= 'choose one of the possible options'

		self.dict_2_attr( attribs)

class MultiChoiceQualifier(ChoiceQualifier):
	def __init__(self, attribs={}):
		super(MultiChoiceQualifier, self).__init__()
		self.ui_widget		= MultiCheckField #'check-boxes'
					# MultiSelectField# 'multi-select'
		self.allow_multi	= True
		self.multi_post		= True
		self.default		= None
		self.help 		= 'may select multiple values'

		self.dict_2_attr( attribs)

class ListQualifier(ChoiceQualifier):
	def __init__(self, attribs={}):
		super(ListQualifier, self).__init__()
		self.ui_widget		= InputField #'input'
#		self.coerce 		= lambda x: [y.strip() for y in x.split(',')]
#tried to get it to seperate by comma, but it was too hard to flatten the list
#		self.reduce		= #must flatten the list of lists!!
		self.ui_coerce		= lambda x: [y.strip() for y in re.split(r',',x)]
#x.split(' ')] 
#tried to get it to split by space or comma, but it was too hard. currently ',' in web.
		self.allow_multi	= True
		self.default		= ""
		self.help 		= 'list seperated by space, or in shell --x=a b c --x=d => [a,b,c,d]'

		self.dict_2_attr( attribs)

#*********Special Cases: Month pickers  **********************************************

class MonthEntryQualifier(DateQualifier):
	def date_mask(self,x):
		if re.match(r'^\d\d?//\d\d$',x):
			return '%m//%y'
		if re.match(r'^\d\d?//\d\d\d\d$',x):
			return '%m//%Y'
		if re.match(r'^\d\d\d\d-\d\d?$',x):
			return '%Y-%m'
		return None

	def __init__(self, attribs={}):
		super(MonthEntryQualifier, self).__init__()
		self.ui_widget 		= DateField #input for now, popup calendar in future
		self.coerce 		=lambda x: datetime.datetime.strptime(x, self.date_mask(x))
						#m?m[-/]d?d[-/]((yy)?yy)?
		self.ui_coerce		= self.coerce 
		self.metavar 		='<mm//yy>'
		self.help 		= 'form of m?m//(yy)?yy or yyyy-m?m'
		self.default 		= ''

		self.dict_2_attr( attribs)

class MonthPickQualifier(ChoiceQualifier):
	def list_the_months(self,months_back=5 ):
		pick_month = []
		today = datetime.date.today()
		target = today 
		while months_back:
			monthkey = target.strftime('%Y-%m')
			monthvalue = target.strftime('%B %Y') 
			if target == today:
				monthvalue += ' -- MTD'
			months_back -= 1
			if target.month == 1:
				target = target.replace(year=target.year-1,month=12)
			else:
				target = target.replace(month=target.month-1)
			pick_month.insert(0,(monthkey,monthvalue))
		return pick_month
	
	def __init__(self, attribs={}, months_back=10):
		super(MonthPickQualifier, self).__init__()
		self.pickkv 		= self.list_the_months(months_back=months_back)
		self.help 		= "choose a month"
		self.default 		= datetime.date.today().strftime('%Y-%m')
		self.option_prefix 	= ""
		self.ui_coerce		= lambda x: datetime.datetime.strptime(x, '%Y-%m')

		self.dict_2_attr( attribs)

#TODO: create a base report that calculates the COLS

#TODO: create a test set of qualifiers, that will test out the optargs and the web-interface
#		with all kinds of fields, and then shows results, no report.

class Q_Test_Args(QueryDef):
	"""
	A test for testing Qualifiers of all types:
	"""
	version = 1.0
	base_query = 'test-args'
	descript = 'A test query to test arguments'

		##TODO: CAN also use required:True
	publisher= ChoiceQualifier({
				'args'		: ('-P','--publisher')
				,'help'		:'Pick a Publisher to isolate to'
		#		,'metavar'	:'publisher'
		#		,'pick'		: ['225besteats', 'yollar', 'tippr', 'msn']
				,'pickkv'	: sql_pull_lookup('select name, title from core_publisher order by title;',DB_PBT)
				})	#('ALL':None, string,required) 
	start_dt= DateQualifier({
				'args'		:('-S','--start')
				,'help'		:'Include transaction after (or on) this starting date; format is mm/dd/yy'
				,'required'	:True
				})	
	credits_only= BooleanQualifier({ #true or false
				'args'		:('-C', '--credits-only')
				,'help'		:'Show only Credits'
				})	#(bool,False) 
#ideas:
#		age= NumberQualifier({ #!!!allow validation, but free-form entry
#				'args'		:('-A','--age')
#				,'help'		:'show things older than this'
#				,'required'	:True
#				}).add_validation(NON_NEG, NON_ZERO, IN_RANGE(2,100))
#		zip-code= InputQualifier({ #!!!allow validation, but free-form entry
#				'args'		:('-A','--age')
#				,'help'		:'show things older than this'
#				,'required'	:True
#				}).add_validation(NUMONLY, RE_MASK('\d{5}(-\d{3})?'))
#		phone= InputQualifier({ #!!!allow validation, but free-form entry
#				'args'		:('-A','--age')
#				,'help'		:'show things older than this'
#				,'required'	:True
#				}).add_validation(NUMONLY, RE_MASK('(1?\((\d\d\d)\))?(\d\d\d)[-\.](\d\d\d\d)', '1-($0)$2-$3')
	
	disabled= IntQualifier({ #!!!allow validation, but free-form entry
				'args'		:('-D','--disabled')
				,'help'		:'show things older than this'
				,'disabled'	:True
				})	
	hidden= IntQualifier({ #!!!allow validation, but free-form entry
				'args'		:('-H','--hidden')
				,'help'		:'show things older than this'
				,'hidden'	:True
				})	
	email_addresses= ListQualifier({ #allow entry of multiple free-form entries, 
							#can be --to jelliott tpearl
							# or --to jelliott --to tpearl 
				'args'		:('-E', '--email')
				,'help'		:'Email to these guys.  Provide list'
				})	#(bool,False) 
	radio_suits= ChoiceQualifier({ #select multiple choices 
				'args'		:( '--suits',)
				,'ui_widget'	:RadioChoiceField  #special-use widget
				,'required'	:True
				,'help'		:'choose your favorite suits.'
				,'pick'		:['hearts','spades','diamonds','clubs']
				})	#(bool,False) 
	multi_suits= MultiChoiceQualifier({ #select multiple choices 
				'args'		:( '--cbsuits',)
		#		,'ui_widget'	:'check-boxes'
				,'help'		:'choose your favorite suits.'
				,'pick'		:['hearts','spades','diamonds','clubs']
				})	#(bool,False) 

class Q_Test_Args2(QueryDef):
	"""
	A test for testing Qualifiers of all types:
	"""
	version = 1.0
	base_query = 'test-args'
	descript = 'A test query to test arguments'

	publisher= ChoiceQualifier({
				'args'		: ('-P','--publisher')
				,'help'		:'Pick an active Publisher to isolate to'
		#		,'metavar'	:'publisher'
				,'pick'		: ['225besteats', 'yollar', 'tippr', 'msn']
				,'pickkv'	: sql_pull_lookup("select name, title from core_publisher where status='active' order by title;",DB_PBT)
				,'required'	: True
				})	#('ALL':None, string,required) 
	month_dt= MonthEntryQualifier({
				'args'		:('-M','--month')
				,'help'		:'Include transaction in this month only; format is mm//yy'
				,'required'	:True
				})	
	month_dt2= MonthPickQualifier({
				'args'		:('-M','--month')
				,'help'		:'Pick from List'
				,'required'	:True
				})	
	credits_only= BooleanQualifier({ #true or false
				'args'		:('-C', '--credits-only')
				,'help'		:'Show only Credits'
				})	#(bool,False) 
#ideas:
#		,age= NumberQualifier({ #!!!allow validation, but free-form entry
#				'args'		:('-A','--age')
#				,'help'		:'show things older than this'
#				,'required'	:True
#				}).add_validation(NON_NEG, NON_ZERO, IN_RANGE(2,100))
#		,zip-code= InputQualifier({ #!!!allow validation, but free-form entry
#				'args'		:('-A','--age')
#				,'help'		:'show things older than this'
#				,'required'	:True
#				}).add_validation(NUMONLY, RE_MASK('\d{5}(-\d{3})?'))
#		,phone= InputQualifier({ #!!!allow validation, but free-form entry
#				'args'		:('-A','--age')
#				,'help'		:'show things older than this'
#				,'required'	:True
#				}).add_validation(NUMONLY, RE_MASK('(1?\((\d\d\d)\))?(\d\d\d)[-\.](\d\d\d\d)', '1-($0)$2-$3')
	
	disabled= IntQualifier({ #!!!allow validation, but free-form entry
				'args'		:('-D','--disabled')
				,'help'		:'show things older than this'
				,'disabled'	:True
				})	
	hidden= IntQualifier({ #!!!allow validation, but free-form entry
				'args'		:('-H','--hidden')
				,'help'		:'show things older than this'
				,'hidden'	:True
				})	
	email_addresses= ListQualifier({ #allow entry of multiple free-form entries, 
							#can be --to jelliott tpearl
							# or --to jelliott --to tpearl 
				'args'		:('-E', '--email')
				,'help'		:'Email to these guys.  Provide list'
				})	#(bool,False) 
	radio_suits= ChoiceQualifier({ #select multiple choices 
				'args'		:( '--suits',)
				,'ui_widget'	:RadioChoiceField  #special-use widget
				,'required'	:True
				,'help'		:'choose your favorite suits.'
				,'pick'		:['hearts','spades','diamonds','clubs']
				})	#(bool,False) 
	multi_suits= MultiChoiceQualifier({ #select multiple choices 
				'args'		:( '--cbsuits',)
		#		,'ui_widget'	:'check-boxes'
				,'help'		:'choose your favorite suits.'
				,'pick'		:['hearts','spades','diamonds','clubs']
				})	#(bool,False) 
		

class R_Test_Args(RepDef):
	"""
		dummy to test Q_Test_Args
	"""
	require_query = Q_Test_Args
	name ='TEST ARG REPORT'
	version = 0.5
	slug= 'test-args'
	descript = "Test Arg Report"
	title= 'Test Arg Report'
	subtitle = ''
	lpp   = None

	custom_template = None






class Q_Test_Query(QueryDef):
	"""
	A Simple Test Query to use to test features,
	no qualifiers, but will run a simple quick report
	"""
	version = 1.0
	base_query='test-all-pubs'
	descript = 'A test report to show all pubs quickly'

	@property
	def SQL_template(self):
		"""
		Get detailed closed transactions (for this pubisher, period TODO).
		Maybe credits only.

		"""
		build_sql = " select name, title, country from core_publisher where status = 'active' LIMIT {{LIMIT}};"
		return build_sql

class R_Test_Report(RepDef):
		"""
		Test Report
"""
		require_query = Q_Test_Query
		name ='TEST REPORT'
		version = 0.5
		slug= 'test-rep'
		descript = "Test Report"
		title= 'Test Report'
		subtitle = ''
		lpp   = None

		custom_template = None

#       SUBTITLE = q_filter_pretty

        #COLS defines the COLS to output, and the details are used for various conversions, need not include all RS columns
        ##NOTE: the field_name matches the column name in the result set, without any table qualifier:
        ##       e.g. select a.x , b.x from tbl a, tbl2 b; will return two columns named x!!

		COLS_OUT = [#k:field_name           l:title(\n)             u:formatting   t!new: google-typ     w:width  	!!added x:example_text!! instead of w
		 {'k':'country' 	,'l':'country'        ,'u': None     ,'t':None	,'w':'104px' 	,'x': '225besteats'}
               	,{'k':'name' 	,'l':'name'    ,'u': None   ,'t':None	,'w':'139px'	,'x': '01/01/2012'}
               	,{'k':'title' 	,'l':'title'     	,'u': None     ,'t':None       	,'w':'133px'	,'x': 'Health & Medicine'}
		]
		META = {#TODO: META data should ALWAYS be attached to the run-report!! to have an audit-trail of what generated this report.
                        # for JSON, we could have a META-block
                        # for csv file, we could have a seperate *.meta file
                        # for web-pages, there could be mouse-over or special pop-up modal
                        # for printed it should always say above the footer 
                'report': name,
                'rpt_v' : version,
                'slug'  : slug,
                'title' : title,
                'subtitle': '',
                'lpp'   : None,
                'base_query': require_query.base_query,
                        #{'publisher':publisher, 'start_dt':start_dt, 'end_dt':end_dt, 'credits_only':credits_only}, 
                # ideas: incl_titles, best_width, best_height, is_use_color?, is_html_interactive? 
                # new idea: checksums (that we can't put in the csv), e.g. #rows, sum(<field>), MD5
                # other idea: profiling: it took x long for x rows, started at, finished at, against server X
		}		

