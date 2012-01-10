import psycopg2
from flask import Flask, url_for, render_template, g, session, request, redirect, abort
from flaskext.openid import OpenID, COMMON_PROVIDERS
import datetime
import os
import sys
import csv

from sqlhelpers import *
from settings import *

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


