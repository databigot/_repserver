
from flask import Response
import csv
from cStringIO import StringIO
import json
import datetime
import tempfile
from jinja2 import Template

import boto
from settings import *
import pymongo 

class exporter(): 
#TODO: this was a start idea, to group all the converters together...but never really built it.
		"""
			class to encapsulate: output this data D as output type X,
			potential: text, html-table, json, csv.


			the different output types may want/need different things out of CONTEXT
		""" 
		pass

#TODO: in all converters, handle the data-type, both pulling the datum, and formatting it.
# especially note: 'u'-type, (and maybe 't'-type), handle 'percent', 'linkto', 'currency', etc.
#		right now will die ugly in linkto, and percent.

CSV_MIME='text/csv'; CSV_CTYPE='text/csv'
def data_to_csv(ROWS, COLS, CONTEXT):
    csvfile = StringIO();
    csvout = csv.writer(csvfile)

    csvout.writerow( [col['l'] for col in COLS] );

    for row in ROWS:
	csvout.writerow([ ("%s"%row[col['k']]).encode('ascii','ignore') 
		for col in COLS] )

    return  csvfile.getvalue(), CSV_MIME, CSV_CTYPE

def csv_response(data, CONTEXT):
    filename = '%s--%s.csv'%(CONTEXT.get('REPORTSLUG',''),
		datetime.date.strftime(datetime.datetime.now(), '%Y%b%d_%I%M'))

    response = Response(status=200, mimetype=CSV_MIME , content_type=CSV_CTYPE)
    response.data = data
    if True: #download as attachment/show in browser
        response.headers['Content-Disposition'] = 'attachment; filename='+filename;	
    return response



HTML_MIME='text/html'; HTML_CTYPE='text/html'
def data_to_htmltable(ROWS, COLS, CONTEXT):
	"""
		produce a simple html table of our data
	"""
	html_template = """
	<table>
		<thead>
			<tr> 
				{% for c in COLS %} 
				<th> {{ c['l'] }} </th>
				{% endfor %}
			</tr>
		</thead>
		<tbody>
			{% for r in ROWS %}
			<tr>
				{% for c in COLS %}
				<td class="{{ c['k'] }}">{{ r[c['k']] }}</td>
				{% endfor %}
			</tr>
			{% endfor %}
		</tbody>
	</table>
	"""
	return Template(html_template).render(
		ROWS=ROWS, COLS=COLS, **CONTEXT), HTML_MIME, HTML_CTYPE

def data_to_texttable(ROWS, COLS, CONTEXT):
	"""
	"""
	textout = StringIO();
	doc = ""	

	col_width = {};tbl_width= 0	
	for c in COLS:
		col_name = c['k']
		_wid = len(c['l'])
		col_width[col_name] = _wid
	justifier = {
	#TODO: handle 'u'-type, handle 'percent', 'linkto', 'currency', etc.
		None:		(lambda _val, _wid: (_val or '').ljust(_wid))
		,'string': 	(lambda _val, _wid: (_val or '').ljust(_wid))
		,'number':	(lambda _val, _wid: str(_val).rjust(_wid))
		,'date':	(lambda _val, _wid: str(_val).rjust(_wid))
		}
	formatter = {
		None:		(lambda _val: (_val or '').encode('ascii','ignore'))
		,'string': 	(lambda _val: (_val or '').encode('ascii','ignore')) 
		,'number':	(lambda _val: str(_val)) #commify, zero-blank, currency, percent
		,'date':	(lambda _val: str(_val)) #format date?
		}
		

	for r in ROWS:
		for c in COLS:
			col_name = c['k']
#			if not c['t'] :
			col_width[col_name]= max(col_width[col_name], 
				(0 if not r[col_name] else len(
					formatter[c['t']](r[col_name]))))	
#str(r[col_name])) ))

	print >>textout, CONTEXT["title"].center(sum(col_width.itervalues(), len(COLS)-1))

	# "xx".ljust(10), rjust(), center()
	print >>textout, ' /'+'+'.join(['-'*col_width[c['k']] for c in COLS])+'\\ '
	print >>textout, ' |'+'|'.join([c['l'].center(col_width[c['k']]) for c in COLS])+'| '
	print >>textout, ' |'+'+'.join(['-'*col_width[c['k']] for c in COLS])+'| '
	for r in ROWS:	
		try:
			line = u' |'+u'|'.join(
				[justifier[c['t']](formatter[c['t']](r[c['k']]),col_width[c['k']]) 
					for c in COLS])	+u'| '
			print >>textout, line
		except UnicodeDecodeError,x:
			print >>textout, "Unicode ERROR in Line"
			print x
			print [r[c['k']] for c in COLS]
	print >>textout, ' \\'+'+'.join(['-'*col_width[c['k']] for c in COLS])+'/ '
	print >>textout, ' (%s rows)'% len(ROWS)
	return textout.getvalue(), 'text/plain', 'text/plain'

def unique_filename(format="txt", report="", by=""):
	ext = {'html-table':'html', 'text-table':'txt','csv':'csv', 'json':'json', 'txt':'txt'}[format]
	filename = '%s-%s-%s.%s'%(report
			, by, datetime.date.strftime(datetime.datetime.now()
			, '%Y%b%d_%I%M'), ext)
	return filename

def csv_out_simple(ROWS, COLS, CONTEXT):
    filename = '%s--%s.csv'%(CONTEXT.get('REPORTSLUG',''),
		datetime.date.strftime(datetime.datetime.now(), '%Y%b%d_%I%M'))
    csvfile = StringIO();
    csvout = csv.writer(csvfile)

    csvout.writerow( [col['l'] for col in COLS] );

    for row in ROWS:
	csvout.writerow([ row[col['k']] 
		for col in COLS] )

    data =  csvfile.getvalue()
    response = Response(status=200, mimetype='text/csv', content_type='text/csv')
    response.data = data
    if True: #download as attachment/show in browser
    	response.headers['Content-Disposition'] = 'attachment; filename='+filename;	
    return response

JSON_MIME='application/json'; JSON_CTYPE='application/json'
def data_to_json(ROWS, COLS, CONTEXT):
#TODO: extra things to send: # of rows, query params, datetime, reportname, report version, 		
	data = {
		'COLS':	COLS,
		'ROWS': ROWS
		}
	return json.dumps(data), JSON_MIME, JSON_CTYPE

def json_to_data(data):
	return json.loads(data)

def json_response(data, CONTEXT):	
	#response = Response(status=200, mimetype='text/x-json', content_type='text/x-json')
	response = Response(status=200, mimetype=JSON_MIME, content_type=JSON_CTYPE)
# other examples use application/javascript as the mimetype
# restful spec and Wikipedia say: application/json
	response.data = data

	return response
#, JSON_MIME, JSON_CTYPE

GJSON_MIME='application/json'; GJSON_CTYPE='application/json'
def data_to_gjson(ROWS, COLS, CONTEXT):
#	cols = [{id: 'k', label:'l', type:'' 
	out = "{"
	out += "\n\tcols: [\n"
	
#	cols:
#		id: x, label: y, type: s

	for col in COLS:
		out += "\t\t{label: '%s', type: '%s'},\n" % (col['l'], (col['t'] or 'string'))
	
	out += "\t    ],"	

	out += "\n\trows: ["
	for row in ROWS:
		out += "\n\t\t{c:["
		for col in COLS:
			j = row[col['k']]
#			if col['t'] =='date':
#				j = 'new Date(%y, %m, %d)'%(j.year, j.month, j.day)
#			elif col['t'] =='decimal':
#				j = ...

			out += "{v: '%s'},"% j
		out += "]}"
	out += "\n\t    ]"
	out += "}"
	return out, GJSON_MIME, GJSON_CTYPE

#	return status, mimetype, content_type, data

def gjson_response(data, CONTEXT):
	response = Response(status=200, mimetype=GJSON_MIME, content_type=GJSON_CTYPE)
	response.data = data
	return response

def cache_report_request(context):
	pass

def cache_save_dataset(context):
	pass

def cache_fetch_dataset(context):
	pass

def store_doc_to_s3(doc,unique_name,headers=None, use_prefix=None):
	""" 
	take in data, store it in our s3 bucket, 
	and return url
	"""
	s3 = boto.connect_s3(S3_ACCESS_KEY,S3_SECRET_KEY)
	bucket = s3.get_bucket(S3_REPORT_BUCKET) #bucket to use for storing reports
	
	key = boto.s3.key.Key(bucket)

	if use_prefix: unique_name = use_prefix+'/'+unique_name  #HACK until i figure out how to properly use prefixes.

	key.key = unique_name 
	key.set_contents_from_string(doc, headers=headers)

	url = key.generate_url(100000000, force_http=True)
	return url


def store_as_mongo_fixture(unique_name, query, qualifiers, doc):
	MONGO_HOST = 'localhost' #TODO: move to settings?
	mongo_conn = pymongo.Connection(MONGO_HOST)
	fixtures = mongo_conn.test.fixtures
#	fixtures.save(name, base_query, qualifiers, data)
		#datetime pulled, by_whom, queryversion, ...
	if fixtures.find_one({'name':unique_name}):
		raise Exception('one already exists')
	#TODO: should I just overwrite always?
	fixtures.insert({'name':unique_name, 'base_query':query, 'qualifiers': qualifiers, 'doc':doc})

def load_mongo_fixture(unique_name):
	MONGO_HOST = 'localhost' #TODO: move to settings?
	mongo_conn = pymongo.Connection(MONGO_HOST)
	fixtures = mongo_conn.test.fixtures
	my_fixture = fixtures.find_one({'name':unique_name})

	return my_fixture #nb. returns name, base_query, qualifiers, and doc.

def list_mongo_fixtures(query):
	MONGO_HOST = 'localhost' #TODO: move to settings?
	mongo_conn = pymongo.Connection(MONGO_HOST)
	fixtures = mongo_conn.test.fixtures
	l_fixtures= fixtures.find({'base_query':query})
	if not l_fixtures: return None
	return [x["name"] for x in fixtures.find({'base_query':query})]






def url_to_tiny(url):
	import urllib
	tiny_maker = "http://tinyurl.com/api-create.php?"+ urllib.urlencode({"url":url})
	try: 
		return  urllib.urlopen(tiny_maker).read()
	finally:
		return None

def store_doc_to_local(doc, unique_name):
	"""
	take in a doc, store it locally in a file,
	and return filepath
	"""
	#TODO: add LOCAL_REPORT_BUCKET to settings.py
	#filepath = LOCAL_REPORT_BUCKET or tempfile.gettempdir()
	filepath =  tempfile.gettempdir()
	filepath += '/'+unique_name
	f = open(filepath, 'w+')
	f.write(doc)
	f.close()
	return filepath

def email_simple(addr_from="reporting@tippr.com",addr_to=[], subject="", body=None):
	"""
	Send simple text emails, (w/o attachments)
	"""
	import smtplib
	from email.mime.text import MIMEText

	msg = MIMEText(body)
	msg['Subject'] = subject
	msg['To'] = ','.join(addr_to)
	msg['From'] = addr_from	
	smtp = smtplib.SMTP('localhost')
	smtp.sendmail(addr_from, addr_to, msg.as_string())
	smtp.quit()

def email_wfiles(addr_from="reporting@tippr.com",addr_to=[], subject="", body=None, files=[]):
	"""
	"""
	import smtplib
	from email.mime.text import MIMEText
	from email.mime.multipart import MIMEMultipart
	import mimetypes

	msg = MIMEMultipart()
	msg['Subject'] = subject
	msg['To'] = ','.join(addr_to)
	msg['From'] = addr_from	
	
	msg.attach(MIMEText(body))

	for f in files:
		if not os.path.isfile(f): continue
		ctype, encoding = mimetypes.guess_type(f)
		if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
           	 	ctype = 'application/octet-stream'
        	maintype, subtype = ctype.split('/', 1)
        	if maintype == 'text':
            		fp = open(f)
            		# Note: we should handle calculating the charset
            		submsg = MIMEText(fp.read(), _subtype=subtype)
            		fp.close()
		else:
			#TODO: FAIL!!
			raise Exception("unrecognized, or non-text type: %s/%s"%(maintype, subtype))
	    		continue
		submsg.add_header('Content-Disposition', 'attachment', filename=f)
		msg.attach(submsg)	
		
	smtp = smtplib.SMTP('localhost')
	smtp.sendmail(addr_from, addr_to, msg.as_string())
	smtp.quit()

def email_senddoc(addr_from="reporting@tippr.com",addr_to=[], subject="", body=None, ctype='text/plain', doc=None, fname='report.txt'):
	"""
	"""
	import smtplib
	from email.mime.text import MIMEText
	from email.mime.multipart import MIMEMultipart
#	import mimetypes

	msg = MIMEMultipart()
	msg['Subject'] = subject
	msg['To'] = ','.join(addr_to)
	msg['From'] = addr_from	
	
	msg.attach(MIMEText(body))

	if ctype is None: 
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
  	 	ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
	if maintype == 'text':
		# Note: we should handle calculating the charset
		submsg = MIMEText(doc, _subtype=subtype)
	else:
		#TODO: FAIL!!
		raise Exception("unrecognized, or non-text type: %s/%s"%(maintype, subtype))
	submsg.add_header('Content-Disposition', 'attachment', filename=fname)
	msg.attach(submsg)	
		
	smtp = smtplib.SMTP('localhost')
	smtp.sendmail(addr_from, addr_to, msg.as_string())
	smtp.quit()


class SortedDict(dict):
    """
    A dictionary that keeps its keys in the order in which they're inserted.
    copied from django/utils/datastructures.py
    """
    def __new__(cls, *args, **kwargs):
        instance = super(SortedDict, cls).__new__(cls, *args, **kwargs)
        instance.keyOrder = []
        return instance

    def __init__(self, data=None):
        if data is None:
            data = {}
        super(SortedDict, self).__init__(data)
        if isinstance(data, dict):
            self.keyOrder = data.keys()
        else:
            self.keyOrder = []
            seen = set()
            for key, value in data:
                if key not in seen:
                    self.keyOrder.append(key)
                    seen.add(key)

    def __deepcopy__(self, memo):
        return self.__class__([(key, deepcopy(value, memo))
                               for key, value in self.iteritems()])

    def __setitem__(self, key, value):
        if key not in self:
            self.keyOrder.append(key)
        super(SortedDict, self).__setitem__(key, value)

    def __delitem__(self, key):
        super(SortedDict, self).__delitem__(key)
        self.keyOrder.remove(key)

    def __iter__(self):
        return iter(self.keyOrder)

    def pop(self, k, *args):
        result = super(SortedDict, self).pop(k, *args)
        try:
            self.keyOrder.remove(k)
        except ValueError:
            # Key wasn't in the dictionary in the first place. No problem.
            pass
        return result

    def popitem(self):
        result = super(SortedDict, self).popitem()
        self.keyOrder.remove(result[0])
        return result

    def items(self):
        return zip(self.keyOrder, self.values())

    def iteritems(self):
        for key in self.keyOrder:
            yield key, self[key]

    def keys(self):
        return self.keyOrder[:]

    def iterkeys(self):
        return iter(self.keyOrder)

    def values(self):
        return map(self.__getitem__, self.keyOrder)

    def itervalues(self):
        for key in self.keyOrder:
            yield self[key]

    def update(self, dict_):
        for k, v in dict_.iteritems():
            self[k] = v

    def setdefault(self, key, default):
        if key not in self:
            self.keyOrder.append(key)
        return super(SortedDict, self).setdefault(key, default)

    def value_for_index(self, index):
        """Returns the value of the item at the given zero-based index."""
        return self[self.keyOrder[index]]

    def insert(self, index, key, value):
        """Inserts the key, value pair before the item with the given index."""
        if key in self.keyOrder:
            n = self.keyOrder.index(key)
            del self.keyOrder[n]
            if n < index:
                index -= 1
        self.keyOrder.insert(index, key)
        super(SortedDict, self).__setitem__(key, value)

    def copy(self):
        """Returns a copy of this object."""
        # This way of initializing the copy means it works for subclasses, too.
        obj = self.__class__(self)
        obj.keyOrder = self.keyOrder[:]
        return obj

    def __repr__(self):
        """
        Replaces the normal dict.__repr__ with a version that returns the keys
        in their sorted order.
        """
        return '{%s}' % ', '.join(['%r: %r' % (k, v) for k, v in self.items()])

    def clear(self):
        super(SortedDict, self).clear()
        self.keyOrder = []





