from jinja2 import Template

class BaseField(object):
	"""
	"""
	def __init__(self, name, label=None, dtype=str, default='', options=None, option_prefix = None, help=None, required=False, disabled=False, hidden=False):
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
		self.value_raw = None
		return self
	def is_valid(self):
		return True
	def _html_template(self):
		return ""
	def _html_wrapped(self):
		return """
				<div class='form-row {{field}}'>
					<div>
			""" + self._html_template() + """
				<p class='help'>{{help}}</p>
					</div>
				</div>
			"""
			
	def render_me(self, name, value):	#could be called with self.default, or self.value_raw, or...
		context = {'field'	:name
			,'value'	:value or ''	
			,'label'	:self.label or (name.replace('_',' ').capitalize())
			,'disabled'	:self.disabled
			,'hidden'	:self.hidden
			,'choices'	:self.options
			,'choice_prefix':self.option_prefix or ''
			,'help'		:self.help or ''
			}
		return Template(self._html_wrapped()).render(**context)

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
							{%- if disabled -%} disabled {%- endif -%}
						>
			"""

class DateField(BaseField):
	def __init__(self, name, label=None, dtype=str, default='', help=None, **kwargs): #TODO convert tot datetime.datetime, now()
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

class RadioChoiceField(BaseField):
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
	def __init__(self):
		 super(self.__class__,self).__init__(name, **vars())

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
						{%- if value %} checked='checked'{% endif %} 
					>
					{{title}}</input>
				{%- endfor %}
			</fieldgroup> """

class SuperCoolForm(object):
	fields = []
	def __init__(self, **kwargs):
		self.fields = []
		for kw,value in kwargs.iteritems():
			if isinstance(value,BaseField):
				self._add(value)
	def addField(self, **kwargs):
		for kw,value in kwargs.iteritems():
			if isinstance(value,BaseField):
				return self._add(value)
	def _add(self, field):
		self.fields += [field]
		return self
	def __add__(self, field):
		if isinstance(field, BaseField): 
			return self._add(field)

	def not_valid(self, request):
		return True
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
			
		
		</style>
		<div><form action='{{ACTION}}' method='post'>
			<fieldset class='modlue aligned'>
			""").render(ACTION='')
#               fieldlist = self.make_fieldlist()
		for field in self.fields:
			#print field.__dict__
			form += field.render_me(field.name,field.default)                       
		form += """
                	<br><button type='submit' style='text-align:center;'>Submit</button>                                </fieldset>
		</form></div>                           """
        
		return form





