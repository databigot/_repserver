
from flask import Response
import csv
from cStringIO import StringIO


def csv_out(ROWS, COLS, REPORTSLUG):

    filename = REPORTSLUG + '--DATE_NOW.csv'
    csvfile = StringIO();
    csvout = csv.writer(csvfile)

    csvout.writerow( [col['l'] for col in COLS] );

    for row in ROWS:
	csvout.writerow([ row[col['k']] 
		for col in COLS] )

    data =  csvfile.getvalue()
#    response = Response(data, content_type='text/csv')
#    response['Content-Disposition'] = 'attachment; filename='+FILENAME
    response = Response(status=200, mimetype='text/csv', content_type='text/csv')
    response.data = data
    response.headers['Content-Disposition'] = 'attachment; filename='+filename;	
    return response

#def djson_out(ROWS, COLS):
#	cols = [
#
#def gjson_out(ROWS, COLS):
#	cols = [{id: 'k', label:'l', type:'' 


