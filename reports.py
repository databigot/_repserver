from sqlhelpers import *
from flask import Flask, url_for, render_template, g, session, request, redirect, abort

from utils import csv_out
#from flask import Response
#import csv
#from cStringIO import StringIO

def referrals(id='test'):
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

    format = request.args.get('format','grid');
    if format == 'csv':
	return csv_out(COLS=COLS, ROWS=ROWS, REPORTSLUG='reffered-v1');	
    else: #assume format == 'grid':
    	return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE, SEARCH=searchform);


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
    cols, resultset = throw_sql(sql % {'account':id}    ); ##bind in the input params; and run it.
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
	return csv_out(COLS=COLS, ROWS=ROWS, REPORTSLUG='offer_cat-v1');	
    if format == 'gjson':
	return gjson_out(COLS=COLS, ROWS=ROWS);
    if format == 'djson':
	return djson_out(COLS=COLS, ROWS=ROWS);
    else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, #SUBTITLE=SUBTITLE,
		  SELECTOR=SELECTOR, BACK=url_for('listpubs') );

def agent_sales(yyyymm = None):
	"""
	"""
	pick_month = [('2011-01','January 2011')
			,('2011-02','Febuary 2011')
			,('2011-03','March 2011')
			,('2011-04','April 2011')
			,('2011-05','May 2011')
			,('2011-06','June 2011')
			,('2011-07','July 2011')
			,('2011-08','August 2011') 
			,('2011-09','September 2011') 
			,('2011-10','October 2011') 
			,('2011-11','November 2011') 
			,('2011-12','December 2011') 
			,('2012-01','January 2012 - partial month to date')]
	yyyymm = yyyymm or '2012-01';	
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
	cols, resultset = throw_sql(sql  % {'month':yyyymm+'-01'})
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
		return csv_out(COLS=COLS, ROWS=ROWS, REPORTSLUG='agent_sales-v1');	
    	else: #assume format == 'grid':
		return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, #SUBTITLE=SUBTITLE, 
			SELECTOR=SELECTOR);

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
	cols, resultset = throw_sql(sql)
	ROWS = [dict(zip(cols,row)) for row in resultset]
        COLS = [#k:field_name           l:title(\n)                     u:formatting            w:width
               {'k':'agent' 	,'l':'agent'         ,'u': None              ,'w': '70px'}
               ,{'k':'merchant' 	,'l':'merchant'      ,'u': None              ,'w': '130px'}
               ,{'k':'publisher' ,'l':'publisher'     ,'u': None              ,'w': '90px'}
		,{'k':'status', 'l':'status'		,'u': None		,'w': '70px'}
               ,{'k':'start_date' ,'l':'start_date'   ,'u': 'date'              ,'w': '80px'}
               ,{'k':'end_date' 	,'l':'end_date'      ,'u': 'date'              ,'w': '80px'}
               ,{'k':'category' 	,'l':'category'      ,'u': None              ,'w': '110px'}
               ,{'k':'headline' 	,'l':'headline'      ,'u': None              ,'w': '170px'}
               ,{'k':'qty' 	,'l':'qty'           ,'u': 'integer'              ,'w': '40px'}
               ,{'k':'gross' 	,'l':'gross'         ,'u': 'currency'              ,'w': '60px'}
	]
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

	hash_publishers = sql_pull_lookup('select id, title from core_publisher;');

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


