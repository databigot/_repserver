import psycopg2
from flask import Flask, url_for, render_template, g, session, request, redirect, abort
import jinja2
from flaskext.openid import OpenID, COMMON_PROVIDERS
import datetime
import os
import sys
import hashlib
from pymongo import Connection, ReadPreference
import math

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

app = Flask(__name__)
oid = OpenID(app, '/tmp/'+str(os.getuid()))

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


@app.route("/")
def dashboard():
    recentbad = get_offers( recentbad_sql )
    stillrunning = get_offers( inprocess_sql )
    return render_template("dashboard.html",failed=filter( lambda x: x["failed%"] > 25, recentbad ), current=stillrunning)

def shared_db():
    try:
        conn = psycopg2.connect("dbname='silos' user='django' host='127.0.0.1'");
        return conn        
    except Exception as e:
        print "I am unable to connect to the db", e
        return None

g_conn = shared_db()

def throw_sql(sql):
    try:
        conn = psycopg2.connect("dbname='silos' user='django' host='127.0.0.1'");
#        conn = g_conn
        curr = conn.cursor()
        curr.execute(sql)
        results = curr.fetchall();
        cols = [x.name for x in curr.description]
        return cols, results;
    except Exception as e:
        print "I am unable to connect to the database", e
        return None

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


def sql_simple_fetchrow(sql):
    try:
        conn = psycopg2.connect("dbname='silos' user='django' host='127.0.0.1'");
#        conn = g_conn
        curr = conn.cursor();
        curr.execute(sql);
        row = curr.fetchone();
        curr.close();
        conn.close();
        return row;
    except Exception as e:
        print "Database error",e
        return None

@app.route("/referrals/<id>")
@app.route("/referrals/")
def referrals_for_account(id = '75514bb16add426bb4b8203c4354d893'):
    sql = """
        select sharer.account_id "Referrer Account", transaction.status "Txn Type", 
                count(distinct(transaction.id)) "# Referred", sum(transaction.amount) "$ Referred",
                sum(transaction.amount) / count(distinct(referred.id)) "Avg $ / Account" 
            from core_invite sharer, core_inviteuse, core_account referred, core_transaction transaction 
            where sharer.account_id = '%(account)s' and invite_id = sharer.id and 
                transaction.account_id = core_inviteuse.account_id and core_inviteuse.account_id = referred.id 
            group by 1, transaction.status 
            order by 2 desc;
    """
    cols, results = throw_sql(sql % {'account':id}    ); ##bind in the input params; and run it.
    context = {};
    context['report_title']='REFERRED TRANSACTION REPORT BY STATUS';
    context['cols']=cols;
    context['rows']=results;
    context['totals']='';
    return render_template("report.html", **context);

@app.route("/referrals2/<id>")
@app.route("/referrals2/", methods=['POST'])
def referrals_for_account2(id=''):
    if id == '':
        if request.method == 'POST':
            id = request.form['id']
        if id == '':
            raise Exception("empty id") 
    if id == 'test':
        id = '75514bb16add426bb4b8203c4354d893'    
    sql = """
        select sharer.account_id "referred_acct", 
                transaction.status "txn_type", 
                count(distinct(transaction.id)) "qty_referred", 
                sum(transaction.amount)::float "amt_referred",
                sum(transaction.amount)::float / count(distinct(referred.id)) "avg_amt_per_acct" 
            from core_invite sharer, core_inviteuse, core_account referred, core_transaction transaction 
            where sharer.account_id = '%(account)s' and invite_id = sharer.id and 
                transaction.account_id = core_inviteuse.account_id and core_inviteuse.account_id = referred.id 
            group by 1, transaction.status 
            order by 2 desc;
    """
    cols, resultset = throw_sql(sql % {'account':id}    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]

    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
#TODO: add in tool-tip, and link-logic.
        {'k':'referred_acct'        ,'l': 'Referrer Account'    ,'u': None            ,'w': '200px'}
        ,{'k':'txn_type'            ,'l': 'Txn Type'                ,'u': None            ,'w': '130px'}
        ,{'k':'qty_referred'        ,'l': '# Referred'                ,'u': 'integer'        ,'w': '120px'}
        ,{'k':'amt_referred'        ,'l': '$ Referred'                ,'u': 'currency'    ,'w': '130px'}
        ,{'k':'avg_amt_per_acct'    ,'l': 'Avg $/ Account'        ,'u': 'currency'    ,'w': '120px'}
    ]

#TODO: 'account:'inputbox& select button, currentval='$id', submiturl=url_for('referrals_for_account2')

    searchform = """
        <form method='POST' action='%s'> <!--- target is me -->
            <p><label id='search_label' for='search_input'><span>Account: </span></label>
            <input id='search_input' name='id' value='%s'>
            <button type='submit'>Search</button></p> 
        </form>
    """%('/referrals2/',id) #note: hardcoded url!
#(url_for('referrals_for_account2'), id)
    context = {};
    TITLE='REFERRED TRANSACTION REPORT'; SUBTITLE= ' BY STATUS';
    return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE, SEARCH=searchform);



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



@app.route("/pubreps/<id>/dealcats")
@app.route("/pubreps/dealcats", methods=['POST'])
def dealcats(id=None):
    if id == None:
        if request.method == 'POST':
            id = request.form['id']
        if id == '':
            raise Exception("empty id") 
    if id == 'test':
        id = 'dd8506870eb34167a489fd59dcda316c'    
    pub_name = sql_simple_fetchrow("select title from core_publisher where id = '%s';"%id)[0];
    sql = """
        select channel.name, advertiser.category_id, count(distinct(offer.id)) "offer count", 
                sum(item.amount)::float "gross revenue", 
                round(sum(item.amount)/count(distinct(offer.id)))::float "gross revenue/offer" 
            from core_transaction transaction, core_channel channel, core_offer offer, core_item item,
                 core_advertiser advertiser 
            where offer.start_date > '2011-02-28' and channel.publisher_id = '%(account)s' and 
                offer.id = item.offer_id and advertiser.id = offer.advertiser_id and 
                transaction.channel_id = channel.id and item.transaction_id = transaction.id 
                and offer.id in (
                    select offer_id from core_offer_channels 
                        group by 1 having count(distinct(channel_id)) = 1) 
            group by 1,2 order by 1 desc;
    """
    cols, resultset = throw_sql(sql % {'account':id}    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]

    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
#TODO: add in tool-tip, and link-logic.
        {'k':'name'        ,'l': 'Offer Name '    ,'u': None            ,'w': '200px'}   #linkto: 
        ,{'k':'category_id'            ,'l': 'Category'    ,'u': None            ,'w': '130px'}
        ,{'k':'offer count'        ,'l': '# offers'        ,'u': 'integer'        ,'w': '120px'}
        ,{'k':'gross revenue'        ,'l': 'ttl gross $ revenue'    ,'u': 'currency'    ,'w': '130px'}
        ,{'k':'gross revenue/offer'    ,'l': 'gross $/offer'        ,'u': 'currency'    ,'w': '120px'}
    ]

    searchform = """
        <form method='POST' action='%s'> <!--- target is me -->
            <p><label id='search_label' for='search_input'><span>Publisher ID: </span></label>
            <input id='search_input' name='id' value='%s'>
            <button type='submit'>Search</button></p> 
        </form>
    """%('/pubreps/dealcats',id) #note: hardcoded url!

    context = {};
    TITLE='OFFER CATEGORY REPORT'; SUBTITLE='(for %s)'%pub_name;
    return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE, SEARCH=searchform, BACK=url_for('listpubs') );

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



@app.route("/cctrans")
def cctrans():
    conn = Connection("dw.tippr.com", read_preference=ReadPreference.SECONDARY_ONLY)
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
    port = 10000+os.getuid()
    if len(sys.argv) > 1:
        if '-production' in sys.argv:
            port = 80
	

    app.debug = True
    app.secret_key = "sudo that shit, yo"

    try:

        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print 'Error running on port %s.' % port
        if port == 80:
            print 'Remember, port 80 is protected, so sudo that shit yo.'
        print 'Exception detail:', e


