from flask import render_template_string, request
class SimpleField:
#todo: default to use my name as the id&name in the form
#todo: default to use my name initial-capped as the label

#ok, if i'm being called as a POST, then set fields to current variables
#else set to defaults
    def __init__(self,  id, default='', label=''):
    	self.id	= id
	self.default= default
	self.label = label 
    def value(self):
	if request.method == 'POST':
		return request.values.get(self.id, None)
	return self.default #if GET
#	form.addfield(self);

class SimpleIntField(SimpleField):
    def value(self):
	return int(SimpleField.value(self) or '0')
 
    
class SimpleForm:
    template = """
<div>
	<form method='POST' id='form01' action=''> <!-- target is me --> 
		{% for field in FIELDS %}
		<label for='{{ field.id }}'> {{ field.label }} </label>
			<input type='text' id='{{ field.id }}' name='{{ field.id }}' value='{{ field.value }}'><br>
		{% endfor %}
		<input type='submit'>
	</form>

	{% if ERRORS %}
		<strong> Error: {{ ERRORS }} </strong>
	{% endif %}
</div>
    """

    def __init__(self, id='00', template='easy_form.html', field_list=[]):
	self.request = request
	self.field_list = field_list
	self.errors = ""
    def addfield(self,field):
	self.field_list.append(field)
    def fields(self):
	return [dict(label=x.label, id=x.id, value=x.value()) for x in self.field_list]
    def kv_record(self):
	record = {}
	for x in self.field_list:
		record[x.id]=x.value()
	return record

#	if request.method == 'GET':
#		return [dict(label=x.label, id=x.id, value=x.default) for x in self.field_list]
#	if request.method == 'POST':
#		return [dict(label=x.label, id=x.id, value=request.values.get(x.id, None)) for x in self.field_list]
    def _validate_me(self, cb=None):
	if request.method == 'GET':
		return False
	if request.method == 'POST':
		self.errors = ''
		if cb:
			self.errors = cb(**self.kv_record())
		return self.errors == None or self.errors == ''
    def render_me(self,do_validate=None, do_report=None):
	im_ok = self._validate_me(do_validate)
	print render_template_string(self.template, ERRORS=self.errors, FIELDS= self.fields())
	if im_ok:
		do_report(**self.kv_record())	
	return 
