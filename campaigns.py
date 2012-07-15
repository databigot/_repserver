import psycopg2
from sqlhelpers import db_connectstring
from settings import *
from datetime import date, timedelta, datetime
from hashlib import md5
from urllib import urlencode
from urllib2 import urlopen
from json import loads
from flask import Flask, url_for, render_template, g, session, request, redirect, abort
import pytz


psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)


def get_publishers(conn, dt):

    publisher_query = ( "select distinct p.id, p.name, "
                        "       array( select distinct m.apikey||'|'||m.secretkey "
                        "                from core_mailinglist m, core_segment s, core_channel c "
                        "                where (s.list_id = m.id) and (s.channel_id = c.id) and (c.publisher_id = p.id) ) as keys "
                        "  from core_offer o, core_publisher p "
                        " where (p.id = o.publisher_id) and (o.start_date = %s)" )
       
       
    curr = conn.cursor()
    curr.execute( publisher_query, (dt,) )
    rows = curr.fetchall()

    pubs = []
    for row in rows:
        pubs.append( { "id" : row[0], "name" : row[1], "keys" : [ x.split('|') for x in row[2] ] } )

    return sorted(pubs, key=lambda x: x["name"])


def get_sailthru_blasts( api_key, secret_key ):
    params = { "status" : "scheduled",
               "api_key" : api_key,
               "format" : "json" }

    params["sig"] = md5( secret_key+"".join( sorted( [a[1] for a in params.items()] ) ) ).hexdigest()

    url = "http://api.sailthru.com/blast?"+urlencode(params)
    f = urlopen( url )
    data = loads( f.read() )

    blasts = {}
    for blast in data["blasts"]:
        timestr = blast["schedule_time"]
        offset = int(timestr[-5:])/100
        timestr = timestr[:-5]
        t = datetime.strptime(timestr, "%a, %d %b %Y %H:%M:%S ")-timedelta(hours=offset)
        t = t.replace(tzinfo = pytz.utc)
        blasts[ (blast["list"], blast["subject"]) ] = { "email_count" : blast["email_count"], "blast_id" : blast["blast_id"], "schedule_time":t }

    return blasts


def get_offers( conn, dt, publisher ):
    timezones = {}

    offer_query = ( "select o.id, o.headline, o.status, publication_date at time zone 'CDT', "
                    "       array( select s.name||'|'||g.timezone "
                    "                from core_offer_channels oc, core_channel c, core_geography g, core_segment s "
                    "                where (s.channel_id = c.id) and (g.id = c.geography_id) and (oc.channel_id = c.id) and (oc.offer_id = o.id)) as channels "
                    "  from core_offer o "
                    " where (start_date = %s) and (o.publisher_id = %s) " )

    curr = conn.cursor()
    curr.execute( offer_query, (dt, publisher, ) )
    rows = curr.fetchall()

    offers = []
    for row in rows:
        channels = []
        for c in row[4]:
            name, tz = c.split("|")
            timezones[name] = pytz.timezone( tz )
            channels.append(name)

        offers.append( { "id" : row[0], "headline" : row[1], "status" : row[2], "publication_date" : row[3], "channels" : sorted(channels) } )

    sortorder = ['closed', 'processing', 'published', 'scheduled', 'approved', 'complete', 'creative', 'draft', 'incomplete']

    return sorted(offers, key=lambda x: sortorder.index( x["status"] )), timezones


def get_past_blasts( conn, dt ):

    blast_query = ( "select o.id, o.publisher_id, c.providerid,  m.apikey, m.secretkey, "
                    "       array( select s.name from core_segment s, core_campaign_segments cs where cs.segment_id = s.id and cs.campaign_id = c.id ) as segments "
                    "  from core_offer o, core_offer_campaigns oc, core_campaign c, core_mailinglist m "
                    " where (c.list_id = m.id) and  (oc.campaign_id = c.id) and (oc.offer_id = o.id) and (o.start_date = %s) " )

    curr = conn.cursor()
    curr.execute( blast_query, (dt, ) )
    rows = curr.fetchall()

    blasts = {}
    for row in rows:
        params = { "blast_id" : row[2],
                   "api_key" : row[3],
                   "format" : "json" }

        params["sig"] = md5( row[4]+"".join( sorted( [a[1] for a in params.items()] ) ) ).hexdigest()

        url = "http://api.sailthru.com/blast?"+urlencode(params)
        try:
            f = urlopen( url )
            data = loads( f.read() )

            blasts[ row[0]+"|"+row[5][0] ] = data
        except:
            print "problem with blast #",row[2]

    return blasts


def showcampaigns(datestr = None):

    tznow = datetime.now(tz=pytz.utc)
    today = tznow.astimezone( pytz.timezone("America/Chicago") ).date()
    
    if not datestr:
        dt = today+timedelta(days=1)   # use tomorrow's date
    else:
        dt = datetime.strptime( datestr, "%Y-%m-%d").date()   # use the date supplied

    dtrange = [ dt+timedelta(days=d-7) for d in xrange(0,15) ]


    conn = psycopg2.connect(db_connectstring(DB_PBT))
    pubs = get_publishers(conn, dt)
    tzmaster = {}

    if (dt > today):

        for pub in pubs:
            pub["blasts"] = {}
            for key in pub["keys"]:
                try:
                    pub["blasts"].update( get_sailthru_blasts( key[0], key[1] ) )
                except Exception as e:
                    print "error getting blasts for %s with (%s, %s): %s" % (pub["name"], key[0], key[1], e)

            pub["offers"], timezones = get_offers( conn, dt, pub["id"] )
            tzmaster.update(timezones)
        return render_template('campaigns.html', pubs=pubs, timezones=tzmaster, tomorrow=dt, dtrange=dtrange)

    else:    # if it happened in the past, get blast info
        blasts = get_past_blasts(conn, dt)
        for pub in pubs:
            pub["offers"], timezones = get_offers( conn, dt, pub["id"] )
            tzmaster.update(timezones)

        return render_template('pastcampaigns.html', pubs=pubs, timezones=tzmaster, blasts=blasts, tomorrow=dt, dtrange=dtrange)
