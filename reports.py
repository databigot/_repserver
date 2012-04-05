from sqlhelpers import *
from flask import Flask, url_for, render_template, render_template_string, g, session, request, redirect, abort

from utils import csv_out_simple, json_response, data_to_json, gjson_response, data_to_gjson

from utils import cache_report_request, cache_save_dataset, cache_fetch_dataset
import datetime 

#from flask import Response
#import csv
#from cStringIO import StringIO
def hasoffers_transaction_detail(publisher_id=1,month_start='2012-03-01',publisher='frugaling'):
      import urllib
      #pull all the transactions for a given publisher and given month	
        
      publisher_in = request.args.get('publisher')
      if publisher_in:
          publisher = publisher_in

      month_start_in = request.args.get('month_start')
      if month_start_in:
	  month_start = month_start_in


      sql = """

select distinct(referral.transaction_id) "transaction_id", channel.name "channel", referral.providerid "hasoffers_transaction_id", referral.source "affiliate",(transaction.occurrence at time zone 'pst')::varchar  "tippr_timestamp", transaction.status "tippr_status", transaction.amount::varchar "tippr_amount", offer.name "offer_name"  from core_referral referral, core_publisher publisher, core_channel channel, core_transaction transaction left join core_item item on (item.transaction_id = transaction.id) left join core_offer offer on (offer.id = item.offer_id) where transaction.channel_id = channel.id and date_trunc('month', date(referral.occurrence at time zone 'pst')) = '%(month_start)s' and referral.event='offer-purchase' and referral.provider='hasoffers' and transaction.id = referral.transaction_id and publisher.id = transaction.publisher_id and publisher.name = '%(publisher)s' order by 4;

      """
      cols, resultset = throw_sql(sql % {'month_start':month_start,'publisher':publisher},DB_PBT    ); ##bind in the input p
      ROWS = [dict(zip(cols,row)) for row in resultset]

      for row in ROWS:
          test = 1
	  row['hasoffers_status'] = 'none'
	  row['hasoffers_commission'] = '-1.00'
          row['hasoffers_net_revenue'] = '-1.00'
	  # MAKE SURE THERE IS A PROVIDER ID FOR THE TRANSACTION AND THAT IT IS NOT NULL/EMPTY

          url = "https://api.hasoffers.com/Api"
          url = url + "?Format=json"
          url = url + "&Target=Report"
          url = url + "&Method=getConversions"
          url = url + "&Service=HasOffers"
          url = url + "&Version=2"
          url = url + "&NetworkId=tippr"
          url = url + "&NetworkToken=NETfolm5KpltOeugIlw7JvCjX6Rlq9"
          url = url + "&fields[]=Stat.revenue"
          url = url + "&fields[]=Affiliate.company"
          url = url + "&fields[]=Advertiser.company"
          url = url + "&fields[]=Stat.source"
          url = url + "&fields[]=Stat.payout"
	  url = url + "&fields[]=Stat.refer"
          url = url + "&fields[]=Stat.datetime"
          url = url + "&fields[]=Stat.ad_id"
	  url = url + "&fields[]=Stat.status"
          url = url + "&filters[Stat.ad_id][conditional]=EQUAL_TO"
          url = url + "&filters[Stat.ad_id][values]=" + str(row['hasoffers_transaction_id'])


          f = urllib.urlopen(url)
          json_response  = f.read()
          try:
                decoded_json = json.loads(json_response)
          except:
                print "Cannot decode the json object"
	  try: 
	     row['hasoffers_commission']=str(decoded_json['response']['data']['data'][0]['Stat']['payout'])
	     row['hasoffers_status']=str(decoded_json['response']['data']['data'][0]['Stat']['status'])

	     row['hasoffers_net_revenue'] = str(decoded_json['response']['data']['data'][0]['Stat']['revenue'])
	  except:
		print "Fatal error received querying for " + str(row['hasoffers_transaction_id']) + " in hasoffers"

	  print decoded_json


      COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
        {'k':'transaction_id'           	,'l': 'Tippr Transaction ID'            ,'u': None              ,'w': '200px'}
	,{'k':'channel'				,'l': 'Channel'				,'u': None		,'w': '200px'}
        ,{'k':'hasoffers_transaction_id'        ,'l': 'HasOffers Transaction ID'        ,'u': None              ,'w':'200px'}
        ,{'k':'affiliate'                	,'l': 'Affiliate'  			,'u': None     		,'w': '150px'}
	,{'k':'tippr_timestamp'			,'l': 'Tippr Timestamp'			,'u': 'date'	,'w':'200px'}
	,{'k':'tippr_status'			,'l': 'Tippr Status'			,'u': None		,'w':'120px'}
	,{'k':'tippr_amount'			,'l': 'Tippr Amount'			,'u': None		,'w':'120px'}
	,{'k':'hasoffers_status'		,'l': 'Hasoffers Status'		,'u': None		,'w': '100px'}
	,{'k':'hasoffers_commission'		,'l': 'Hasoffers Commission'		,'u': None		,'w': '100px'}
        ,{'k':'hasoffers_net_revenue'            ,'l': 'Rev. we reported to HO'            ,'u': None              ,'w': '200px'}
	,{'k':'offer_name'            ,'l': 'Offer Name'            ,'u': None              ,'w': '300px'}


      ]


      if 0:
   	for transaction_id in transactions:
           # MAKE SURE THERE IS A PROVIDER ID FOR THE TRANSACTION AND THAT IT IS NOT NULL/EMPTY

	   url = "https://api.hasoffers.com/Api"
	   url = url + "?Format=json"
	   url = url + "&Target=Report"
	   url = url + "&Method=getConversions"
	   url = url + "&Service=HasOffers"
	   url = url + "&Version=2"
	   url = url + "&NetworkId=tippr"
	   url = url + "&NetworkToken=NETfolm5KpltOeugIlw7JvCjX6Rlq9"
	   url = url + "&fields[]=Stat.revenue"
	   url = url + "&fields[]=Affiliate.company"
	   url = url + "&fields[]=Advertiser.company"
	   url = url + "&fields[]=Stat.source"
	   url = url + "&fields[]=Stat.affiliate_info1"
	   url = url + "&fields[]=Stat.affiliate_info2"
	   url = url + "&fields[]=Stat.affiliate_info3"
	   url = url + "&fields[]=Stat.affiliate_info4"
	   url = url + "&fields[]=Stat.affiliate_info5"
	   url = url + "&fields[]=Stat.refer"
	   url = url + "&fields[]=Stat.datetime"
	   url = url + "&fields[]=Stat.ad_id"
	   url = url + "&filters[Stat.ad_id][conditional]=EQUAL_TO"
	   url = url + "&filters[Stat.ad_id][values]=" + str(transaction_id)


	   f = urllib.urlopen(url)
	   json_response  = f.read()
	   try:
		decoded_json = json.loads(json_response)
	   except:
		print "Cannot decode the json object"
      context = {};
      TITLE='HASOFFERS AFFILIATE TRANSACTIONS BY PUBLISHER & MONTH'; SUBTITLE= '';
      searchform = """
        <form method='POST' action='%s'> <!--- target is me -->
            <p><label id='search_label' for='status_input'><span>Month Start: </span></label>
            <input id='month_start_input' name='month_start' value='%s'>
            <button type='submit'>Search</button></p>
        </form>
      """%('/hasoffers_transaction-detail/',month_start) #note: hardcoded url!

      format = request.args.get('format','grid');
      if format == 'csv':

        return csv_out_simple(ROWS,COLS,dict(REPORTSLUG='hasoffers_detail-v1'));
      else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE, SEARCH=searchform);


      # WE ALLOW THE REFERRAL TIMESTAMP AND TRANSACTION TIMESTAMP TO DIFFER BY UP TO ONE DAY


def tom_activity_by_agency():
    # agency name	
    #offers entered	
    # offers approved	
    # promotions requested i
     # promotions approved
    # promotions run
    # vouchers sold
    # gross sales
    # tom fees generated


    sql = """
    select agency.name "agency", count(distinct(offers_entered.id)) "entered_offers", count(distinct(offers_approved.id)) "approved_offers", count(distinct(promotions_created.id)) "promotions_created", count(distinct(promotions_run.id)) "promotions_run", count(distinct(voucher.id)) "vouchers_sold" from marketplace_offer offers_entered left join marketplace_offer offers_approved on (offers_entered.id = offers_approved.id and offers_approved.status = 'approved') left join marketplace_promotion promotions_created on (offers_entered.id = promotions_created.offer_id) left join marketplace_promotion promotions_run on (promotions_created.id = promotions_run.id and promotions_run.status in ('closed','finalized')) left join marketplace_promotioninventory pi on (promotions_run.id = pi.promotion_id) left join marketplace_voucher voucher on (pi.id = voucher.product_id), marketplace_agency agency where agency.id = offers_entered.agency_id group by 1;
    """
    cols, resultset = throw_sql(sql,DB_TOM    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
        {'k':'agency'                     ,'l': 'Agency'               ,'u': None              ,'w': '120px'}
        ,{'k':'entered_offers'                  ,'l': 'Offers Entered'          ,'u': 'integer'              ,'w':'80px'}
        ,{'k':'approved_offers'                ,'l': 'Offers Approved'  ,'u': 'integer'         ,'w': '80px'}
	,{'k':'promotions_created'		,'l': 'Promotions Created','u': 'integer'	,'w': '80px'}
	,{'k':'promotions_run'			,'l': 'Promotions Run','u': 'integer'		,'w': '80px'}
	,{'k':'vouchers_sold'			,'l': 'Vouchers Sold','u': 'integer'		,'w': '80px'}


    ]

    context = {};
    TITLE='TOM ACTIVITY BY AGENCY SOURCE'; SUBTITLE= '';
    searchform = ''
    format = request.args.get('format','grid');
    if format == 'csv':
	return csv_out_simple(ROWS,COLS,dict(REPORTSLUG='tom_activity_by_agency-v1'));

    else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE, SEARCH=searchform);

def tom_activity_by_publisher():
    # agency name
    # promotions requested i
    # promotions run
    # vouchers sold


    sql = """
     select publisher.name "publisher", count(distinct(promotions_created.id)) "promotions_created", count(distinct(promotions_run.id)) "promotions_run", count(distinct(voucher.id)) "vouchers_sold" from marketplace_promotion promotions_created left join marketplace_promotion promotions_run on (promotions_created.id = promotions_run.id and promotions_run.status in ('closed','finalized')) left join marketplace_promotioninventory pi on (promotions_run.id = pi.promotion_id) left join marketplace_voucher voucher on (pi.id = voucher.product_id), marketplace_publisher publisher where publisher.id = promotions_created.publisher_id group by 1;
"""
    cols, resultset = throw_sql(sql,DB_TOM    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
        {'k':'publisher'                     ,'l': 'Publisher'               ,'u': None              ,'w': '120px'}
        ,{'k':'promotions_created'              ,'l': 'Promotions Created','u': 'integer'       ,'w': '80px'}
        ,{'k':'promotions_run'                  ,'l': 'Promotions Run','u': 'integer'           ,'w': '80px'}
        ,{'k':'vouchers_sold'                   ,'l': 'Vouchers Sold','u': 'integer'            ,'w': '80px'}


    ]

    context = {};
    TITLE='TOM ACTIVITY BY PUBLISHER'; SUBTITLE= '';
    searchform = ''
    format = request.args.get('format','grid');
    if format == 'csv':
    	return csv_out_simple(ROWS,COLS,dict(REPORTSLUG='tom_activity_by_publisher-v1'));
 
    else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE, SEARCH=searchform);

def cumulative_tom_sales_by_site(status='assigned'):
    status_in = request.args.get('status')
    if status_in:
        status = status_in 

    sql = """
select site.name "site", voucher.status "status", count(voucher.*) "vouchers" from marketplace_site site, marketplace_voucher voucher where voucher.site_id = site.id group by 1,2 having count(voucher.*) > 1 and voucher.status = '%(status)s' order by 3 desc;

    """
    cols, resultset = throw_sql(sql % {'status':status},DB_TOM    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
        {'k':'site'  			,'l': 'Site Name'    		,'u': None            	,'w': '200px'}
        ,{'k':'status'			,'l': 'Voucher Status'		,'u': None     		,'w':'80px'}
        ,{'k':'vouchers'                ,'l': 'Vouchers Sold/Assigned'  ,'u': 'integer'		,'w': '150px'}

    ]

    context = {};
    TITLE='CUMULATIVE TOM VOUCHERS SALES BY SITE NAME (ALL VOUCHERS THAT HAVE NOT BEEN RETURNED/CANCELLED)'; SUBTITLE= '';
    searchform = """
        <form method='POST' action='%s'> <!--- target is me -->
            <p><label id='search_label' for='status_input'><span>Date: </span></label>
            <input id='status_input' name='status' value='%s'>
            <button type='submit'>Search</button></p>
        </form>
    """%('/cumulative_tom_sales_by_site/',status) #note: hardcoded url!

    format = request.args.get('format','grid');
    if format == 'csv':
	return csv_out_simple(ROWS,COLS,dict(REPORTSLUG='tom_cumulative_vouchers-v1'));

    else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE, SEARCH=searchform);

def tom_local_inventory(status='approved'):
    status_in = request.args.get('status')
    if status_in:
        status = status_in

    sql = """
 select market.name "market", offer.status "current_status", to_char(date(date_trunc('month', offer.available_end_date)), 'YYYY-MM') "expiration_month", count(offer.*) "non-national_offers" from marketplace_market market, marketplace_offer offer, marketplace_offer_markets offermarkets where offermarkets.offer_id = offer.id and offermarkets.market_id = market.id and offer.status = '%(status)s' and offer.available_end_date > now() and offer.id not in (select offer_id from marketplace_offer_markets where market_id = 'f3413ab5b96611e09a38c42c033b32fa') and offer.private_offer = 'f' group by 1,2,3 order by 1,3;

    """
    cols, resultset = throw_sql(sql % {'status':status},DB_TOM    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
        {'k':'market'                     ,'l': 'TOM Market'               ,'u': None              ,'w': '200px'}
        ,{'k':'current_status'                  ,'l': 'Offer Status'          ,'u': None              ,'w':'100px'}
	,{'k':'expiration_month'	,'l': 'Expiration Month'	,'u': None 		,'w': '100px'}
        ,{'k':'non-national_offers'                ,'l': 'Non-National Offer Count'  ,'u': 'integer'         ,'w': '150px'}

    ]

    context = {};
    TITLE='TOM LOCAL INVENTORY LEVELS (non national offers, in approved status, with private_offer set to false)'; SUBTITLE= '';
    searchform = """
        <form method='POST' action='%s'> <!--- target is me -->
            <p><label id='search_label' for='status_input'><span>Date: </span></label>
            <input id='status_input' name='status' value='%s'>
            <button type='submit'>Search</button></p>
        </form>
    """%('/cumulative_tom_sales_by_site/',status) #note: hardcoded url!

    format = request.args.get('format','grid');
    if format == 'csv':
	return csv_out_simple(ROWS,COLS,dict(REPORTSLUG='tom_local_inventory-v1'));

    else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE, SEARCH=searchform);


def tom_local_inventory(status='approved'):
    status_in = request.args.get('status')
    if status_in:
        status = status_in

    sql = """
 select market.name "market", offer.status "current_status", to_char(date(date_trunc('month', offer.available_end_date)), 'YYYY-MM') "expiration_month", count(offer.*) "non-national_offers" from marketplace_market market, marketplace_offer offer, marketplace_offer_markets offermarkets where offermarkets.offer_id = offer.id and offermarkets.market_id = market.id and offer.status = '%(status)s' and offer.available_end_date > now() and offer.id not in (select offer_id from marketplace_offer_markets where market_id = 'f3413ab5b96611e09a38c42c033b32fa') and offer.private_offer = 'f' group by 1,2,3 order by 1,3;

    """
    cols, resultset = throw_sql(sql % {'status':status},DB_TOM    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
        {'k':'market'                     ,'l': 'TOM Market'               ,'u': None              ,'w': '200px'}
        ,{'k':'current_status'                  ,'l': 'Offer Status'          ,'u': None              ,'w':'100px'}
	,{'k':'expiration_month'	,'l': 'Expiration Month'	,'u': None 		,'w': '100px'}
        ,{'k':'non-national_offers'                ,'l': 'Non-National Offer Count'  ,'u': 'integer'         ,'w': '150px'}

    ]

    context = {};
    TITLE='TOM LOCAL INVENTORY LEVELS (non national offers, in approved status, with private_offer set to false)'; SUBTITLE= '';
    searchform = """
        <form method='POST' action='%s'> <!--- target is me -->
            <p><label id='search_label' for='status_input'><span>Date: </span></label>
            <input id='status_input' name='status' value='%s'>
            <button type='submit'>Search</button></p>
        </form>
    """%('/cumulative_tom_sales_by_site/',status) #note: hardcoded url!

    format = request.args.get('format','grid');
    if format == 'csv':
	return csv_out_simple(ROWS,COLS,dict(REPORTSLUG='tom_local_inventory-v1'));

    else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE, SEARCH=searchform);

def tom_offers_per_market():
    sql = """
	with offermarkets as (
	    select m.label from 
	        marketplace_offer o, marketplace_offer_markets om, marketplace_market m 
		    where (om.market_id = m.id) and (om.offer_id = o.id) 
		        and (not o.available_start_date > current_date) 
			and (not o.available_end_date < current_date) 
			and (o.status = 'approved')  
			and (private_offer = false) 
			and (o.id not in (
			    select o.id from 
				marketplace_offer o, marketplace_offer_markets om 
				    where (om.offer_id = o.id) 
					and (om.market_id = 'f3413ab5b96611e09a38c42c033b32fa')) )) 
	select m.label, count(offermarkets.name) from 
	    marketplace_market m left join offermarkets on (offermarkets.label = m.label) 
		where m.label != 'USA' 
	group by m.label 
	order by m.label;
    """
    cols, resultset = throw_sql(sql, DB_TOM); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
        {'k':'label'                     ,'l': 'TOM Market'               ,'u': None              ,'w': '200px'}
	,{'k':'count'                ,'l': 'Offer Count'  ,'u': 'integer'         ,'w': '150px'}

    ]

    context = {};
    TITLE='TOM OFFER COUNT PER MARKET'; SUBTITLE= '';

    format = request.args.get('format','grid');
    if format == 'csv':
        return csv_out_simple(ROWS,COLS,dict(REPORTSLUG='tom_offers_per_market-v1'));
 
    else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE);

def tom_detailed_inventory_non_national():
    sql = """
	select m.name market, o.name offer, date(o.available_start_date) ::varchar "start_date", date(o.available_end_date) ::varchar "end_date", a.name agency, avg(p.price)::float price, avg(p.ask_price)::float ask_price, avg(p.marketplace_ask)::float marketplace_ask
  	    from marketplace_offer o, marketplace_offer_markets om, marketplace_market m, marketplace_agency a, marketplace_product p
  		where (om.market_id = m.id) and (om.offer_id = o.id)  and (a.id = o.agency_id) and (p.offer_id = o.id)
      		    and (not o.available_start_date > current_date) and (not o.available_end_date < current_date) 
      		    and (o.status = 'approved')  and (private_offer = false) 
     		    and (o.id not in (select o.id from marketplace_offer o, marketplace_offer_markets om where (om.offer_id = o.id) and (om.market_id = 'f3413ab5b96611e09a38c42c033b32fa')) )
        group by market, offer, available_start_date, available_end_date, agency
        order by market, offer;
    """
    cols, resultset = throw_sql(sql ,DB_TOM    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
        {'k':'market'                     ,'l': 'TOM Market'               ,'u': None              ,'w': '200px'}
        ,{'k':'offer'                  ,'l': 'Offer'          ,'u': None              ,'w':'100px'}
	,{'k':'start_date'	,'l': 'Available Start Date'	,'u': 'date' 		,'w': '100px'}
	,{'k':'end_date'	,'l': 'Available End Date'	,'u': 'date' 		,'w': '100px'}
        ,{'k':'agency'                  ,'l': 'Agency'          ,'u': None              ,'w':'100px'}
  	,{'k':'price'                	,'l': 'Price'  ,'u': 'currency'         ,'w': '150px'}
  	,{'k':'ask_price'               ,'l': 'Asking Price'  ,'u': 'currency'         ,'w': '150px'}
  	,{'k':'marketplace_ask'         ,'l': 'Marketplace Asking Price'  ,'u': 'currency'         ,'w': '150px'}
    ]
    context = {};
    TITLE='TOM DETAILED INVENTORY LEVELS (non national offers)'; SUBTITLE= '';

    format = request.args.get('format','grid');
    if format == 'csv':
   	return csv_out_simple(ROWS,COLS,dict(REPORTSLUG='tom_detailed_inventory_non_national-v1'));
 
    else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE);

def credit_summary_by_month(rdate='2012-01-01'):
    rdate_in = request.args.get('rdate')
    if rdate_in:
	rdate = rdate_in

    sql = """
	select static_dates.datei ::varchar "date", 
		sum(s.value) ::float "share_credits_granted", 
		(select sum(n.value) 
			from core_credit n 
			where date(n.activated)=static_dates.datei 
			and n.condition='') ::integer "new_account_credits_granted", 
		(select sum(payment.amount) 
			from core_payment payment, core_transaction transaction 
			where payment._polymorphic_identity = 'payment.creditpayment' 
			and payment.transaction_id = transaction.id 
			and date(transaction.occurrence) = static_dates.datei) ::integer "credits_spent" 
	from 
		(select current_date - s.t as datei 
			from generate_series(0,2000) as s(t)) as static_dates 
	left outer join core_credit s 
		on (date(static_dates.datei) = date(s.activated) and s.condition != '') 
	where date_trunc('month',static_dates.datei) = '%(rdate)s' 
	group by static_dates.datei order by 1;


    """
    cols, resultset = throw_sql(sql % {'rdate':rdate},DB_PBT    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    for row in ROWS:
	  referred_params = []
	  referred_params.append("rdate=" + row['date']) 
          row['share_credits_granted'] = {'linkto':url_for('credits_granted_by_date'), 'params':referred_params, 'show':'$ ' + str(int(row['share_credits_granted']))}
          row['new_account_credits_granted'] = {'linkto':url_for('credits_granted_by_date'), 'params':referred_params, 'show':'$ ' + str(int(row['new_account_credits_granted']))}
    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
#TODO: add in tool-tip, and link-logic.
        {'k':'date'        ,'l': 'Activity Date'    ,'u': 'date'            ,'w': '80px'}
        ,{'k':'share_credits_granted',           'l': 'Share Credits Granted','u':'linkto','w':'150px'}
        ,{'k':'new_account_credits_granted',     'l': 'New Account Credits Granted','u':'linkto','w':'150px'}
	,{'k':'credits_spent'            ,'l': 'Credits Spent'                ,'u': 'currency','w': '150px'}

    ]
#TODO: 'account:'inputbox& select button, currentval='$id', submiturl=url_for('referrals_for_account2')

    searchform = """
        <form method='POST' action='%s'> <!--- target is me -->
            <p><label id='search_label' for='search_input'><span>Date: </span></label>
            <input id='search_input' name='date' value='%s'>
            <button type='submit'>Search</button></p>
        </form>
    """%('/credit_summary_by_month/',rdate) #note: hardcoded url!
#(url_for('referrals_for_account2'), id)
    context = {};
    TITLE='CREDIT SUMMARY BY MONTH (ALL PUBLISHERS)'; SUBTITLE= ' BY DATE';

    format = request.args.get('format','grid');
    if format == 'csv':
        return csv_out_simple(ROWS, COLS, dict(REPORTSLUG='credit_summary_by_month-v1'));
    else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE, SEARCH=searchform);



def credits_granted_by_date(rdate='2012-01-01'):
    rdate_in = request.args.get('rdate')
    if rdate_in:
	rdate = rdate_in

    sql = """

        select date(credit.activated) ::varchar "credit_activated_date",
                account.id "credit_owner_id",
		account.fullname "credit_owner_name",
		emailaddress.email "credit_owner_email",
		publisher.name "credit_owner_publisher_name",
		transaction.id "ref_trans_id",		
                transaction.status "ref_trans_status",
                transaction.amount ::float "ref_trans_amt",
		ref_account.id "ref_trans_account_id",
		ref_account.fullname "ref_trans_account_name",
		ref_email.email "ref_trans_account_email",
                credit.value ::float "credit_amount"
          from
                core_publisher publisher,
		core_emailaddress emailaddress,
		core_account account,
		core_credit credit 
                left join core_transaction transaction on (credit.transaction_id = transaction.id) 
		left join core_account ref_account on (transaction.account_id = ref_account.id)
                left join core_emailaddress ref_email on (ref_account.id = ref_email.account_id)
          where
                publisher.id = account.publisher_id and
		emailaddress.account_id = account.id and
		account.id = credit.account_id and
		date(credit.activated) = '%(rdate)s'; 

    """
    cols, resultset = throw_sql(sql % {'rdate':rdate}    ,DB_PBT); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    for row in ROWS:
          referrer_params = []
          referrer_params.append("id=" + row['credit_owner_id'])
          row['credit_owner_id'] = {'linkto':url_for('account_detail'), 'params': referrer_params, 'show':row['credit_owner_id']}
	  referred_params = []
	  if row['ref_trans_account_id'] != None:
            referred_params.append("id=" + row['ref_trans_account_id'])
            row['ref_trans_account_id'] = {'linkto':url_for('account_detail'), 'params':referred_params, 'show':row['ref_trans_account_id']}
 
	  else:
	    referred_params.append("id=" + 'none') 
            row['ref_trans_account_id'] = {'linkto':url_for('account_detail'), 'params':referred_params, 'show':'none'}

    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
#TODO: add in tool-tip, and link-logic.
        {'k':'credit_activated_date'        ,'l': 'Credit Activated'    ,'u': 'date'            ,'w': '80px'}
        ,{'k':'credit_amount',           'l': 'Credit Amount','u':'currency','w':'50px'}
        ,{'k':'credit_owner_publisher_name'            ,'l': 'Publisher'                ,'u': None            ,'w': '130px'}
        ,{'k':'credit_owner_id'        ,'l': 'Referrer ID'                ,'u': 'linkto'        ,'w': '150px'}
        ,{'k':'credit_owner_name'        ,'l': 'Referrer Name'                ,'u': None    ,'w': '140px'}
        ,{'k':'credit_owner_email'    ,'l': 'Referrer Email'        ,'u': None    ,'w': '150px'}
        ,{'k':'ref_trans_account_id'    ,'l': 'Referred Account ID' ,'u': 'linkto'  ,'w': '150px'}
	,{'k':'ref_trans_account_name'  ,'l': 'Referred Account Name','u': None ,'w': '140px'}
	,{'k':'ref_trans_account_email' ,'l': 'Referred Account Email','u': None,'w': '150px'}
        ,{'k':'ref_trans_id'    ,'l': 'Referred Trans ID'   ,'u': None  ,'w': '120px'}
        ,{'k':'ref_trans_status'        ,'l': 'Referred Trans Status'       ,'u': None    ,'w': '100px'}
        ,{'k':'ref_trans_amt'          ,'l': 'Referred Trans Amt'         ,'u': 'currency'    ,'w': '75px'}

    ]
#TODO: 'account:'inputbox& select button, currentval='$id', submiturl=url_for('referrals_for_account2')

    searchform = """
        <form method='POST' action='%s'> <!--- target is me -->
            <p><label id='search_label' for='search_input'><span>Date: </span></label>
            <input id='search_input' name='date' value='%s'>
            <button type='submit'>Search</button></p>
        </form>
    """%('/credit_grants_by_date/',rdate) #note: hardcoded url!
#(url_for('referrals_for_account2'), id)
    context = {};
    TITLE='DAILY TIPPR CREDIT ACTIVITY REPORT'; SUBTITLE= ' BY DATE';

    format = request.args.get('format','grid');
    if format == 'csv':
        return csv_out_simple(ROWS, COLS, dict(REPORTSLUG='credit_grants_by_date-v1'));
    else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE, SEARCH=searchform);




def account_detail(id='d1f5be0616ba4751a9a1a607c6175504'):
    
    id_in = request.args.get('id')
    if id_in:
       id = id_in 


    metrics = {}
    metrics['details'] = {}
   
    sql = """
        select transaction.status "status", count(distinct(transaction.id)) "transactions", sum(transaction.amount) "amount", date(min(transaction.occurrence)) "first", date(max(transaction.occurrence)) "last" from core_transaction transaction where transaction.account_id = '%(account)s' group by 1;
    """
    cols, resultset = throw_sql(sql % {'account':id},DB_PBT    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    metrics['details']['transaction_summary'] = ROWS

    sql = """
	select account.*, publisher.name "publisher_name" from core_account account, core_publisher publisher where account.publisher_id = publisher.id and account.id = '%(account)s';
    """
    cols, resultset = throw_sql(sql % {'account':id},DB_PBT    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    metrics['details']['account'] = ROWS[0]

    sql = """
        select sum(value) "total_earned" from core_credit where account_id = '%(account)s' and status='activated';
    """
    cols, resultset = throw_sql(sql % {'account':id},DB_PBT    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    metrics['details']['credits_earned'] = ROWS[0]['total_earned']

    sql = """
        select sum(value) "total_remaining" from core_credit where account_id = '%(account)s' and status='activated' and id not in (select credit_id from core_creditpayment);
    """
    cols, resultset = throw_sql(sql % {'account':id},DB_PBT    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    metrics['details']['credits_remaining'] = ROWS[0]['total_remaining']
 
    sql = """
        select sharer.account_id "referred_acct", 
                transaction.status "type", 
                count(distinct(transaction.id)) "transactions", 
                sum(transaction.amount)::float "gross",
                count(distinct(transaction.account_id)) "accounts",
		sum(transaction.amount)::float / count(distinct(transaction.id)) "spend_per_trans" 
            from core_invite sharer, core_inviteuse, core_account referred, core_transaction transaction 
            where sharer.account_id = '%(account)s' and invite_id = sharer.id and 
                transaction.account_id = core_inviteuse.account_id and core_inviteuse.account_id = referred.id 
            group by 1, transaction.status 
            order by 2 desc;
    """
    cols, resultset = throw_sql(sql % {'account':id},DB_PBT    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    metrics['referrals_table'] = ROWS

    sql = """
	select sharer.account_id "referrer_account", to_date(to_char(referred.date_joined,'MM-YYYY'),'MM-YYYY') "month", count(distinct(referred.id)) "accounts", count(distinct(transaction.id)) "transactions", sum(transaction.amount) "spend", sum(transaction.amount) / count(distinct(referred.id)) "spend_per_acct" from core_invite sharer, core_inviteuse, core_account referred, core_transaction transaction where sharer.account_id = '%(account)s' and invite_id = sharer.id and transaction.account_id = core_inviteuse.account_id and core_inviteuse.account_id = referred.id and transaction.status = 'completed' group by 1,2 order by 1,2;
    """
    cols, resultset = throw_sql(sql % {'account':id},DB_PBT    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    metrics['monthly_referrals_table'] = ROWS

    
    context = {};
    TITLE='REFERRED TRANSACTION REPORT'; SUBTITLE= ' BY STATUS';

    return render_template("account_metrics.html", **metrics);


def dealcats(id='test'):
    if id == None:
        if request.method == 'POST':
            id = request.form['id']
        if id == '':
            raise Exception("empty id") 
    if id == 'test':
        id = 'dd8506870eb34167a489fd59dcda316c'  
  
#    pub_name = sql_simple_fetchrow("select title from core_publisher where id = '%s';"%id)[0];

    hash_publishers = sql_pull_lookup(
	'select id, title \
		from core_publisher \
		order by title;');

#    pub_name = hash_publishers[id]
    sql = """
        select channel.name, advertiser.category_id, count(distinct(offer.id)) "offer count", 
		array_agg(distinct(offer.id)) "offers_list", 
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
    cols, resultset = throw_sql(sql % {'account':id},DB_PBT    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    for row in ROWS:
	params = []
	params.append("filter_pretty="+"for channel %s, category %s" % (row['name'],row['category_id']))
	for x in row['offers_list']: 
		params.append('offer='+ x) 
	row['link'] = {'linkto':url_for('offers_detail'), 'params': params, 'show':row['offer count']} #set up link to orders detail
    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
#TODO: add in tool-tip, and link-logic.
        {'k':'name'        		,'l': 'Channel '    ,'u': None            ,'w': '200px'}   #linkto: 
        ,{'k':'category_id'             ,'l': 'Category'    ,'u': None            ,'w': '140px'}
        ,{'k':'link'        		,'l': '# offers'        ,'u': 'linkto'        ,'w': '50px'}
        ,{'k':'gross revenue'        	,'l': 'ttl gross $ revenue'    ,'u': 'currency'    ,'w': '80px'}
        ,{'k':'gross revenue/offer'     ,'l': 'gross $/offer'        ,'u': 'currency'    ,'w': '70px'}
    ]
    
    GROWS = []
    for row in ROWS:
	GROWS.extend({'c': [{'v': c} for c in row]})

#    GROWS = [{'c':[{'v':x},...]},...]
	
    GCOLS = [ 
	{'id':'name'			,'label': 'Channel'	,'type':'string'}
	,{'id':'category_id'		,'label': 'Category'	,'type':'string'}
	,{'id':'offer count'		,'label': '# offers'	,'type':'number'}
	,{'id':'gross revenue'		,'label': 'ttl gross $ revenue'	,'type':'number'}
	,{'id':'gross revenue/offer'	,'label': 'gross $/offer'	,'type':'number'}
    ]
#	,{'id':''		,'label': ''	,'type':''}

    SELECTOR = {
	'list':		hash_publishers	
	,'current':	id
	,'submit_url':	'/pubreps/dealcats/'
	,'name':	'Publisher'
	}

    context = {};
    TITLE='OFFER CATEGORY REPORT'; #SUBTITLE='(for %s)'%pub_name;

    format = request.args.get('format','grid');
    if format == 'csv':
	return csv_out_simple(ROWS,COLS,dict(REPORTSLUG='offer_cat-v1'));	
    if format == 'gjson':
	return gjson_response(data_to_gjson(ROWS,COLS))
    if format == 'djson':
	return djson_out(ROWS,COLS);
    else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, #SUBTITLE=SUBTITLE,
		  SELECTOR=SELECTOR, BACK=url_for('listpubs') );

def agent_sales(yyyymm = None):
	"""
		Report of Agent Sales for the Month
	"""
	month = datetime.date(2011, 1, 1) #starting month that we have data for
	pick_month = []; 
	today = datetime.date.today()
	todaykey = today.strftime('%Y-%m')
	while month < today:
		monthkey = month.strftime( '%Y-%m')
		monthvalue = month.strftime( '%B %Y') + (
			" -- MTD" if monthkey == todaykey else "")
		pick_month.append((monthkey,monthvalue))
		month = month + datetime.timedelta(days=31) 
		month = month - datetime.timedelta(month.day - 1) #go to first of month 

	yyyymm = yyyymm or todaykey #pick current as default	
	SELECTOR = {
		'list':		pick_month
		,'current': 	yyyymm
		,'submit_url': '/agent_sales/'
		,'name':	'Month'
	}
#TODO fix to use array_agg(offer.id)!!
	sql = """
	select 		/*date(date_trunc('month',offer.start_date)) "Deal Start Month",*/ account.fullname "Agent", 
			case when offer.upstream_source = 'tom' THEN 'TOM' else 'PBT' end "source", 
			array_agg(distinct(offer.id)) "offers_list", 
			count(distinct(offer.id)) "Offers", count(distinct(item.id)) "vouchers", 
			round(avg(offer.processing_fee_percentage * 100),1)/100::float "Avg CC", sum(item.amount)::float "Item.Gross", 
			sum(product.payout)::float "Merchant Payout", sum(product.marketplace_cost)::float "TOM Payout",
			round(sum(offer.processing_fee_percentage * item.amount),2)::float "CC fees", 
			case when offer.upstream_source = 'tom' then 
				(sum(product.price) - sum(product.marketplace_cost))::float 
				else (sum(product.price) - sum(product.payout))::float end "Net", 
			coalesce(sum(returns.amount),0.00)::float "Returns/Voids", 
			round((coalesce(sum(returns.amount),0.00)/sum(item.amount)) * 100,1)/100::float "returns" 
		from core_offer offer, core_publisher publisher, core_account account, core_agent agent, 
			core_transaction transaction, core_item item, core_product product, core_voucher voucher 
			left join core_item returns on (returns.id = voucher.item_ptr_id and 
				(voucher.status = 'voided' or voucher.status = 'invalidated')) 
		where voucher.product_id = product.id and transaction.id = item.transaction_id and offer.agent_id = agent.id
			and agent.account_id = account.id and publisher.id = offer.publisher_id and item.offer_id = offer.id
			and item.id = voucher.item_ptr_id and date(date_trunc('month',offer.start_date)) = '%(month)s' 
			and offer.status = 'closed' 
		group by 1,2,offer.upstream_source 
		order by 1,2 desc;
	"""
	cols, resultset = throw_sql(sql  % {'month':yyyymm+'-01'}, DB_PBT)
	ROWS = [dict(zip(cols,row)) for row in resultset]
	for row in ROWS:
		params = []
		params.append("filter_pretty="+"for %s in %s" % (row['Agent'], yyyymm+'-01'))
		for x in row['offers_list']: 
			params.append('offer='+ x) 
		row['link'] = {'linkto':url_for('offers_detail'), 'params': params, 'show':row['Offers']} #set up link to orders detail
	COLS = [#k:field_name		l:title(\n)			u:formatting		w:width
	#	{'k':'Deal Start Month'	,'l':'Deal Start Month'		,'u': None		,'w': ''}
		{'k':'Agent'		,'l':'Agent'			,'u': None		,'w': '100px'}
		,{'k':'source'		,'l':'source'			,'u': None		,'w': '50px'}
		,{'k':'link'		,'l':'Offers'			,'u': 'linkto'		,'w': '50px'}
		,{'k':'vouchers'	,'l':'vouchers'			,'u': 'integer'		,'w': '60px'}
		,{'k':'Avg CC'		,'l':'Avg CC%'			,'u': 'percent'		,'w': '60px'}
		,{'k':'Item.Gross'	,'l':'Item.Gross'		,'u': 'currency'	,'w': '80px'}
		,{'k':'Merchant Payout'	,'l':'Merchant Payout'		,'u': 'currency'	,'w': '90px'}
		,{'k':'TOM Payout'	,'l':'TOM Payout'		,'u': 'currency'	,'w': '90px'}
		,{'k':'CC fees'		,'l':'CC fees'			,'u': 'currency'	,'w': '70px'}
		,{'k':'Net'		,'l':'Net'			,'u': 'currency'	,'w': '90px'}
		,{'k':'Returns/Voids'	,'l':'Returns & Voids'		,'u': 'currency'	,'w': '60px'}
		,{'k':'returns'		,'l':'Returns %'		,'u': 'percent'		,'w': '40px'}
	]	
	TITLE='FANFORCE AGENT SALES REPORT'; #SUBTITLE='(for %s)'%pick_month[yyyymm]

    	format = request.args.get('format','grid');
    	if format == 'csv':
		return csv_out_simple(ROWS,COLS,dict(REPORTSLUG='agent_sales-v1'));	
    	else: #assume format == 'grid':
		return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, #SUBTITLE=SUBTITLE, 
			SELECTOR=SELECTOR);

def tom_breakdown(offer_id='1'):
        """
                Show detailed metrics on a specific offer
        """

        offer_in = request.args.get('offer_id')
        if offer_in:
           offer_id = offer_in


        TITLE='TOM BREAKDOWN REPORT'
        metrics = {}
        sql = """
                select offer.name "name", offer.id "id", offer.available_start_date, offer.available_end_date from marketplace_offer offer where offer.status NOT in ('draft','archived') order by offer.available_start_date desc limit 5000;
        """
        sql = sql % {}
        cols, resultset = throw_sql(sql, DB_TOM)
        offer_list = []
        for row in resultset:
                offer_list.append([row[0] + " - (" + str(row[2]) + " - " + str(row[3]) + ")",row[1]])

        metrics['offer_list'] = offer_list

        sql = """
                 select product.id "product", agency.name "agency", offer.headline "headline", advertiser.name "advertiser", offer.available_start_date, offer.available_end_date, offer.processing_fee_percentage, offer.marketplace_commission, product.title, product.price, product.ask_price, product.marketplace_ask, product.advertiser_return from marketplace_product product, marketplace_agency agency, marketplace_offer offer, marketplace_advertiser advertiser where offer.agency_id = agency.id and offer.id = product.offer_id and advertiser.id = offer.advertiser_id and offer.id = '%(offer_id)s';
        """
        sql = sql % {'offer_id':offer_id}
        cols, resultset = throw_sql(sql, DB_TOM)
        ROWS = [dict(zip(cols,row)) for row in resultset]
        metrics['name'] = None
        if len(ROWS) == 0:
                metrics['offer_products'] = {}
		return render_template("tom_breakdown.html", **metrics);
        metrics['available_start_date'] = ROWS[0]['available_start_date']
        metrics['available_end_date'] = ROWS[0]['available_end_date']
        metrics['headline'] = ROWS[0]['headline']
        metrics['advertiser'] = ROWS[0]['advertiser']
        metrics['processing_fee_percentage'] = ROWS[0]['processing_fee_percentage']
        metrics['marketplace_commission'] = ROWS[0]['marketplace_commission']
	metrics['offer_products'] = {}
	for row in ROWS:
	  metrics['offer_products'][row['product']] = {}
          metrics['offer_products'][row['product']]['title'] = row['title']
	  metrics['offer_products'][row['product']]['product_price'] = row['price']
	  metrics['offer_products'][row['product']]['product_ask_price'] = row['ask_price']
	  metrics['offer_products'][row['product']]['product_marketplace_ask'] = row['marketplace_ask']
	  metrics['offer_products'][row['product']]['advertiser_return'] = row['advertiser_return']	


        sql = """
	select promotion.id, publisher.name "publisher_name", promotion.start_date, promotion.end_date, promotion.status, product.title, inventory.maximum_quantity, inventory.bid_price, inventory.marketplace_bid, inventory.bid_price - inventory.marketplace_bid "tom_fee", count(voucher.*) "total_sold" from marketplace_product product, marketplace_promotion promotion, marketplace_promotioninventory inventory, marketplace_publisher publisher, marketplace_voucher voucher where promotion.id = inventory.promotion_id and voucher.status = 'assigned' and voucher.product_id = inventory.id and promotion.publisher_id = publisher.id and product.id = inventory.product_id and promotion.offer_id =  '%(offer_id)s' group by 1,2,3,4,5,6,7,8,9,10; 
	"""
        sql = sql % {'offer_id':offer_id}
        cols, resultset = throw_sql(sql, DB_TOM)
        ROWS = [dict(zip(cols,row)) for row in resultset]
        metrics['promotions'] = ROWS



        return render_template("tom_breakdown.html", **metrics);


def offer_metrics(offer_id='1'):
	"""
		Show detailed metrics on a specific offer
	"""

        offer_in = request.args.get('offer_id')
        if offer_in:
           offer_id = offer_in 
	
	TITLE='OFFER METRICS REPORT'
	metrics = {} 
	sql = """
		select offer.headline "name", offer.id "id", publisher.name, offer.start_date from core_offer offer, core_publisher publisher where offer.status in ('published','closed') and publisher.id = offer.publisher_id order by offer.end_date desc limit 5000;
	"""
	sql = sql % {}
	cols, resultset = throw_sql(sql, DB_PBT)
	offer_list = []
	for row in resultset:
		offer_list.append([row[0] + " - " + str(row[2]) + " ( " + str(row[3]) + " )",row[1]])

	metrics['offer_list'] = offer_list
	
	sql = """
		 select publisher.name "publisher", offer.headline "name", offer.start_date "start_date", offer.end_date "end_date", count(distinct(transaction.account_id)) "unique_buyers", sum(item.amount)::float "gross", avg(transaction.amount)::float "avg_order_amount", count(distinct(item.id)) "voucher_count", (count(distinct(item.id))::float/count(distinct(transaction.id))) "avg_order_qty" from core_offer offer, core_item item, core_transaction transaction, core_publisher publisher where item.offer_id = offer.id and offer.publisher_id = publisher.id and item.transaction_id = transaction.id and offer.id = '%(offer_id)s' group by 1,2,3,4; 
	"""
	sql = sql % {'offer_id':offer_id}
	cols, resultset = throw_sql(sql, DB_PBT)
        ROWS = [dict(zip(cols,row)) for row in resultset]	
	metrics['name'] = None	
	if len(ROWS) == 0:
		return render_template("offer_metrics.html", **metrics);
	metrics['start_date'] = ROWS[0]['start_date']
	metrics['end_date'] = ROWS[0]['end_date']	
	metrics['name'] = ROWS[0]['name']
	metrics['unique_buyers'] = ROWS[0]['unique_buyers']
	metrics['gross_sales'] = ROWS[0]['gross']
	metrics['avg_order_amount'] = ROWS[0]['avg_order_amount']
	metrics['avg_order_qty'] = ROWS[0]['avg_order_qty']
	metrics['voucher_count'] = ROWS[0]['voucher_count']
	metrics['publisher'] = ROWS[0]['publisher']

	sql = """
	select payment._polymorphic_identity "ptype", sum(payment.amount)::float "amount" from core_payment payment where payment.transaction_id in (select transaction.id from core_transaction transaction, core_offer offer, core_item item where offer.id = '%(offer_id)s' and offer.id = item.offer_id and item.transaction_id = transaction.id) group by 1;
	"""
        sql = sql % {'offer_id':offer_id}
        cols, resultset = throw_sql(sql, DB_PBT)
        ROWS = [dict(zip(cols,row)) for row in resultset]
        metrics['payments'] = {}
	for row in ROWS:
	  metrics['payments'][row['ptype']] = row['amount']
	sql = """
	select name "name", total_trans "trans_count", count(account) "users" from (select offer.name "name",  transaction.account_id "account", count(distinct(acct_trans.id)) "total_trans" from core_offer offer, core_transaction transaction left join core_transaction acct_trans on (transaction.account_id = acct_trans.account_id and acct_trans.occurrence <= transaction.occurrence and acct_trans.id != transaction.id), core_item item where offer.id = '%(offer_id)s' and offer.id = item.offer_id and item.transaction_id = transaction.id group by 1,2) as cust_behavior group by 1,2;
	"""
 
        sql = sql % {'offer_id':offer_id}
        cols, resultset = throw_sql(sql, DB_PBT)
        ROWS = [dict(zip(cols,row)) for row in resultset]
        metrics['prior_buyers'] = {}
	metrics['prior_buyers']['0 Purchases'] = 0
	metrics['prior_buyers']['1 Purchase'] = 0
	metrics['prior_buyers']['2-5 Purchases'] = 0
 	metrics['prior_buyers']['6-10 Purchases'] = 0
	metrics['prior_buyers']['10+ Purchases'] = 0
        for row in ROWS:
          if row['trans_count'] == 0:
                metrics['prior_buyers']['0 Purchases'] += row['users']
          if row['trans_count'] == 1:
		metrics['prior_buyers']['1 Purchase'] += row['users']
	  if row['trans_count'] > 1 and row['trans_count'] <= 5:
		metrics['prior_buyers']['2-5 Purchases'] += row['users']
	  if row['trans_count'] > 5 and row['trans_count'] <= 10:
		metrics['prior_buyers']['6-10 Purchases'] += row['users']
	  if row['trans_count'] > 10:
		metrics['prior_buyers']['10+ Purchases'] += row['users']

        sql = """
        select name "name", total_trans "trans_count", count(account) "users" from (select offer.name "name",  transaction.account_id "account", count(distinct(acct_trans.id)) "total_trans" from core_offer offer, core_transaction transaction left join core_transaction acct_trans on (transaction.account_id = acct_trans.account_id and acct_trans.occurrence >= transaction.occurrence and acct_trans.id != transaction.id), core_item item where offer.id = '%(offer_id)s' and offer.id = item.offer_id and item.transaction_id = transaction.id group by 1,2) as cust_behavior group by 1,2;
        """

        sql = sql % {'offer_id':offer_id}
        cols, resultset = throw_sql(sql, DB_PBT)
        ROWS = [dict(zip(cols,row)) for row in resultset]
        metrics['future_buyers'] = {}
	metrics['future_buyers']['0 Purchases'] = 0
        metrics['future_buyers']['1 Purchase'] = 0
        metrics['future_buyers']['2-5 Purchases'] = 0
        metrics['future_buyers']['6-10 Purchases'] = 0
        metrics['future_buyers']['10+ Purchases'] = 0
        for row in ROWS:
	  if row['trans_count'] == 0:
		metrics['future_buyers']['0 Purchases'] += row['users']
          if row['trans_count'] == 1:
                metrics['future_buyers']['1 Purchase'] += row['users']
          if row['trans_count'] > 1 and row['trans_count'] <= 5:
                metrics['future_buyers']['2-5 Purchases'] += row['users']
          if row['trans_count'] > 5 and row['trans_count'] <= 10:
                metrics['future_buyers']['6-10 Purchases'] += row['users']
          if row['trans_count'] > 10:
                metrics['future_buyers']['10+ Purchases'] += row['users']

	sql = """
	select referral.source "source", count(referral.*) "count" from core_referral referral, core_item item where item.transaction_id = referral.transaction_id and item.offer_id='%(offer_id)s' and campaign='Affiliate' and event='offer-purchase' group by 1; 
	"""
	sql = sql % {'offer_id':offer_id}
        cols, resultset = throw_sql(sql, DB_PBT)
        ROWS = [dict(zip(cols,row)) for row in resultset]
	metrics['affiliate_sales'] = ROWS

	sql = """
 select event "event", campaign "campaign", medium "medium",count(core_referral.*) "referral_count" from core_referral, core_transaction, core_item where core_transaction.id = core_referral.transaction_id and core_item.transaction_id = core_transaction.id and core_item.offer_id = '%(offer_id)s' group by 1,2,3;
	"""
        sql = sql % {'offer_id':offer_id}
        cols, resultset = throw_sql(sql)
        ROWS = [dict(zip(cols,row)) for row in resultset]
        metrics['sale_sources'] = ROWS


	sql = """
	select offer.name "name", count(distinct(transaction.account_id)) "unique_buyers", sum(transaction.amount)::float "gross" from core_offer offer, core_item item, core_transaction transaction, core_account account where item.offer_id = offer.id and item.transaction_id = transaction.id and transaction.account_id = account.id and account.date_joined > transaction.occurrence - interval '4 hours' and offer.id = '%(offer_id)s' group by 1;
	"""
        sql = sql % {'offer_id':offer_id}
        cols, resultset = throw_sql(sql, DB_PBT)
        ROWS = [dict(zip(cols,row)) for row in resultset]
        metrics['new_buyers'] = ROWS[0]['unique_buyers']


	return render_template("offer_metrics.html", **metrics);


def offers_detail(offers=None):
	"""
		Show detailed closed orders.
		List passed in
	"""
	offers = request.values.getlist('offer',None)
	offers = offers or ['abb65856923e4e389ae6a09709e70600','7b7c54d1a9854f8788db45df42b7d87b', '8d10df493ad74e86a70e9a4527913739','7ee676edc5564d5f9d0cdfa7d5d620fe']
	SUBTITLE = request.values.get('filter_pretty',None)
	TITLE ='OFFER DETAIL REPORT';
	sql = """
		select ag_acc.fullname agent, ad.name merchant, p.name publisher, o.status, o.start_date::varchar start_date, o.end_date::varchar end_date
				, ad.category_id category, o.headline
                                , (select count(id) from core_item where offer_id = o.id group by offer_id) qty
				, (select sum(amount)::float from core_item where offer_id= o.id group by offer_id) gross
                        from core_offer o, core_publisher p, core_advertiser ad, core_agent ag, core_account ag_acc
                                /*,core_item i */
                        where o.advertiser_id = ad.id and o.publisher_id = p.id
                                and o.agent_id = ag.id and ag.account_id = ag_acc.id
                               /* and o.status = 'closed' 
                                and o.id= i.offer_id and exists (
                                        select * from core_transaction
                                                where id = i.transaction_id and status in ('completed', 'pending')) */
				and o.id = any ('{ %(offer_list)s }')
			group by 1,2,3,o.id, ad.category_id;
	"""
	"""
select ag_acc.fullname agent, ad.name merchant, p.name publisher, o.status, o.start_date::varchar start_date, o.end_date::varchar end_date
                                , ad.category_id category, o.headline
                                , (select count(id) from core_item where offer_id = o.id group by offer_id) qty
                                , (select sum(amount)::float from core_item where offer_id= o.id group by offer_id) gross
                        from core_offer o, core_publisher p, core_advertiser ad, 
				left join core_agent ag on o.agent_id = ag.id join core_account ag_acc on ag.account_id = ag_acc.id
                                /*,core_item i */
                        where o.advertiser_id = ad.id and o.publisher_id = p.id
                                /*and o.agent_id = ag.id and ag.account_id = ag_acc.id*/
                               /* and o.status = 'closed'
                                and o.id= i.offer_id and exists (
                                        select * from core_transaction
                                                where id = i.transaction_id and status in ('completed', 'pending')) */
	"""
	sql = """
select ag_acc.fullname agent, ad.name merchant, p.name publisher, o.status, o.start_date::varchar start_date, o.end_date::varchar end_date
                                , ad.category_id category, o.headline
                                , (select count(id) from core_item where offer_id = o.id group by offer_id) qty
                                , (select sum(amount)::float from core_item where offer_id= o.id group by offer_id) gross
                        from core_publisher p, core_advertiser ad, 
                                core_offer o left join core_agent ag on o.agent_id = ag.id left join core_account ag_acc on ag.account_id = ag_acc.id
                                /*,core_item i */
                        where o.advertiser_id = ad.id and o.publisher_id = p.id and o.id = any ('{ %(offer_list)s }');
	"""


	#expects order_list to be string,string,string -- not quoted.
	#todo: add the numerics: voucher#, net, gross, etc.
	sql = sql % {'offer_list':','.join(offers)}
	cols, resultset = throw_sql(sql, DB_PBT)
	ROWS = [dict(zip(cols,row)) for row in resultset]
        COLS = [#k:field_name           l:title(\n)                     u:formatting            w:width
               {'k':'agent' 		,'l':'agent'         ,'u': None              ,'w': '70px'}
               ,{'k':'merchant' 	,'l':'merchant'      ,'u': None              ,'w': '130px'}
               ,{'k':'publisher' 	,'l':'publisher'     ,'u': None              ,'w': '90px'}
		,{'k':'status'		, 'l':'status'		,'u': None		,'w': '70px'}
               ,{'k':'start_date' 	,'l':'start_date'   ,'u': 'date'              ,'w': '80px'}
               ,{'k':'end_date' 	,'l':'end_date'      ,'u': 'date'              ,'w': '80px'}
               ,{'k':'category' 	,'l':'category'      ,'u': None              ,'w': '110px'}
               ,{'k':'headline' 	,'l':'headline'      ,'u': None              ,'w': '170px'}
               ,{'k':'qty' 		,'l':'qty'           ,'u': 'integer'              ,'w': '40px'}
               ,{'k':'gross' 		,'l':'gross'         ,'u': 'currency'              ,'w': '60px'}
	]
    	format = request.args.get('format','grid');
    	if format == 'csv':
		return csv_out_simple(ROWS,COLS,dict(REPORTSLUG='offers-detail'));	
    	else: #assume format == 'grid':
		return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE);

def engagement(id = 'test'):
	"""
		Customer engagement Dashboard (for Publisher)
	"""
    	if id == None:
        	if request.method == 'POST':
			id = request.form['id']
	if id == '':
		raise Exception("empty id")
	if id == 'test':
		id = 'dd8506870eb34167a489fd59dcda316c'

#    pub_name = sql_simple_fetchrow("select title from core_publisher where id = '%s';"%id)[0];

	hash_publishers = sql_pull_lookup('select id, title from core_publisher;', DB_PBT);

#	pub_name = hash_publishers[id]


	{'Total Subscribers' :	
		"""
	select core_subscription.status, count(s.id) 
		from core_account, core_subscription s 
		where publisher_id = '%s' and s.account_id = core_account.id
		group by 1;
		"""
	}







	"""
	select 
	select fullname 
		from core_emailaddress e, core_account a 
		where a.id = e.account_id and a.status = 'active' and a.superuser and e.email='%s';

	jeremy.elliott@tippr.com';

	if sql_simple_fetchrow(sql % g.user):
		"SuperUser"
	else: 
		"Not!!"

ideas: @whitelist("david.tobias","aaron.krill")
	@req_superuser()
	@restrict_to_group(FINANCE_VIPS,BIG_VIPS,...) from settings.py
	"""






	return "zx"+g.user+"x"


