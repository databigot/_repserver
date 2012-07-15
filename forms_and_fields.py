from jinja2 import Template
from flask import flash,get_flashed_messages
from utils import SortedDict

class ValidationError(Exception):
	pass

class BaseField(object):
#TODO: handle HiddenFields, handle Input.size.
	"""
	"""
	creation_counter = 0

	def __init__(self, name, label=None, dtype=None, default='', options=None, option_prefix = None, help=None, required=False, disabled=False, hidden=False, size=None):
		# To order the fields in a Form, we use a django trick.  See django/forms/fields.py

		self.creation_counter = BaseField.creation_counter
		BaseField.creation_counter += 1

		assert name 
		self.name = name
		self.required = required		#True/False
		self.disabled = disabled		#True/False
		self.hidden	= hidden		#True/False
		self.label 	= label #or (name.replace('_',' ').capitalize())		
		self.dtype 	= dtype			#datatype: str, int, lamda x: convert(x)
		self.default	= default		#default 
		self.options	= options		#list of options in [k=v]
		self.option_prefix = option_prefix 	#--pick one-- 
		self.help	= help			#tooltip msg
		self.size 	= size
		self.value_raw = None			#the raw value inputted
		self.value_clean = None			#the validated, cleaned, converted value from input.  
						#the datatype of value_cleaned is the desired final datatype, e.g: may be an int, a list, a date, ...
		self.errors	= []
		self.validators = []
		if self.required:
			self.validators+=[
				lambda field,clean=None,raw=None: "Field %s is required!" if not raw else None]
	
		return self
#	def is_valid(self):
#		return True
	@property
	def my_label(self):
		return self.label or (self.name.replace('_',' ').capitalize())

	def clean_me(self):
		if self.value_raw and self.dtype:
			try:
				self.value_clean = (self.dtype)(self.value_raw)
				if not self.value_clean:
					raise TypeError
			except (TypeError,Exception):
				self.add_error('Field %s is invalid: invalid type') 			
				self.value_clean = None
		else:
			self.value_clean = self.value_raw

	def add_error(self, error):
		self.errors += [error % self.my_label]

	def self_exam(self):	
		self.errors = []
		self.clean_me()
		for v in self.validators:
			try:
				#error = v(**{self.name: self.value_raw})	#raises ValidationError(error_msg) if bad
				error = v(self, clean=self.value_clean, raw=self.value_raw)	#raises ValidationError(error_msg) if bad
				if error:
					raise ValidationError(error if isinstance(error, str) else None)		#or return False and I will do it.
			except ValidationError, e:
				self.add_error(e.message or "Field %s is Invalid!")
		return self.errors



	def _html_template(self):
		return ""
	def _html_wrapped(self):
		return """
				<div class='form-row {{field}}
					{%- if in_error %} error {%- endif -%}'>
					<div>
			""" + self._html_template() + """
				<p class='help'>{{help}}</p>
					</div>
				</div>
			"""
			
	def render_me(self, name, value):	#could be called with self.default, or self.value_raw, or...
		context = {'field'	:name
			,'value'	:value or ''	
			,'label'	:self.my_label 
			,'required'	:self.required
			,'disabled'	:self.disabled
			,'hidden'	:self.hidden
			,'size'		:self.size
			,'choices'	:self.options
			,'choice_prefix':self.option_prefix or ''
			,'help'		:self.help or ''
			}
		context['in_error'] = len(self.errors)
		return Template(self._html_wrapped()).render(**context)

	def set_to_default(self):
		self.value_raw = self.default

	def parse_field(self, args_in):
		if args_in.get(self.name):
			self.value_raw = args_in.get(self.name)
			return True
		return False

class Validator(object): #can be used for the Required, and maybe the form validation too?
	pass
#	define ValidationError
#	def __init__:
#		message or None
#		check_ok_f: return True is good, else 
#
#		def am_i_valid(field, value):
#			if not check_ok_f(**{field:value}):
#				raise ValidationError(message) 
#
#******
#Validator("Field %s is Required!", lambda field, value: field.required and not value)

g_flash_list = []
def flash(msg, cat):
	global g_flash_list
	g_flash_list += [(cat, msg)]
	print msg

def get_flashed_messages(with_categories=True):
	global g_flash_list
	tmp = g_flash_list
	g_flash_list = []
	return tmp
	
class ErrorFormInvalid(Exception):
	pass
class ErrorFormNew(Exception):
	pass
class BaseCoolForm(object):
#	global g_flash_list
#	g_flash_list = []

	def __init__(self, fieldlist=[], title='a Report', description=''):		#expecting named fields in kwargs, and in future validators
		self.title = title
		self.description = description
		self.errors = []				#not currently used
	#	self.fields = []				#ordered list of fields in this form
		self.validators = [] 				#lambdas/defs which take (some of) the form-fields
								# in as args, and return is-valid: True or False
		self.fields = self.base_fields[::1] #DEEPCOPY! Start with the fields defined or inherited by the class 
		for field in fieldlist:
			self.__add__(field)
#		for kw,value in kwargs.iteritems():
#			self.__add__(value)
		
	def addField(self, **kwargs):
		for kw,value in kwargs.iteritems():
			if isinstance(value,BaseField):
				return self._add_field(value)
	def _add_field(self, field):
		self.fields += [field]
		return self
	def __add__(self, thing):
		if isinstance(thing, BaseField): 
			return self._add_field(thing)
#		if isinstance(thing, Validator):
#			return self._add_validator(thing)

	def parse_form(self, args): 			#load incomming params into my fields in field.value_raw
		for field in self.fields:
			if not field.parse_field(args): #not found in incomming arguments, could be empty, could be disabled
				if field.disabled: field.set_to_default()
#			field.convert_me()

	def load_defaults(self):
		for field in self.fields:
			field.set_to_default()

	def redisplay_me(self, request):   #For Form handling, use this method which returns T/F, or process_form() which throws Exception if we need to redisplay
		if request.method == 'GET': 			#assume first time through
			self.load_defaults()			#load defaults into f.value_raw
			return True
		if request.method == 'POST': 			#assume submitted
			self.parse_form(request.values)		#load submitted values into f.value_raw
#			q.post_pull_qualifiers(request.form)
			return not self.am_i_ok()		#check validation, make errors
		return True	

	def process_me(self, request):	#For Form handling, either use this method, or the redisplay_me() above
		if request.method == 'GET':
			self.load_defaults()
			raise ErrorFormNew
		if request.method == 'POST':
			self.parse_form(request.values)
			if not self.am_i_ok():
				raise ErrorFormInvalid
		return True

	def am_i_ok(self):					#do a self_examination, generate errors 
		get_flashed_messages()				#clear any flash errors
		field_labels = self._field_labels()
		return (
			all(
				[self._field_ok(field, 
						lambda error: flash(error, 'error')) 	# true if not error
					for field in self.fields] +
				[self._validator_ok( f_invalid,
						lambda error: flash(error % field_labels, 'error'))
					for f_invalid in self.validators]
				)
			)
	def _field_ok(self,field, handle_error_f):
		errors=field.self_exam()
		if not errors: return True
		for error in errors:
			(handle_error_f)(error)
		return False
	def _field_labels(self):
		return {x.name:x.label for x in self.fields}
	def _field_values(self):
		return {x.name:x.value_clean for x in self.fields}

	def _validator_ok(self,f_invalid, handle_error_f):
		error = f_invalid(**self._field_values())
		if error:
			(handle_error_f)(error)
		else:
			return True
		return False
	
	def __getitem__(self, i):
		d = self._field_values()
		if i in d:
			return d[i]
		return None

	def render_me(self):
 		form = Template("""
		<style type='text/css'>
			.aligned {
				display: inline;
				float: none !important;
				padding-left: 4px;
			}
			.aligned label {
				display: block;
				float: left;
				padding: 3px 10px 0 0;
				width: 8em;
			}
			.required label, label.required {
				color: #333333 !important;
				font-weight: bold !important;
			}
		
			label {
				color: #666666;
				font-size: 12px;
				font-weight: normal !important;
			}
			.vCheckboxLabel {
				display: inline;
				float: none !important;
				padding-left: 4px;
			}
			form .aligned p.help {
				padding-left: 38px;
				padding-right: 10px;
				color: #999999;
				font-size: 10px !important;
				vertical-align: middle;
			}
			form .aligned p, form .aligned ul {
				margin-left: 7em;
			}
			form .form-row p {
				font-size: 11px;
			}
			.form-row {
				border-bottom: 1px solid #EEEEEE;
				font-size: 11px;
				overflow: hidden;
				padding: 8px 12px;
			}
			.form-row input {
				vertical-align: middle;
			}
			textarea, select, .vTextField {
				border: 1px solid #CCCCCC;
			}
			input, textarea, select, .form-row p {
				font-family: "Lucida Grande", "DejaVu Sans";
				font-size: 11px;
				font-weight: normal;
				margin: 2px 0;
				padding: 2px 3px;
			}
			body {
				color: #333333;
				font-family: "Lucida Grande", "DejaVu Sans";
				font-size: 12px;
			}
			.error label {
				color: red !important;
			}	
			.error input, 
			.error select,
			.error textarea {
				border: 1px solid red;
			}
			ul.messagelist {
				margin: 0;
				padding: 0 0 5px;
			}
				
			ul.messagelist li {
				background: url("../img/admin/icon_success.gif") no-repeat scroll 5px 0.3em #FFFFCC;
				border-bottom: 1px solid #DDDDDD;
				color: #666666;
				display: block;
				font-size: 12px;
				margin: 0 0 3px;
				padding: 4px 5px 4px 25px;
			}
			ul li {
				list-style-type: square;
				padding: 1px 0;
			}
			ul.messagelist li.error {
				background-image: url("/static/imgs/icon_error.gif")
			}
			ul.messagelist li.warning {
				background-image: url("/static/imgs/icon_alert.gif")
			}
			ul.messagelist li.success {
				background-image: url("/static/imgs/icon_success.gif")
			}
		</style>
		<div style='border: 1px solid black;width: 530; padding:0px;'>
		<div style='padding: 5px;'>
			<h1 style="text-align:center;">{{title}}</h1>
			<p>{{description}}</p>
		</div>
		<form action='{{ACTION}}' method='post'>
			<div class='header' style="width:auto;">
				{% if messages %}
					<ul class='messagelist'>
					{% for category, message in messages %}
						<li class='{{ category }}'>{{ message }} </li>
					{% endfor %}
					</ul>
				{% endif %}
			</div>
			<fieldset class='aligned'>

			""").render(ACTION='', title=self.title, description=self.description, 
				messages=get_flashed_messages(with_categories=True))
#               fieldlist = self.make_fieldlist()
		for field in self.fields:
			#print field.__dict__
			form += field.render_me(field.name,field.value_raw)                       
		form += """
                	<br><button type='submit' style='text-align:center;'>Submit</button>                                </fieldset>
		</form></div>                           """
        
		return form

def get_declared_fields(bases, attrs):
	# this mechanism, for managing fields, is taken from django/forms/forms.py
	fields = [(field_name, attrs.pop(field_name)) for field_name, obj in attrs.items() if isinstance(obj,BaseField)]
	fields.sort(key=lambda x: x[1].creation_counter)
	
	for base in bases[::-1]:
		if hasattr(base, 'base_fields'):
			fields = base.base_fields + fields

	return [x[1] for x in fields]	#ordered list
#	return SortedDict(fields)

def get_declared_validators(bases, attrs):
	validators = [attrs.pop(validator_name) for validator_name, obj in attrs.items() if isinstance(obj, Validator)]
	for base in bases[::-1]:
		if hasattr(base, 'validators'):
			validators = base.validators + validators
	return validators #as list

def deepcopy(iterx):
	return iterx[::1]

class DeclarativeFieldsMetaclass(type):
	"""
	Metaclass that converts Field attributes to a sorted dictionary
	"""
	def __new__(cls, name, bases, attrs):
		attrs['base_fields']= get_declared_fields(bases, attrs)
		attrs['validators'] = get_declared_validators(bases, attrs)
		new_class = super(DeclarativeFieldsMetaclass, cls).__new__(cls, name, bases, attrs)
		return new_class

class SuperCoolForm(BaseCoolForm):
	'a collection of fields, plus associated data.'
	# separate from BaseCoolForm to abstract the filed stuff
	__metaclass__ = DeclarativeFieldsMetaclass
#	def __init__(self, *pargs, **kwargs):
#		super(self.__class__, self).__init__(*pargs, **kwargs)
#		self.fields = deepcopy(self.base_fields)


#BaseField, CheckboxField, InputField, DateField, MultiCheckField, MultiSelectField, DropChoiceField, RadioChoiceField, 
class CheckboxField(BaseField):
	def __init__(self, name, label= None, default=False, dtype=bool,  help=None, **kwargs):
		 super(self.__class__, self).__init__(name,
			label=label, dtype=dtype, default=default, help=help, **kwargs)
	def _html_template(self):
		return """
						<label for='id_{{field}}' class='vCheckboxLabel
							{%- if required %} required {%- endif -%}
								'>
						<input id='id_{{field}}' name='{{field}}' type='checkbox' 
						{%- if disabled -%} disabled {%- endif -%}
						{% if value %} checked='checked'{% endif %} 
						>
							{{label}}
						</label>
			"""

class InputField(BaseField):
	def __init__(self, name, label=None , dtype=str , default='', help=None, **kwargs):
		 super(self.__class__,self).__init__(name,
			label=label, dtype=dtype, default=default, help=help, **kwargs)
	def _html_template(self):
		return """			<label for='id_{{field}}' class='
							{%- if required %} required {%- endif -%}
								'>
							{{label}} :
						</label>
						<input id='id_{{field}}' name='{{field}}' type='text' 
							value='{{value}}' 
							{%- if size -%} size='{{size}}' {%- endif -%}
							{%- if disabled -%} disabled {%- endif -%}
						>
			"""

class DateField(BaseField):
	def __init__(self, name, label=None, dtype=str, default='', help=None, **kwargs): 
		#TODO convert to datetime.datetime, now()
		 super(self.__class__,self).__init__(name,
			label=label, dtype=dtype, default=default, help=help, **kwargs)
	def _html_template(self):
		return """			<label for='id_{{field}}' class='
							{%- if required %} required {%- endif -%}
								'>
							{{label}} :
						</label>
						<input id='id_{{field}}' name='{{field}}' type='text' 
							value='{{value}}'
							{%- if size -%} size='{{size}}' {%- endif -%}
							{%- if disabled -%} disabled {%- endif -%}
							>
			"""

class DropChoiceField(BaseField):
	def __init__(self, name, label=None, dtype=str, default=None, options=[], option_prefix = '--pick one--', help=None,**kwargs):
		 super(self.__class__,self).__init__(name, 
			label=label, dtype=dtype, default=default, help=help, options=options, option_prefix=option_prefix, **kwargs)
	def _html_template(self):
		return """			<label for='id_{{field}}' class='
							{%- if required %} required {%- endif -%}
								'>
							{{label}} :
						</label>
						<select id='id_{{field}}' name='{{field}}'>
							<option value=''>{{choice_prefix}}</option>
							{%- for key,title in choices %}
								<option value='{{key}}' 
									{%- if disabled -%} disabled {%- endif -%}
									{%- if key==value %} selected {%endif%}
								>
								{{title}}</option>
							{%- endfor %}
						</select>
			"""

class RadioChoiceField(BaseField): #single value
	def __init__(self, name, label=None, dtype=str, default=None, help=None, options=[], **kwargs):
		 super(self.__class__,self).__init__(name, 
			label=label, dtype=dtype, default=default, help=help, options=options, **kwargs)
	def _html_template(self):
		return """			<label for='id_{{field}}' class='
							{%- if required %} required {%- endif -%}
								'>
							{{label}} :
						</label>
				<fieldgroup>
				{%- for key,title in choices %}
					<input id='id_{{field}}' name='{{field}}' type='radio' 
						value='{{key}}' 
						{%- if disabled -%} disabled {%- endif -%}
						{%- if key==value %} checked {%endif%}
					>
					{{title}}</input>
				{%- endfor %}
				</fieldgroup> 
			"""

class MultiSelectField(BaseField):
	#TODO:DO
	def __init__(self):
		 super(self.__class__,self).__init__(name, **vars())
	def parse_field(self, args_in):
		if args_in.getlist(self.name):
			self.value_raw = args_in.getlist(self.name)
			return True
		return False

class MultiCheckField(BaseField):
	def __init__(self, name, label=None, dtype=list, default=None, help=None, options=[], **kwargs):
		 super(self.__class__,self).__init__(name, 
			label=label, dtype=dtype, default=default, help=help, options=options, **kwargs)
	def _html_template(self):
		return """			<label for='id_{{field}}' class='
							{%- if required %} required {%- endif -%}
								'>
							{{label}} :
						</label>
				{%- for key,title in choices %}
					<input id='id_{{field}}' name='{{field}}' type='checkbox' 
						value='{{key}}'	
						{%- if disabled -%} disabled {%- endif -%}
						{%- if key in value %} checked='checked'{% endif %} 
					>
					{{title}}</input>
				{%- endfor %}
			</fieldgroup> """
	def parse_field(self, args_in):
		if args_in.getlist(self.name):
			self.value_raw = args_in.getlist(self.name)
			return True
		return False





