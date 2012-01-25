from sqlhelpers import *
from flask import Flask, url_for, render_template, g, session, request, redirect, abort

from utils import csv_out
#from flask import Response
#import csv
#from cStringIO import StringIO
def credits_by_date(rdate=''):
    if request.method == 'POST':
            rdate = request.form['rdate']
    if request.method == 'GET':
            rdate = request.values['rdate']
    if rdate == '' or rdate == None:
            raise Exception("empty rdate passed in")

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
    cols, resultset = throw_sql(sql % {'rdate':rdate}    ); ##bind in the input params; and run it.
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
    """%('/referrals_by_date/',rdate) #note: hardcoded url!
#(url_for('referrals_for_account2'), id)
    context = {};
    TITLE='DAILY TIPPR CREDIT ACTIVITY REPORT'; SUBTITLE= ' BY DATE';

    format = request.args.get('format','grid');
    if format == 'csv':
        return csv_out(COLS=COLS, ROWS=ROWS, REPORTSLUG='credits_by_date-v1');
    else: #assume format == 'grid':
        return render_template("report2.html", COLS=COLS, ROWS=ROWS, TITLE=TITLE, SUBTITLE=SUBTITLE, SEARCH=searchform);




def account_detail(id='test'):
    
    if request.method == 'POST':
            id = request.form['id']
    if request.method == 'GET':
            id = request.values['id']
    if id == '':
            raise Exception("empty id")
    if id == 'test':
        id = '75514bb16add426bb4b8203c4354d893'

    metrics = {}
    metrics['details'] = {}
   
    sql = """
        select transaction.status "status", count(distinct(transaction.id)) "transactions", sum(transaction.amount) "amount", date(min(transaction.occurrence)) "first", date(max(transaction.occurrence)) "last" from core_transaction transaction where transaction.account_id = '%(account)s' group by 1;
    """
    cols, resultset = throw_sql(sql % {'account':id}    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    metrics['details']['transaction_summary'] = ROWS

    sql = """
	select account.*, publisher.name "publisher_name" from core_account account, core_publisher publisher where account.publisher_id = publisher.id and account.id = '%(account)s';
    """
    cols, resultset = throw_sql(sql % {'account':id}    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    metrics['details']['account'] = ROWS[0]

    sql = """
        select sum(value) "total_earned" from core_credit where account_id = '%(account)s' and status='activated';
    """
    cols, resultset = throw_sql(sql % {'account':id}    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    metrics['details']['credits_earned'] = ROWS[0]['total_earned']

    sql = """
        select sum(value) "total_remaining" from core_credit where account_id = '%(account)s' and status='activated' and id not in (select credit_id from core_creditpayment);
    """
    cols, resultset = throw_sql(sql % {'account':id}    ); ##bind in the input params; and run it.
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
    cols, resultset = throw_sql(sql % {'account':id}    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    metrics['referrals_table'] = ROWS

    sql = """
	select sharer.account_id "referrer_account", to_date(to_char(referred.date_joined,'MM-YYYY'),'MM-YYYY') "month", count(distinct(referred.id)) "accounts", count(distinct(transaction.id)) "transactions", sum(transaction.amount) "spend", sum(transaction.amount) / count(distinct(referred.id)) "spend_per_acct" from core_invite sharer, core_inviteuse, core_account referred, core_transaction transaction where sharer.account_id = '%(account)s' and invite_id = sharer.id and transaction.account_id = core_inviteuse.account_id and core_inviteuse.account_id = referred.id and transaction.status = 'completed' group by 1,2 order by 1,2;
    """
    cols, resultset = throw_sql(sql % {'account':id}    ); ##bind in the input params; and run it.
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
    cols, resultset = throw_sql(sql % {'account':id}    ); ##bind in the input params; and run it.
    ROWS = [dict(zip(cols,row)) for row in resultset]
    for row in ROWS:
	params = []
	params.append("filter_pretty="+"for channel %s, category %s" % (row['name'],row['category_id']))
	for x in row['offers_list']: 
		params.append('offer='+ x) 
	row['link'] = {'linkto':url_for('offers_detail'), 'params': params, 'show':row['name']} #set up link to orders detail
    COLS = [#k:field_name            l:title(\n)                        u:formatting        w:width
#TODO: add in tool-tip, and link-logic.
        {'k':'link'        		,'l': 'Channel '    ,'u': 'linkto'            ,'w': '200px'}   #linkto: 
        ,{'k':'category_id'             ,'l': 'Category'    ,'u': None            ,'w': '130px'}
        ,{'k':'offer count'        	,'l': '# offers'        ,'u': 'integer'        ,'w': '120px'}
        ,{'k':'gross revenue'        	,'l': 'ttl gross $ revenue'    ,'u': 'currency'    ,'w': '130px'}
        ,{'k':'gross revenue/offer'     ,'l': 'gross $/offer'        ,'u': 'currency'    ,'w': '120px'}
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
		row['link'] = {'linkto':url_for('offers_detail'), 'params': params, 'show':row['Agent']} #set up link to orders detail
	COLS = [#k:field_name		l:title(\n)			u:formatting		w:width
	#	{'k':'Deal Start Month'	,'l':'Deal Start Month'		,'u': None		,'w': ''}
		{'k':'link'		,'l':'Agent'			,'u': 'linkto'		,'w': '100px'}
		,{'k':'source'		,'l':'source'			,'u': None		,'w': '80px'}
		,{'k':'Offers'		,'l':'Offers'			,'u': 'integer'		,'w': '50px'}
		,{'k':'vouchers'	,'l':'vouchers'			,'u': 'integer'		,'w': '60px'}
		,{'k':'Avg CC'		,'l':'Avg CC%'			,'u': 'percent'		,'w': '60px'}
		,{'k':'Item.Gross'	,'l':'Item.Gross'		,'u': 'currency'	,'w': '80px'}
		,{'k':'Merchant Payout'	,'l':'Merchant Payout'		,'u': 'currency'	,'w': '90px'}
		,{'k':'TOM Payout'	,'l':'TOM Payout'		,'u': 'currency'	,'w': '90px'}
		,{'k':'CC fees'		,'l':'CC fees'			,'u': 'currency'	,'w': '80px'}
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
def offer_metrics(offer_id=''):
	"""
		Show detailed metrics on a specific offer
	"""

        if offer_id == '':
	  if request.method == 'POST':
            offer_id = request.form['offer_id']
          if request.method == 'GET':
            offer_id = request.values['offer_id']

          if offer_id == '' or offer_id == None:
            raise Exception("empty offer_id passed in")
	
	TITLE='OFFER METRICS REPORT'
	metrics = {} 
	sql = """
		select offer.headline "name", offer.id "id" from core_offer offer where end_date < now() order by end_date desc limit 500;
	"""
	sql = sql % {}
	cols, resultset = throw_sql(sql)
	offer_list = []
	for row in resultset:
		offer_list.append([row[0],row[1]])
	metrics['offer_list'] = offer_list
	
	sql = """
		 select offer.headline "name", offer.start_date "start_date", offer.end_date "end_date", count(distinct(transaction.account_id)) "unique_buyers", sum(transaction.amount)::float "gross", avg(transaction.amount)::float "avg_order_amount", (count(distinct(item.id))::float/count(distinct(transaction.id))) "avg_order_qty" from core_offer offer, core_item item, core_transaction transaction where item.offer_id = offer.id and item.transaction_id = transaction.id and offer.id = '%(offer_id)s' group by 1,2,3; 
	"""
	sql = sql % {'offer_id':offer_id}
	cols, resultset = throw_sql(sql)
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

	sql = """
	select offer.name "offer", payment._polymorphic_identity "ptype", sum(payment.amount)::float "amount" from  core_offer offer, core_transaction transaction, core_payment payment, core_item item where offer.id = '%(offer_id)s' and offer.id = item.offer_id and item.transaction_id = transaction.id and transaction.id = payment.transaction_id group by 1,2;
	"""
        sql = sql % {'offer_id':offer_id}
        cols, resultset = throw_sql(sql)
        ROWS = [dict(zip(cols,row)) for row in resultset]
        metrics['payments'] = {}
	for row in ROWS:
	  metrics['payments'][row['ptype']] = row['amount']
	sql = """
	select name "name", total_trans "trans_count", count(account) "users" from (select offer.name "name",  transaction.account_id "account", count(distinct(acct_trans.id)) "total_trans" from core_offer offer, core_transaction transaction left join core_transaction acct_trans on (transaction.account_id = acct_trans.account_id and acct_trans.occurrence <= transaction.occurrence and acct_trans.id != transaction.id), core_item item where offer.id = '%(offer_id)s' and offer.id = item.offer_id and item.transaction_id = transaction.id group by 1,2) as cust_behavior group by 1,2;
	"""
 
        sql = sql % {'offer_id':offer_id}
        cols, resultset = throw_sql(sql)
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
        cols, resultset = throw_sql(sql)
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
        cols, resultset = throw_sql(sql)
        ROWS = [dict(zip(cols,row)) for row in resultset]
	metrics['affiliate_sales'] = ROWS


	sql = """
	select offer.name "name", count(distinct(transaction.account_id)) "unique_buyers", sum(transaction.amount)::float "gross" from core_offer offer, core_item item, core_transaction transaction, core_account account where item.offer_id = offer.id and item.transaction_id = transaction.id and transaction.account_id = account.id and account.date_joined > transaction.occurrence - interval '4 hours' and offer.id = '%(offer_id)s' group by 1;
	"""
        sql = sql % {'offer_id':offer_id}
        cols, resultset = throw_sql(sql)
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
	TITLE ='DETAIL CLOSED OFFER REPORT';
	sql = """
		select ag_acc.fullname agent, ad.name merchant, p.name publisher, o.start_date::varchar start_date, o.end_date::varchar end_date
				, ad.category_id category, o.headline
                                , count(i.id) qty, sum(i.amount)::float gross
                        from core_offer o, core_publisher p, core_advertiser ad, core_agent ag, core_account ag_acc
                                ,core_item i
                        where o.advertiser_id = ad.id and o.publisher_id = p.id
                                and o.agent_id = ag.id and ag.account_id = ag_acc.id
                                and o.status = 'closed'
                                and o.id= i.offer_id and exists (
                                        select * from core_transaction
                                                where id = i.transaction_id and status in ('completed', 'pending'))
				and o.id = any ('{ %(offer_list)s }')
			group by 1,2,3,4,5,6,7;
	"""
	#expects order_list to be string,string,string -- not quoted.
	#todo: add the numerics: voucher#, net, gross, etc.
	sql = sql % {'offer_list':','.join(offers)}
	cols, resultset = throw_sql(sql)
	ROWS = [dict(zip(cols,row)) for row in resultset]
        COLS = [#k:field_name           l:title(\n)                     u:formatting            w:width
               {'k':'agent' 	,'l':'agent'         ,'u': None              ,'w': '70px'}
               ,{'k':'merchant' 	,'l':'merchant'      ,'u': None              ,'w': '140px'}
               ,{'k':'publisher' ,'l':'publisher'     ,'u': None              ,'w': '60px'}
               ,{'k':'start_date' ,'l':'start_date'   ,'u': 'date'              ,'w': '80px'}
               ,{'k':'end_date' 	,'l':'end_date'      ,'u': 'date'              ,'w': '80px'}
               ,{'k':'category' 	,'l':'category'      ,'u': None              ,'w': '140px'}
               ,{'k':'headline' 	,'l':'headline'      ,'u': None              ,'w': '170px'}
               ,{'k':'qty' 	,'l':'qty'           ,'u': 'integer'              ,'w': '50px'}
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


