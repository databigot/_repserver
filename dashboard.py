#import psycopg2
from flask import Flask, url_for, render_template, g, session, request, redirect, abort
import jinja2
from flaskext.openid import OpenID, COMMON_PROVIDERS
import datetime
import os
import sys

import csv

from settings import * #imports general settings, AND settings_local.py machine-local settings. 
from sqlhelpers import *

import hashlib
from pymongo import objectid, ReadPreference
import math
from datetime import date, timedelta

##from long_running import ui_invoke_long_running

#psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
#psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

app = Flask(__name__)

@app.context_processor
def inject_now():
    return dict(now=datetime.date.strftime(datetime.datetime.now(),'%Y%b%d,%H:%M%p'))


#=========================================================
#
#  Open ID Support code


oid = OpenID(app, '/tmp/'+str(UID))

@app.before_request
def lookup_current_user():
    g.user = None
    if 'openid' in session:
        if session['email'].lower().endswith("@tippr.com"):
            g.user = session['email']
            return

    if (request.path != "/login") and (not g.user):
        return redirect("/login")


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(oid.get_next_url())

    openid = request.form.get('openid')
    if not openid:
        openid = COMMON_PROVIDERS["google"]

    if openid:
        resp = oid.try_login(openid, ask_for=['email'])
        return resp

    raise Exception("Shouldn't get here")


@app.route("/logout")
def logout():
    if g.user:
        del session['openid']
    return redirect("/")
    return redirect("/login")


@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    session['email'] = resp.email

    next = oid.get_next_url()
    return redirect( next )


#=========================================================

@app.route("/")
def index():
	reports = {}

        reports['MARKETPLACE REPORTS'] = [
                {'name': 'TOM Dashboard'                        ,'url': url_for('tom_dashboard')}
		,{'name': 'TOM voucher sales by site'           ,'url': url_for('cumulative_tom_sales_by_site')}
                ,{'name': 'TOM sales by date'                   ,'url': url_for('tom_sales_by_date')}
                ,{'name': 'TOM activity by agency'              ,'url': url_for('tom_activity_by_agency')}
                ,{'name': 'TOM activity by publisher'           ,'url': url_for('tom_activity_by_publisher')}
                ,{'name': 'TOM promotion detail'      ,'url': url_for('tom_promotion_detail')}
                ,{'name': 'TOM local inventory levels'          ,'url': url_for('tom_local_inventory',status='approved')}
                ,{'name': 'TOM offers per market'               ,'url': url_for('tom_offers_per_market')}
                ,{'name': 'TOM Inventory of Non-National Offers'                ,'url': url_for('tom_detailed_inventory_non_national')}
                ,{'name': 'TOM Offer Breakdown'                ,'url': url_for('tom_breakdown')}
                ]

	reports['PBT REPORTS'] = [
		 {'name': "Purchases Report"			,'url': url_for('purchasereport')}
		,{'name': "Offers Dashboard"			,'url': url_for('offers')}
		,{'name': "Publishers Reports"			,'url': url_for('listpubs')}
		,{'name': 'Account Detail Report'		,'url': url_for('account_detail')}
		,{'name': 'Offer Metrics Report'		,'url': url_for('offer_metrics',offer_id=1)}
		,{'name': 'Deal Category Report'		,'url': url_for('dealcats')}
		,{'name': 'Customer Engagement Dashboard'	,'url': url_for('engagement')}
		,{'name': 'Daily Credit Grants Report'		,'url': url_for('credits_granted_by_date',rdate='2012-01-01')}
		,{'name': 'Monthly Credit Summary Report'	,'url': url_for('credit_summary_by_month',rdate='2012-01-01')}
		,{'name': 'Sales Report by Agent'		,'url': url_for('agent_sales')}
		,{'name': 'Channel Sales By Offer Type Summary'  ,'url': url_for('pbt_channel_sales_by_offer_type_summary', channel='tippr-honolulu')}
		,{'name': 'Channel Sales By Offer Type Detail', 'url': url_for('pbt_channel_sales_by_offer_type_detail', channel='tippr-honolulu')}
		,{'name': 'Schools Referral Report for MS Offers', 'url': url_for('schools_referral')}
		] 

        reports['OTHER REPORTS'] = [
                {'name': 'Hasoffers transactions by publisher/date', 'url': url_for('hasoffers_transaction_detail',month_start='2012-03-01',publisher='frugaling')}
		,{'name': 'Voucher debug tool between TOM and PBT', 'url': url_for('tom_pbt_voucher_sync',offer_id=1)}
        	]


	reports['TOOLS'] = [
		{'name': 'Finn & Maddy Code Generator'		,'url': '/volusion'}
        	,{'name': 'Email Schedule Checker',           'url': '/campaigns'}
        	,{'name': 'Request Long-running Report',           'url': '/lr'}
	]	

	return render_template("index.html", REPORTS=reports);


#--------------------------------------------------------


recentbad_sql = ( "select p.name pub_name, o.id offer_id, o.name offer_name, o.start_date start_date,"
		"	 o.end_date end_date, o.automatable, o.status offstatus, t.status txnstatus, count(*)"
                "  from core_offer o, core_publisher p, core_item i, core_transaction t"
                " where o.publisher_id = p.id"
                "   and o.status = 'processing'"
                "   and end_date <= current_date"
                "   and i.offer_id = o.id"
                "   and i.transaction_id = t.id"
                " group by p.name, o.id, o.name, o.start_date, o.end_date, o.automatable, o.status, t.status"
                " order by end_date desc" )

inprocess_sql = ( "select p.name pub_name, o.id offer_id, o.name offer_name, o.start_date start_date, "
		"	o.end_date end_date, o.automatable, o.status offstatus, t.status txnstatus, count(*)"
                "  from core_offer o, core_publisher p, core_item i, core_transaction t"
                " where o.publisher_id = p.id"
                "   and end_date > current_date"
                "   and end_date < current_date+30"
                "   and i.offer_id = o.id"
                "   and i.transaction_id = t.id"
                " group by p.name, o.id, o.name, o.start_date, o.end_date, o.automatable, o.status, t.status"
                " order by end_date desc" )


@app.route("/offers/")
def offers():
    recentbad = get_offers( recentbad_sql )
    stillrunning = get_offers( inprocess_sql )
    return render_template("dashboard.html",failed=filter( lambda x: x["failed%"] > 25, recentbad ), current=stillrunning)


def get_offers(sql):
	(cols,results) = throw_sql(sql, DB_PBT)
	offers = []
	if (len(results) == 0):
	    return []
	offer = dict( zip( cols, results[0] ) )
	offer["statii"] = {}

	for res in results:
	    if res[1] != offer["offer_id"]:
		total = sum( [v for k,v in offer["statii"].items() ] )*1.0
		failed = sum( [v for k,v in offer["statii"].items() if k != "completed"] )*1.0
		offer["failed%"] = int(failed*100/total)
		offers.append(offer)
#
		offer = dict( zip( cols, res ) )
		offer["statii"] = {}

	    offer["statii"][res[7]] = res[8]

	total = sum( [v for k,v in offer["statii"].items() ] )*1.0
	failed = sum( [v for k,v in offer["statii"].items() if k != "completed"] )*1.0
	offer["failed%"] = int(failed*100/total)
	offers.append(offer)

	return offers

#--------------------------------------------------------

purchase_sql = ( "select o.id "
                 "     , o.headline"
                 "     , date(t.occurrence at time zone 'PST')"
                 "     , count(i.id)"
                 "  from core_offer o, core_item i, core_transaction t"
                 " where (i.offer_id = o.id)"
                 "   and (i.transaction_id = t.id)"
                 "   and (t.status in ('completed','pending'))"
                 "   and ((t.occurrence at time zone 'PST') > date(now() at time zone 'PST')-7)"
                 " group by o.id, headline, date(occurrence at time zone 'PST')"
                 " order by o.id, date" )

purchase30_sql = ( "select date(occurrence at time zone 'PST'), count(i.id) "
                   "  from core_item i, core_transaction t"
                   " where (i.transaction_id = t.id)"
                   "   and (date(occurrence at time zone 'PST') > date(now() at time zone 'PST')-30)"
                   "   and (t.status in ('completed', 'pending'))" 
                   " group by date(occurrence at time zone 'PST')"
                   " order by date(occurrence at time zone 'PST')" )

@app.route("/purchases/")
def purchasereport():
    # get the raw data back from the db
    (cols,results) = throw_sql( purchase_sql, DB_PBT)


    offers = []
    days = {}
    names = {}
    for r in results:
	rdict = dict(zip(cols, r))
        if rdict["count"] == 0:
            continue; 

        if not rdict["id"] in offers:
            offers.append( rdict["id"] )
            names[rdict["id"]] = rdict["headline"]
        if not rdict["date"] in days:
            days[rdict["date"]] = {}
        days[rdict["date"]][rdict["id"]] = rdict["count"]


    context = {}
    context["p30"] = (lambda c,rs: [dict(zip(c,r)) for r in rs])(*throw_sql( purchase30_sql, DB_PBT ))

    context["names"] = names
    context["days"] = days
    context["offers"] = offers
    context["today"] = (datetime.datetime.now() - timedelta(seconds=8*60*60)).date();
    context["yesterday"] = context["today"] - timedelta(days=1)

    return render_template('purchases.html', **context )


#--------------------------------------------------------



##TODO:break this out to reports.py?
#merchant_sql = ( "select o.id offerid, p.primary_channel_id channelid, o.end_date, ad.name, o.headline, g.title city, count(i.id), sum(i.amount), c.name channame, p.name pubname"
#  		 "   from core_advertiser ad, core_offer o, core_publisher p, core_channel c, core_geography g, core_item i, core_transaction t"
#		 "  where (o.advertiser_id = ad.id)"
#		 "    and (o.publisher_id = p.id)"
#		 "    and (p.primary_channel_id = c.id)"
#		 "    and (c.geography_id = g.id)"
#		 "    and (i.offer_id = o.id)"
#		 "    and (i.transaction_id = t.id)"
#		 "    and (t.status in ('completed','pending'))"
#		 "    and ((ad.name ilike %s) or (o.headline ilike %s))"
#		 "  group by o.id, p.primary_channel_id, o.end_date, ad.name, o.headline, city, c.name, p.name"
#		 "  order by end_date desc;" )
merchant_sql = (" with counts as " 
		"  (select o.id offer_id, t.status, count(i.id) num_stat, sum(i.amount) amount_stat "
                "   from core_advertiser ad, core_item i, core_transaction t, core_offer o "
                "   where (i.transaction_id = t.id) "
		"   and (i.offer_id = o.id) and (ad.id = o.advertiser_id) "
                "   and ((ad.name ilike %s) or "
		"   (o.headline ilike %s)) group by o.id, t.status )"
		"  select  o.id offerid, p.primary_channel_id, g.title city, o.end_date, ad.name advertiser, p.name pubname, c.name channame, o.headline, count(i.id) voucher_count, sum(i.amount) voucher_sum, "
		"  (select sum(num_stat) from counts where offer_id = o.id and counts.status = 'completed') as completed, "
		"  (select sum(amount_stat) from counts where offer_id = o.id and counts.status = 'completed') as completed_amount, "

		"  (select sum(num_stat) from counts where offer_id = o.id and counts.status = 'voided') as voided, "
                "  (select sum(amount_stat) from counts where offer_id = o.id and counts.status = 'voided') as voided_amount, "

		"  (select sum(num_stat) from counts where offer_id = o.id and counts.status = 'aborted') as aborted, "
                "  (select sum(amount_stat) from counts where offer_id = o.id and counts.status = 'aborted') as aborted_amount, "

		"  (select sum(num_stat) from counts where offer_id = o.id and counts.status = 'failed') as failed, "
                "  (select sum(amount_stat) from counts where offer_id = o.id and counts.status = 'failed') as failed_amount "

		"   from core_advertiser ad, core_item i, core_transaction t, core_offer o, core_publisher p, core_channel c, core_geography g "
		"   where (i.transaction_id = t.id) and (i.offer_id = o.id) and (ad.id = o.advertiser_id) and (t.publisher_id = p.id) and (p.primary_channel_id = c.id) and (c.geography_id = g.id) "
		"   and ((ad.name ilike %s) or (o.headline ilike %s)) "
		"   group by o.id, o.end_date, o.headline, ad.name, p.name, p.primary_channel_id, c.name, g.title;"
	)

@app.route("/merchant")
@app.route("/merchant/")
def merchant_report( name = None ):
    name = None
    if 'name' in request.values:
    	name = request.values['name']

    context = {}
    context["is_good"] = name and (len(name) > 3)
    context["query"] = name
    if context["is_good"]:
        cols, rows = throw_sql( merchant_sql, DB_PBT, params=('%'+name+'%','%'+name+'%','%'+name+'%','%'+name+'%',) )
	context["rows"] = [dict(zip(cols,row)) for row in rows]

    return render_template( 'merchant.html', **context )


@app.route("/pubreps/")
def listpubs():
    sql = """
        select title,name,id from core_publisher where status = 'active' order by title;
    """
    cols, resultset = throw_sql(sql   ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    for row in ROWS: ##add a new column, generated.
        row['report1'] = {'linkto':url_for('dealcats', id=row['id']),'show':row['title']} #to setup link 

    COLS = [#ordered in display order, add computeds or non-db fields
        #k:field_name            l:title(\n)        c:classes                u:formatting        w:width
#TODO: add in tool-tip, and link-logic.
        {'k':'title'        ,'l': 'Publisher '    ,'c': ''    ,'u': None            ,'w': '200px'}   #linkto: 
        ,{'k':'name'        ,'l': 'name'        ,'c': ''    ,'u': 'link'        ,'w': '100px'}
        ,{'k':'report1'        ,'l': 'Offer Category Report'            ,'c': ''    ,'u': 'linkto', 'w': '200px'        }
        ,{'k':'id'            ,'l': ''            ,'c': ''    ,'u': 'link'        ,'w': '100px'}
    ]

    context = {};
    TITLE='ACTIVE PUBLISHERS LIST';
    SUBTITLE='';
    return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE);

from campaigns import showcampaigns
showcampaigns = app.route("/campaigns/<datestr>")(showcampaigns)
showcampaigns = app.route("/campaigns/")(showcampaigns)

from reports import account_detail
account_detail = app.route("/account_detail/<id>")(account_detail)
account_detail = app.route("/account_detail/", methods=['GET','POST'])(account_detail)

from reports import tom_pbt_voucher_sync
tom_pbt_voucher_sync = app.route("/tom_pbt_voucher_sync/<offer_id>")(tom_pbt_voucher_sync)

from reports import cumulative_tom_sales_by_site
cumulative_tom_sales_by_site = app.route("/cumulative_tom_sales_by_site/<status>")(cumulative_tom_sales_by_site)
cumulative_tom_sales_by_site = app.route("/cumulative_tom_sales_by_site/", methods=['GET','POST'])(cumulative_tom_sales_by_site)

from reports import pbt_channel_sales_by_offer_type_summary
pbt_channel_sales_by_offer_type_summary = app.route("/pbt_channel_sales_by_offer_type_summary/<channel>")(pbt_channel_sales_by_offer_type_summary)
pbt_channel_sales_by_offer_type_summary = app.route("/pbt_channel_sales_by_offer_type_summary/", methods=['GET','POST'])(pbt_channel_sales_by_offer_type_summary)

from reports import pbt_channel_sales_by_offer_type_detail
pbt_channel_sales_by_offer_type_detail = app.route("/pbt_channel_sales_by_offer_type_detail/<channel>")(pbt_channel_sales_by_offer_type_detail)
pbt_channel_sales_by_offer_type_detail = app.route("/pbt_channel_sales_by_offer_type_detail/", methods=['GET','POST'])(pbt_channel_sales_by_offer_type_detail)


from reports import tom_sales_by_date
tom_sales_by_date = app.route("/tom_sales_by_date/", methods=['GET','POST'])(tom_sales_by_date)

from reports import tom_activity_by_agency
tom_activity_by_agency = app.route("/tom_activity_by_agency/", methods=['GET','POST'])(tom_activity_by_agency)
tom_activity_by_agency = app.route("/tom_activity_by_agency/<rdate>")(tom_activity_by_agency)


from reports import tom_activity_by_publisher
tom_activity_by_publisher = app.route("/tom_activity_by_publisher/", methods=['GET','POST'])(tom_activity_by_publisher)

from reports import tom_local_inventory
tom_local_inventory = app.route("/tom_local_inventory/<status>")(tom_local_inventory)
tom_local_inventory = app.route("/tom_local_inventory/", methods=['GET','POST'])(tom_local_inventory)

from reports import tom_offers_per_market
tom_local_inventory = app.route("/tom_offers_per_market/<status>")(tom_offers_per_market)
tom_local_inventory = app.route("/tom_offers_per_market/", methods=['GET','POST'])(tom_offers_per_market)

from reports import tom_detailed_inventory_non_national 
tom_local_inventory = app.route("/tom_detailed_inventory_non_national/<status>")(tom_detailed_inventory_non_national)
tom_local_inventory = app.route("/tom_detailed_inventory_non_national/", methods=['GET','POST'])(tom_detailed_inventory_non_national)

from reports import tom_promotion_detail
#tom_publisher_promotions = app.route("/tom_publisher_promotions/?publisher=<publisher>")(tom_publisher_promotions)
#tom_publisher_promotions = app.route("/tom_publisher_promotions/<publisher>")(tom_publisher_promotions)
tom_promotion_detail = app.route("/tom_promotion_detail/", methods=['GET','POST'])(tom_promotion_detail)

from reports import tom_breakdown
tom_breakdown = app.route("/tom_breakdown/", methods=['GET','POST'])(tom_breakdown)

from reports import tom_dashboard
tom_dashboard = app.route("/tom_dashboard/", methods=['GET','POST'])(tom_dashboard)


from reports import credits_granted_by_date
credits_granted_by_date = app.route("/credits_granted_by_date/<rdate>")(credits_granted_by_date)
credits_granted_by_date = app.route("/credits_granted_by_date/", methods=['GET','POST'])(credits_granted_by_date)

from reports import credit_summary_by_month
credit_summary_by_month = app.route("/credit_summary_by_month/<rdate>")(credit_summary_by_month)
credit_summary_by_month = app.route("/credit_summary_by_month/", methods=['GET','POST'])(credit_summary_by_month)

from reports import offer_metrics
offer_metrics = app.route("/offer_metrics/<offer_id>")(offer_metrics)
offer_metrics = app.route("/offer_metrics/", methods=['GET','POST'])(offer_metrics)

from reports import tom_breakdown
tom_breakdown = app.route("/tom_breakdown/<offer_id>")(tom_breakdown)
tom_breakdown = app.route("/tom_breakdown/", methods=['GET','POST'])(tom_breakdown)

from reports import hasoffers_transaction_detail
hasoffers_transaction_detail = app.route("/hasoffers_transaction_detail/", methods=['GET','POST'])(hasoffers_transaction_detail)

from reports import dealcats
dealcats = app.route("/pubreps/dealcats/<id>")(dealcats)
dealcats = app.route("/pubreps/dealcats", methods=['GET','POST'])(dealcats)

from reports import offers_detail
offers_detail = app.route("/offers_detail")(offers_detail)

from reports import schools_referral
schools_referral = app.route("/schools_referral/<yyyymm>")(schools_referral)
schools_referral = app.route("/schools_referral/")(schools_referral)

def who_in(*groupnames):
   members = []
   for group in groupnames:
	members.extend(ACCESS_GROUPS[group])
   return members
	
def restrict_to(*whitelist): #
   """
	decorator to restrict access to a view to a specific userGroup.
	pass in one or more Access Groups (e.g. "DEVS","VIPS") as defined in settings.py:ACCESS_GROUPS
   """
   allow = who_in(*whitelist)
   def decorator(f):
   	def _restrict(*args):
		if (not g.user in allow):	
   			abort(403)
		return f(*args)
	_restrict.__name__ = f.__name__
	return _restrict
   return decorator


from reports import engagement 
engagement = restrict_to("TEST1","TEST2")(engagement)
engagement = app.route("/pubreps/engage/")(engagement)

#engagement = app.route("/pubreps/engage", methods=['POST'])(engagement)
#engagement = app.route("/pubreps/<id>/engage/")(engagement)

from reports import agent_sales
agent_sales = app.route("/agent_sales/<yyyymm>")(agent_sales)
agent_sales = app.route("/agent_sales/")(agent_sales)

from mongo_reps import subscriptions
subs = app.route("/subs")(subscriptions)


from f_and_m_pages import gen_skus_wform 
gen_skus_wform = app.route("/volusion", methods=['GET', 'POST'] )(gen_skus_wform)

#from reports import txn_detail
#txn_detail = app.route("/txn.<format>/<publisher>")(txn_detail)
#txn_detail = app.route("/txn.<format>")(txn_detail)
#txn_detail = app.route("/txn/<publisher>")(txn_detail)
#txn_detail = app.route("/txn")(txn_detail)

#from long_running import ui_invoke_long_running
#ui_invoke_long_running = app.rount('/long_running/')(ui_invoke_long_running)
from indev import lr_request_rpt
#request_rpt = app.route("/lr/", methods=['GET','POST'])(request_rpt)
lr_request_rpt = app.route("/lr/", methods=['GET','POST'])(lr_request_rpt)

from indev import pmt_detail_view
pmt_detail_view = app.route('/tests/pmt_detail', methods=['GET','POST'])(pmt_detail_view)

from indev import test_args
#txn_detail = app.route('/lr/txn_detail', methods=['GET','POST'])(txn_detail)
test_args = app.route('/tests/test-args', methods=['GET','POST'])(test_args)


@app.route("/cctrans")
def cctrans():
#    conn = Connection("mongodb://warehouse-ro:fr33$tuff@dw.tippr.com/warehouse", read_preference=ReadPreference.SECONDARY_ONLY)
    conn = mongo_connect(DB_EDW,  read_preference=ReadPreference.SECONDARY_ONLY)
    coll = conn.warehouse.events

    query = { 'event' : { '$regex' : '^payments.authorization.' } ,
              'grid' : 'production',
              'timestamp' : { "$gte" : (datetime.datetime.now()-datetime.timedelta(days=14)).isoformat() } }

    cursor = coll.find(query, {'timestamp':1, 'event':1, 'user_ip':1})

    perday = [None] * 14
    perhour = [None] * 24
    perip = {}
    now = datetime.datetime.now()

    perday = [ { "label" : "in the last day" if i == 0 else "%d to %d days ago" % (i, i+1) } for i in range(14) ]
    perhour = [ { "label" : "in the last hour" if i == 0 else "%d to %d hours ago" % (i, i+1) } for i in range(24) ]

    for r in cursor:
        ip = r.get("user_ip", None)
        eventdate = datetime.datetime.strptime( r["timestamp"].split(".")[0], "%Y-%m-%dT%H:%M:%S" )
        hoursago = int(math.floor( (now-eventdate).total_seconds()/3600 ))
        daysago = int(math.floor( ( now-eventdate).total_seconds()/(3600*24)) )
        eventtype = r['event'].split('.')[2]

        perday[daysago][eventtype] = perday[daysago].get(eventtype,0)+1
        
        if hoursago < 24:
            perhour[hoursago][eventtype] = perhour[hoursago].get(eventtype,0)+1
            if ip:
		if not ip in perip:
                    perip[ip] = {'total':0}
	    	perip[ip][eventtype] = perip[ip].get(eventtype,0)+1
                perip[ip]["total"] = perip[ip].get("total",0)+1

    suspicious = []
    for k,v in perip.items():
	if (v.get("success",0) > 1) or (v.get("failed",0) > 2) or (v.get("throttled",0) > 0):
            v["ip"] = k
            suspicious.append(v)


    context = {}
    context["daysago"] = perday 
    context["hoursago"] = perhour
    context["perip"] = suspicious

    return render_template( 'cctrans.html', **context )

#------------------------------------------------------------------------------

@app.route("/upload_codeset/")
def upload_codeset():
    return render_template( 'upload_new_codeset.html' )

@app.route("/action/", methods=["POST"] )
def action():
    act = request.values["action"]
    obtype = request.values["type"]
    oid = objectid.ObjectId( request.values["id"] )

    status = "haven't tried anything"

#    conn = Connection("mongodb://code_store:fr33$tuff@master.dw.tippr.com/code_store")
    conn = mongo_connect(DB_CODESTORE)

    if (obtype == "codeset"):
	if (act== "activate"):
	    conn.code_store.codes.update( { "codeset" : oid }, {"$set" : {"activated":True}}, multi=True  )
            conn.code_store.codesets.update( { "_id" : oid }, {"$set": {"activated":True}} )
            status = "Succeeded: that codeset is activated"
        elif (act == "delete"):
            conn.code_store.codes.remove( { "codeset" : oid } )
            conn.code_store.codesets.remove( { "_id" : oid } )            
            status = "Succeeded: that codeset is toast"
        else:
            status = "Failed: I don't know how to %s a %s" % (act, obtype)
    else:
        status = "Failed: I have no idea what a %s is." % obtype


    context = { "action" : act,
                "obtype" : obtype,
                "id" : request.values["id"],
                "status" : status }

    return render_template( 'action.html', **context )


@app.route("/confirm_codeset/", methods=['POST'])
def upload():
    codes =  request.files["codes"].getvalue().split("\n")


    # Write the codeset
#    conn = Connection("mongodb://code_store:fr33$tuff@master.dw.tippr.com/code_store")
    conn = mongo_connect(DB_CODESTORE)

    db = conn.code_store
    coll = conn.code_store.codes
   

    merch = request.values["merchant"].lower().replace(" ","-").replace(".", "").replace(",","").replace("&","").replace("--", "-")
    dt = datetime.date.today().strftime("%y-%m-%d")
    done = False
    tries = 1
    while not done:
        if (tries == 1):
            name = "%s-%s" % (merch,dt)
        else:
            name = "%s-%s-%s" % (merch, dt, tries)
        found = conn.code_store.codesets.find_one( { "name" : name } )
        if found == None:
            done = True
        else:
            tries += 1

	
    codeset = { "_id" : objectid.ObjectId(),
		"merchant" : request.values["merchant"],
                "related_system": { "system" : request.values["system"], "id" : request.values["sysid"] },
                "name" : name,
		"info" : request.values["comments"],
                "activated" : False }

    db.codesets.save( codeset )
    print "Got this far at least"

    code_docs = [ { "code": c, "codeset" : codeset["_id"], "activated" : False, "expires" : request.values["date"] } for c in codes ]
    db.codes.insert(code_docs)

    # render the page
    context = { "merchant" : request.values["merchant"],
                "expdate" : request.values["date"],
                "system" : request.values["system"],
		"comments" : request.values["comments"],
		"name" : name,
		"samples" : "<br />".join(codes[:5]),
                "codeset_id" : str(codeset["_id"])  }

    return render_template('confirm_codeset.html', **context)






def md5( s ):
    m = hashlib.md5()
    m.update( s )
    return m.hexdigest()

jinja2.filters.FILTERS["md5"] = md5


if __name__ == "__main__":
    app.debug = True
    app.secret_key = "sudo that shit, yo"

    try:
        app.run(host=WEBSERVER_HOST, port=WEBSERVER_PORT)
    except Exception as e:
        print 'Error running on port %s.' % WEBSERVER_PORT
        if WEBSERVER_PORT == 80:
            print 'Remember, port 80 is protected, so sudo that shit yo.'
        print 'Exception detail:', e


