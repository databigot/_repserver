
from flask import Response
import csv
from cStringIO import StringIO
import json
import datetime

class exporter(): 
		"""
			class to encapsulate: output this data D as output type X,
			potential: text, html-table, json, csv.


			the different output types may want/need different things out of CONTEXT
		""" 
		pass

def csv_out(ROWS, COLS, CONTEXT):
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

def csv_out_simple(ROWS, COLS, CONTEXT):
    filename = '%s--%s.csv'%(CONTEXT.get('REPORTSLUG',''),
		datetime.date.strftime(datetime.datetime.now(), '%Y%b%d_%I%M'))
    csvfile = StringIO();
    csvout = csv.writer(csvfile)

    csvout.writerow( COLS );

    for row in ROWS:
	csvout.writerow([ row[col] 
		for col in COLS] )

    data =  csvfile.getvalue()
    response = Response(status=200, mimetype='text/csv', content_type='text/csv')
    response.data = data
    if True: #download as attachment/show in browser
    	response.headers['Content-Disposition'] = 'attachment; filename='+filename;	
    return response



def json_out(ROWS, COLS, CONTEXT):
#TODO: extra things to send: # of rows, query params, datetime, reportname, report version, 		
	data = {
		'COLS':	COLS,
		'ROWS': ROWS
		}
		
	#response = Response(status=200, mimetype='text/x-json', content_type='text/x-json')
	response = Response(status=200, mimetype='application/json', content_type='application/json')
# other examples use application/javascript as the mimetype
# restful spec and Wikipedia say: application/json
	response.data = json.dumps(data)

	return response


def gjson_out(ROWS, COLS, CONTEXT):
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
	response = Response(status=200, mimetype='application/json', content_type='application/json')
	response.data = out
	return response



def cache_report_request(context):
	pass

def cache_save_dataset(context):
	pass

def cache_fetch_dataset(context):
	pass









