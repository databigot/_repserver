import psycopg2
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


def showcampaigns():
    conn = psycopg2.connect("dbname='silos' user='django' host='127.0.0.1'");
    tznow = datetime.now(tz=pytz.utc)
    today = tznow.astimezone( pytz.timezone("America/Chicago") ).date()
    tomorrow = today+timedelta(days=1)

    pubs = get_publishers(conn, tomorrow)
    tzmaster = {}

    for pub in pubs:
        pub["blasts"] = {}
        for key in pub["keys"]:
            try:
                pub["blasts"].update( get_sailthru_blasts( key[0], key[1] ) )
            except Exception as e:
                print "error getting blasts for %s with (%s, %s): %s" % (pub["name"], key[0], key[1], e)

        pub["offers"], timezones = get_offers( conn, tomorrow, pub["id"] )
        tzmaster.update(timezones)

    return render_template('campaigns.html', pubs=pubs, timezones=tzmaster, tomorrow=tomorrow)

