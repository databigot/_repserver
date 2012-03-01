
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



#def gjson_out(ROWS, COLS):
#	cols = [{id: 'k', label:'l', type:'' 

def cache_report_request(context):
	pass

def cache_save_dataset(context):
	pass

def cache_fetch_dataset(context):
	pass









