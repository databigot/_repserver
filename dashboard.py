import psycopg2
from flask import Flask, url_for, render_template, g, session, request, redirect, abort
import jinja2
from flaskext.openid import OpenID, COMMON_PROVIDERS
import datetime
import os
import sys

import csv

from sqlhelpers import *
from settings import *

import hashlib
from pymongo import Connection, ReadPreference
import math

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

app = Flask(__name__)
oid = OpenID(app, '/tmp/'+str(UID))

@app.context_processor
def inject_now():
    return dict(now=datetime.datetime.isoformat(datetime.datetime.now()))



recentbad_sql = ( "select p.name, o.id, o.name, o.start_date, o.end_date, o.automatable, o.status, t.status, count(*)"
                "  from core_offer o, core_publisher p, core_item i, core_transaction t"
                " where o.publisher_id = p.id"
                "   and o.status = 'processing'"
                "   and end_date <= current_date"
                "   and i.offer_id = o.id"
                "   and i.transaction_id = t.id"
                " group by p.name, o.id, o.name, o.start_date, o.end_date, o.automatable, o.status, t.status"
                " order by end_date desc" )

inprocess_sql = ( "select p.name, o.id, o.name, o.start_date, o.end_date, o.automatable, o.status, t.status, count(*)"
                "  from core_offer o, core_publisher p, core_item i, core_transaction t"
                " where o.publisher_id = p.id"
                "   and end_date > current_date"
                "   and end_date < current_date+30"
                "   and i.offer_id = o.id"
                "   and i.transaction_id = t.id"
                " group by p.name, o.id, o.name, o.start_date, o.end_date, o.automatable, o.status, t.status"
                " order by end_date desc" )

def get_offers(sql):
    try:
        conn = psycopg2.connect("dbname='silos' user='django' host='127.0.0.1'");
        curr = conn.cursor()
        curr.execute(sql)
        results = curr.fetchall();

        offers = []
        if (len(results) == 0):
            return []

        offer = dict( zip( ["pub_name", "offer_id", "offer_name", "start_date", "end_date", "automatable", "offstatus"], results[0] ) )
        offer["statii"] = {}
        
        for res in results:
            if res[1] != offer["offer_id"]:
                total = sum( [v for k,v in offer["statii"].items() ] )*1.0
                failed = sum( [v for k,v in offer["statii"].items() if k != "completed"] )*1.0
                offer["failed%"] = int(failed*100/total)
                offers.append(offer)
                offer = dict( zip( ["pub_name", "offer_id", "offer_name", "start_date", "end_date", "automatable", "offstatus"], res ) )
                offer["statii"] = {}

            offer["statii"][res[7]] = res[8]

        total = sum( [v for k,v in offer["statii"].items() ] )*1.0
        failed = sum( [v for k,v in offer["statii"].items() if k != "completed"] )*1.0
        offer["failed%"] = int(failed*100/total)
        offers.append(offer)

        return offers
    except Exception as e:
        print "I am unable to connect to the database", e
        return None


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
    return redirect("/login")


@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    session['email'] = resp.email

    next = oid.get_next_url()
    return redirect( next )

@app.route("/offers/")
def dashboard():
    recentbad = get_offers( recentbad_sql )
    stillrunning = get_offers( inprocess_sql )
    return render_template("dashboard.html",failed=filter( lambda x: x["failed%"] > 25, recentbad ), current=stillrunning)

##TODO:move to sqlhelpers.py
def execute_sql( sql, params ):
    try:
        conn = psycopg2.connect("dbname='silos' user='django' host='127.0.0.1'")
        curr = conn.cursor()
        curr.execute( sql, params )
        results = curr.fetchall()
        cols = [x.name for x in curr.description]

	rows = [ dict( zip( cols, r ) ) for r in results ]
        return rows
    except Exception as e:
	raise e
        print "exception executing sql", e
        return None

##TODO:break this out to reports.py?
merchant_sql = ( "select o.id offerid, p.primary_channel_id channelid, o.end_date, ad.name, o.headline, g.title city, count(i.id), sum(i.amount)"
  		 "   from core_advertiser ad, core_offer o, core_publisher p, core_channel c, core_geography g, core_item i, core_transaction t"
		 "  where (o.advertiser_id = ad.id)"
		 "    and (o.publisher_id = p.id)"
		 "    and (p.primary_channel_id = c.id)"
		 "    and (c.geography_id = g.id)"
		 "    and (i.offer_id = o.id)"
		 "    and (i.transaction_id = t.id)"
		 "    and (t.status in ('completed','pending'))"
		 "    and ((ad.name ilike %s) or (o.headline ilike %s))"
		 "  group by o.id, p.primary_channel_id, o.end_date, ad.name, o.headline, city"
		 "  order by end_date desc;" )

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
        context["rows"] = execute_sql( merchant_sql, ('%'+name+'%','%'+name+'%',) )

    return render_template( 'merchant.html', **context )


@app.route("/pubreps/")
def listpubs():
    sql = """
        select title,name,id from core_publisher where status = 'active' order by title;
    """
    cols, resultset = throw_sql(sql % {'account':id}    ); ##bind in the input params; and run it.
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

from reports import referrals
referrals = app.route("/referrals/<id>")(referrals)
referrals = app.route("/referrals/", methods=['POST'])(referrals)

from reports import dealcats
dealcats = app.route("/pubreps/dealcats/<id>")(dealcats)
dealcats = app.route("/pubreps/dealcats", methods=['GET','POST'])(dealcats)

from reports import offers_detail
offers_detail = app.route("/offers_detail")(offers_detail)

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


@app.route("/")
def index():
	reports = [
		{'name': "Offers Dashboard"			,'url': url_for('dashboard')}
		,{'name':"Publishers Reports"			,'url': url_for('listpubs')}
		,{'name':'Referrals Report'			,'url': url_for('referrals')}
		,{'name': 'Deal Category Report'		,'url': url_for('dealcats')}
		,{'name': 'Customer Engagement Dashboard'	,'url': url_for('engagement')}
		,{'name':'Sales Report by Agent','url': url_for('agent_sales')}
		] 
	return render_template("index.html", REPORTS=reports);


@app.route("/cctrans")
def cctrans():
    conn = Connection("mongodb://warehouse-ro:fr33$tuff@dw.tippr.com/warehouse", read_preference=ReadPreference.SECONDARY_ONLY)
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


