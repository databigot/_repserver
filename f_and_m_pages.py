import random
import cStringIO, sys
from flask import Flask, render_template, render_template_string, g, session, request, redirect

from simpleforms import SimpleField, SimpleForm, SimpleIntField

def print2www(): ##this is a test -- not in use -- of a decorator to print directly out to http
    def decorator(f):
	def _out(*args):
	   buf=cStringIO.StringIO()
	   _old = sys.stdout
	   sys.stdout = buf
	   try: 
	   	f(*args)
	   finally:
	   	out = buff.getvalue()
	       	buf.close()
	       	sys.stdout = _old
	   return out		
	_out.__name__ = f.__name__
	return _out
    return decorator

def gen_skus_wform():
	# TODO: convert to required, and initial, size, and max_length, to match Django forms' syntax.  for the ids as "id_name".
	# TODO: also name the submit button.
	# turnon print to http
 	buf=cStringIO.StringIO()
	_old = sys.stdout
	sys.stdout = buf

	my_form = SimpleForm(template= 'easy_form.html', id='form00')
	my_form.field_list = [ 
		SimpleField(       	id='prefix',    default='ATOM011311',   label='Prefix:'),
	    	SimpleIntField(     	id='quantity',  default=500,            label='Quantity:'),
    		SimpleField(          	id='sku',       default='ATOMIZER_001', label='Sku:'),
    		SimpleIntField(		id='discountautoid_start', default=421,    	label='Discount AutoID Start:'),
    		SimpleIntField( 	id='syncid_start',    default=440,            label='SyncID Start:'),
    		SimpleField(  		id='coupon_name',default="Atomizer $12 for $24 including shipping", 	label='Coupon Name:'),
    		SimpleField( 	  	id='amount',    default='15.98',	label='Amount:')
	]
	#my_form.do_validate=check_params_ok #set validator routine

#todo: create a wrapper to print text output to html form 
	my_form.render_me(do_validate=check_params_ok, do_report=gen_skus) #only call print_results() if form is filled in

	# turnoff print to http
	out=buf.getvalue()
	buf.close()
	sys.stdout = _old
	return out

def check_params_ok(prefix, quantity, sku, discountautoid_start, syncid_start, coupon_name, amount):
	###NOTE: this should return None if all ok, else return a single error string which will be displayed below the form.
	#TODO: change to a try, except
	if (not prefix or not quantity or not sku):
		return "Please fill in the prefix, quantity, and sku fields."	
	return None 


def gen_skus(prefix, quantity, sku, discountautoid_start, syncid_start, coupon_name, amount):        
    ###DO any sort of validation 
    ### and throw exception if invalid, with the error_text
    print "<hr><br>"
    print "<pre>"

    o_codes = {} 
    codes = []
    while len(o_codes) < int(quantity):
        o_codes[prefix + str(random.randint(100000,999999))] = 1

    for code in o_codes.keys():
        codes.append(code)
        
    s_codes = sorted(codes)
    codes = s_codes

    	
    print "Found ", str(len(s_codes)), " unique codes"
    print "TOM CODES:"
    for code in codes:
        print code

    discountautoid_current = int(discountautoid_start)

    print "----"
    
    print "discountautoid, name, discounttype, discountvalue, span, couponcode, onetimeuse, cannot_use_with_any_other, taxable_discountaftertax"
    for code in codes:
        print  str(discountautoid_current) + "," + coupon_name + ",Per Order," + amount + ",N," + str(code) + ",Y,Y,0"
        discountautoid_current += 1

    print "----"

    print "syncid, discountautoid, productcode"
    discountautoid_current = discountautoid_start
    syncid_current = syncid_start

    for code in codes:
        print str(syncid_current) + "," + str(discountautoid_current) + "," + sku
        discountautoid_current += 1
        syncid_current += 1

    print "</pre>"
    return 

##print moo()
 

 

