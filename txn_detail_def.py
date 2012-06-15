#from jinja2 import Template
#from sqlhelpers import *
#import datetime
#import utils
#import time

from report_query_framework import *


class Q_Txn_Detail(QueryDef):
	"""
	All Completed Transactions for a given period.  Can be restricted to a publisher; also can show credits only.
	"""
	version= 1.0
	base_query = 'txn-detail-dataset'
	descript = 'A report to show Transaction Detail.'
	long_running = True

	#TODO: include local HELP argparse, also --version

	qualifiers = {#todo: include info to allow shell args or web form
		##TODO: CAN also use required:True
		##should also figure out how to handle sql-lookups, and multi-selects
		'publisher':ChoiceQualifier({
				'args'		: ('-P','--publisher')
				,'help'		:'Pick a Publisher to isolate to'
		#		,'metavar'	:'publisher'
				,'pick'		: ['225besteats', 'yollar', 'tippr', 'msn']
				,'picksql'	: sql_pull_lookup('select name, title from core_publisher order by title;',DB_PBT)
				})	#('ALL':None, string,required) 
		,'start_dt':DateQualifier({
				'args'		:('-S','--start')
				,'help'		:'Include transaction after (or on) this starting date; format is YYYYMMDD'
				})	
		,'end_dt':DateQualifier({
				'args'		:('-E','--end')
				,'help'		:'Include transactions before (or on) this ending date; format is YYYYMMDD'
				})	#(date,None) #must > start_dt, limit to <=today.  meta values= TODAY, ...
		,'credits_only'	:BooleanQualifier({
				'args'		:('-C', '--credits-only')
				,'help'		:'Show only Credits'
				})	#(bool,False) 
		}

#	def __init__(self, **kwargs):
#		super(Q_Txn_Detail,self).__init__(**kwargs)

	def qualify(self, publisher=None, start_dt='02-16-2012', end_dt='02-29-2012', credits_only=True):
		self.qualifiers["publisher"] = publisher
		self.qualifiers["start_dt"] = start_dt
		self.qualifiers["end_dt"] = end_dt
		self.qualifiers["credits_only"] = credits_only
		self.eval_query()

	def eval_query(self):
		"""
		Get detailed closed transactions (for this pubisher, period TODO).
		Maybe credits only.

		"""
		#TODO: to add channel info: go offer->channel, and ->geography, to get city (or use channel title)
		sql_offer_info = """
				SELECT o.id, p.name publisher, o.end_date::varchar promotion_end, ad.category_id category, o.headline promotion,
						 ad.name merchant, 
						(SELECT ag_acc.fullname agent 
							FROM core_account ag_acc, core_agent ag
							WHERE ag_acc.id = ag.account_id and ag.id = o.agent_id) agent
					FROM core_publisher p, core_advertiser ad, core_offer o
					WHERE o.publisher_id = p.id and o.advertiser_id = ad.id
			"""
		sql_user_info = """
				SELECT a.id, a.fullname as name, a.gender, a.birthday::DATE::VARCHAR, e.email, a.date_joined::DATE::VARCHAR, a.zipcode
					FROM core_account a, core_emailaddress e
					WHERE a.email_id = e.id
			"""
		sql_txn_info = """
				WITH v_vouchers AS (
					SELECT i.transaction_id,  max(i.offer_id) offer_id, 
							sum(1) qty, sum(i.amount) amount
						FROM core_item i, core_voucher v
						WHERE v.item_ptr_id = i.id and
							v.status in ('issued', 'purchased', 'redeemed')
					GROUP BY i.transaction_id
				)
				SELECT t.id, t.occurrence::DATE::VARCHAR, t.account_id user_id, t.amount::float txn_amount,
						v.offer_id, v.qty, v.amount::FLOAT voucher_amount,
						(SELECT sum(p.amount)::FLOAT 
							FROM core_payment p, core_creditpayment cp
							WHERE cp.payment_ptr_id = p.id and p.transaction_id = t.id) credit_amount
					FROM core_transaction t, v_vouchers v
					WHERE v.transaction_id = t.id and t.status = 'completed'
						{% if TXNS_AFTER %} and t.occurrence::DATE >= '{{ TXNS_AFTER }}' {% endif %}
						{% if TXNS_BEFORE %} and t.occurrence::DATE <= '{{ TXNS_BEFORE }}' {% endif %}
			"""
		sql_container = """
			WITH 	v_txns AS (
						{{sql_txn_info}}
					),
					v_users AS (
						{{sql_user_info}}
					),
					v_offers AS (
						{{sql_offer_info}}
					)
				{{sql_main}}
			"""
		sql_main = """
			SELECT 	t.*,
					/*id, occurrence, user_id, txn_amount, offer_id, qty, voucher_amount, ##!! credit_amount */
				u.*,
					/*id, name, gender, birthday, email, date_joined, zipcode*/
				o.*
					/*id, publisher, end_date, category, promotion, merchant*/
				FROM v_txns t, v_users u, v_offers o
				WHERE t.user_id = u.id and t.offer_id = o.id 
					{% if CREDITS %}and t.credit_amount > 0 {% endif %}  
					{% if PUB %} and o.publisher = '{{ PUB }}' {% endif %}
					{# if OFFER_LIST %} and o.id = any ('{ {{OFFER_LIST }} }') {% endif #}
				{% if LIMIT %} LIMIT {{ LIMIT }} {% endif %}
				;   	
		"""
	
		build_sql = Template(sql_container).render( #combine
			sql_main=sql_main,
			sql_txn_info=sql_txn_info, 
			sql_offer_info=sql_offer_info, 
			sql_user_info=sql_user_info) 

		build_sql = Template(build_sql).render(	#then, substitute
			LIMIT=self.limit or 0
			,TXNS_AFTER=self.qualifiers["start_dt"]
			,TXNS_BEFORE=self.qualifiers["end_dt"]
			, CREDITS=self.qualifiers["credits_only"]
			, PUB=self.qualifiers["publisher"])

			#expects offer_list to be string,string,string -- not quoted.
			#todo: add the numerics: voucher#, net, gross, etc.
		#	sql = render_template_string(build_sql, OFFER_LIST=offers, PUB=publisher)

		self.sql = build_sql

class Q_TXNPayment_Detail(QueryDef):
	"""
	All Payments for a given period.  Can be restricted to a publisher; also can show credits only.
	"""
	version= 1.0
	base_query = 'pmt-detail-dataset'
	descript = 'A report to show Transaction Payment Detail.'
	long_running = True

	#TODO: include local HELP argparse, also --version

	qualifiers = {#todo: include info to allow shell args or web form
		##TODO: CAN also use required:True
		##should also figure out how to handle sql-lookups, and multi-selects
		'publisher':	ChoiceQualifier({
				'args'		: ('-P','--publisher')
				,'help'		:'Pick a Publisher to isolate to'
		#		,'metavar'	:'publisher'
				,'pick'		: ['225besteats', 'yollar', 'tippr', 'msn']
				,'picksql'	: sql_pull_lookup("""
					SELECT name, title 
						FROM core_publisher 
						WHERE status='active' 
						ORDER BY title;"""
					,DB_PBT)
				})	#('ALL':None, string,required) 
		,'start_dt':	DateQualifier({
				'label'		:'Start Date (mm/dd/yy)'
				,'args'		:('-S','--start')
				,'help'		:'Include transaction after (or on) this starting date; format is YYYYMMDD'
				})	
		,'end_dt':	DateQualifier({
				'label'		:'End Date (mm/dd/yy)',
				'args'		:('-E','--end')
				,'help'		:'Include transactions before (or on) this ending date; format is YYYYMMDD'
				})	#(date,None) #must > start_dt, limit to <=today.  meta values= TODAY, ...
		,'credits_only'	:BooleanQualifier({
				'args'		:('-C', '--credits-only')
				,'help'		:'Show only Credits'
				})	#(bool,False) 
		}

#	def __init__(self, **kwargs):
#		super(Q_Txn_Detail,self).__init__(**kwargs)

	def OLDeval_query(self):
		"""
		Get detailed payments for  closed transactions (for this pubisher, period TODO).
		Maybe credits only.
		"""
		#TODO: to add channel info: go offer->channel, and ->geography, to get city (or use channel title)
		sql_offer_info = """
				SELECT o.id, p.name publisher, o.end_date::varchar promotion_end, ad.category_id category, o.headline promotion,
						 ad.name merchant, 
						(SELECT ag_acc.fullname agent 
							FROM core_account ag_acc, core_agent ag
							WHERE ag_acc.id = ag.account_id and ag.id = o.agent_id) agent
					FROM core_publisher p, core_advertiser ad, core_offer o
					WHERE o.publisher_id = p.id and o.advertiser_id = ad.id
					{% if PUB %} and p.name = '{{ PUB }}' {% endif %}
			"""
		sql_user_info = """
				SELECT a.id, a.fullname as name, a.gender, a.birthday::DATE::VARCHAR, e.email, a.date_joined::DATE::VARCHAR, a.zipcode
					FROM core_account a, core_emailaddress e
					WHERE a.email_id = e.id
			"""
		sql_purchase_referral = """
                        SELECT transaction_id, source deal_source, campaign deal_campaign, medium deal_medium
                                FROM core_referral
                                WHERE event ='offer-purchase'
                """
		sql_txn_info = """
				WITH v_vouchers AS (
					SELECT i.transaction_id,  max(i.offer_id) offer_id, 
							sum(1) qty, sum(i.amount) amount
						FROM core_item i, core_voucher v
						WHERE v.item_ptr_id = i.id and
							v.status in ('issued', 'purchased', 'redeemed')
					GROUP BY i.transaction_id
				)
				SELECT t.id, t.occurrence::DATE::VARCHAR txn_date, t.account_id user_id, t.amount::float txn_amount,
						v.offer_id, v.qty, v.amount::FLOAT voucher_amount
					FROM core_transaction t, v_vouchers v
					WHERE v.transaction_id = t.id and t.status = 'completed'
		"""
		sql_pmt_info = """
				SELECT id, created pmt_date, amount pmt_amount, charge_type charge_type, transaction_id 
					/*add in CREDIT|MONETARY */
					FROM core_payment p
					WHERE true {% if PMTS_AFTER %} and created::DATE >= '{{ PMTS_AFTER }}' {% endif %}
						{% if PMTS_BEFORE %} and created::DATE <= '{{ PMTS_BEFORE }}' {% endif %}
			"""
		sql_container = """
			WITH 	v_pmts AS (
						{{sql_pmt_info}}
					),
					v_txns AS (
						{{sql_txn_info}}
					),
					v_users AS (
						{{sql_user_info}}
					),
					v_offers AS (
						{{sql_offer_info}}
					)
				{{sql_main}}
			"""
		sql_main = """
			SELECT 	p.*,
					/*id, pmt_date, pmt_amount, charge_type, transaction_id */ 
			 	t.*,
					/*id, txn_date, user_id, txn_amount, offer_id, qty, voucher_amount, ##!! credit_amount */
				u.*,
					/*id, name, gender, birthday, email, date_joined, zipcode*/
				o.*
					/*id, publisher, end_date, category, promotion, merchant*/
				FROM v_pmts p, v_txns t, v_users u, v_offers o
				WHERE p.transaction_id = t.id and t.user_id = u.id and t.offer_id = o.id 
					{% if CREDITS %}and t.credit_amount > 0 {% endif %}  
					{# if OFFER_LIST %} and o.id = any ('{ {{OFFER_LIST }} }') {% endif #}
				{% if LIMIT %} LIMIT {{ LIMIT }}{% endif %}
				;   	
		"""
	
		build_sql = Template(sql_container).render( #combine
			sql_main=sql_main,
			sql_pmt_info=sql_pmt_info,
			sql_purchase_referral=sql_purchase_referral,
			sql_txn_info=sql_txn_info, 
			sql_offer_info=sql_offer_info, 
			sql_user_info=sql_user_info) 

		build_sql = Template(build_sql).render(	#then, substitute
			LIMIT=self.limit
			,PMTS_AFTER=self.qualifiers["start_dt"]
			,PMTS_BEFORE=self.qualifiers["end_dt"]
			, CREDITS=self.qualifiers["credits_only"]
			, PUB=self.qualifiers["publisher"])

			#expects offer_list to be string,string,string -- not quoted.
			#todo: add the numerics: voucher#, net, gross, etc.
		#	sql = render_template_string(build_sql, OFFER_LIST=offers, PUB=publisher)

		self.sql = build_sql

	def eval_query(self):
		"""
		Get detailed payments for  closed transactions (for this pubisher, period TODO).
		Maybe credits only.
		"""
		#TODO: to add channel info: go offer->channel, and ->geography, to get city (or use channel title)
		build_sql = """
	SELECT 
/*pmt*/	  		p.id pmt_id, p.created::DATE::VARCHAR pmt_date, p.amount::FLOAT pmt_amount, p.charge_type charge_type, p.transaction_id 
/*mpmt*/		,substring(p._polymorphic_identity from '[^.]*$') pmt_type, mp.provider gateway, mp.providerid gateway_txn_id
/*txn*/			,t.id txn_id, t.occurrence::DATE::VARCHAR txn_date, t.status txn_status, t.account_id user_id, t.amount::FLOAT txn_amount 
			,(SELECT sum(p2.amount) 
				FROM core_creditpayment cp, core_payment p2 
				WHERE cp.payment_ptr_id = p2.id and transaction_id = t.id)::FLOAT txn_credits
/*vchr*/       	        ,v.offer_id, v.qty, v.amount::FLOAT voucher_amount
/*ofr-context*/		,o.publisher, o.source, o.category, o.agency, o.agent, o.tom_source 
/*ofr*/			,o.id offer_id, o.promotion_start, o.promotion_end, o.promotion, o.merchant 
/*chnl*/		,c.name channel
/*usr*/			,u.id user_id, u.name, u.gender, u.birthday, u.email, u.date_joined, u.city, u.state, u.zipcode
        	FROM 
/*pmt*/			core_payment p 
/*mpmt*/		left outer join core_monetarypayment mp on mp.payment_ptr_id = p.id 
/*txn*/			join core_transaction t on p.transaction_id = t.id
/*chnl*/		join core_channel c on t.channel_id = c.id
/*vchr*/		left outer join (
				SELECT i.transaction_id,  max(i.offer_id) offer_id,
					      sum(1) qty, sum(i.amount) amount
					FROM core_item i, core_voucher v
					WHERE v.item_ptr_id = i.id 
						/*and v.status in ('issued', 'purchased', 'redeemed')*/
					GROUP BY i.transaction_id
				) as v on t.id = v.transaction_id
/*ofr*/			join (
				SELECT o.id, o.start_date::varchar promotion_start, o.end_date::varchar promotion_end, o.name promotion
						/*o.headline promotion*/, o.tom_source,
						case when o.upstream_source = 'tom' THEN 'TOM' else 'PBT' end "source",
						p.name publisher, ad.category_id category, ad.name merchant, 
						(SELECT ag_acc.fullname agent 
							FROM core_account ag_acc, core_agent ag
							WHERE ag_acc.id = ag.account_id and ag.id = o.agent_id) agent,
						(SELECT agency.slug
							FROM core_agency agency
							WHERE agency.id = o.agency_id) agency
					FROM core_publisher p, core_advertiser ad, core_offer o
					WHERE o.publisher_id = p.id and o.advertiser_id = ad.id
				) as o on v.offer_id = o.id		
			join (
                                SELECT a.id, a.fullname as name, a.gender, a.birthday::DATE::VARCHAR, e.email, a.date_joined::DATE::VARCHAR, 
					z.city, z.state, a.zipcode
                                        FROM core_account a, core_emailaddress e, _zip_codes z
                                        WHERE a.email_id = e.id
						and z.zipcode = a.zipcode
				) as u on t.account_id = u.id
				
        	WHERE t.status in ('completed','voided') /*and p.charge_type = 'credit'*/
			{% if PUB %} and o.publisher = '{{ PUB }}' {% endif %}
/*			{% if CREDITS %}and t.credit_amount > 0 {% endif %}  
*/			{# if OFFER_LIST %} and o.id = any ('{ {{OFFER_LIST }} }') {% endif #}
			{% if PMTS_AFTER %}and p.created::DATE >= '{{ PMTS_AFTER }}' {% endif %}
			{% if PMTS_BEFORE %} and p.created::DATE <= '{{ PMTS_BEFORE }}' {% endif %}
		/* ORDER by pmt_date asc */
		ORDER by txn_date, txn_id, pmt_date asc

		{% if LIMIT %}LIMIT {{ LIMIT }}{% endif %}
			"""

		build_sql = Template(build_sql).render(	#then, substitute
			LIMIT=self.limit
			,PMTS_AFTER=self.qualifiers["start_dt"].value_cleaned
			,PMTS_BEFORE=self.qualifiers["end_dt"].value_cleaned
			, CREDITS=self.qualifiers["credits_only"].value_cleaned
			, PUB=self.qualifiers["publisher"].value_cleaned)

			#expects offer_list to be string,string,string -- not quoted.
			#todo: add the numerics: voucher#, net, gross, etc.
		#	sql = render_template_string(build_sql, OFFER_LIST=offers, PUB=publisher)

		self.sql = build_sql

class Q_MSN_Detail(QueryDef):
	"""
	A special transaction detail report designed for Microsoft, showing school & deal source info.  Recently added ability to show non-completed transactions, and show user info.
"""	
###HISTORY------------
###3/20: added status, opened up to non-completeds, 
###	also, added user info...\

	version= 1.1
	base_query = 'msn-detail-dataset'
	descript = 'Detailed Txn report for MSN'
	long_running = True

	#TODO: include local HELP argparse, also --version

	qualifiers = {#todo: include info to allow shell args or web form
		##TODO: CAN also use required:True
		'publisher':	ChoiceQualifier({
				'args'		:('-P','--publisher')
				,'help'		:'Pick a Publisher to isolate to'
		#		,'metavar'	:'publisher'
				,'pick'		:['225besteats', 'yollar', 'tippr', 'msn']
				})	#('ALL':None, string,required) 
		,'start_dt':	DateQualifier({
				'args'		:('-S','--start')
				,'help'		:'Include transaction after (or on) this starting date; format is YYYYMMDD'
				})	
		,'end_dt':	DateQualifier({
				'args'		:('-E','--end')
				,'help'		:'Include transactions before (or on) this ending date; format is YYYYMMDD'
				})	#(date,None) #must > start_dt, limit to <=today.  meta values= TODAY, ...
#TODO:FIX		,'offer_list'	:{#?offer_list?
	#			'args'		:('-o', '--offer')
	#			,'metatype'	:'multi-choice'
	#			,'metavar'	:'0a0f12137cfb4a288542a3696e21e28c'
	#			,'help'		:'Show only these Offers'
	#			}	#(list,[]) 
		,'completed_only':BooleanQualifier({
				'args'		:('-C', '--complete-only')
				,'help'		:'Show only Completed transactions'
				})	#(bool,False) 
		}

	def qualify(self, publisher=None, start_dt='02-16-2012', end_dt='02-29-2012', offer_list=[], completed_only=True):
		self.qualifiers["publisher"] = publisher
		self.qualifiers["start_dt"] = start_dt
		self.qualifiers["end_dt"] = end_dt
		self.qualifiers["offer_list"] = offer_list
		self.qualifiers["completed_only"] = completed_only
		self.eval_query()

	def eval_query(self):
		"""
                Get detailed closed transactions (for this pubisher, period TODO).
                Maybe credits only.
		"""

        #TODO: to add channel info: go offer->channel, and ->geography, to get city (or use channel title)
		sql_offer_info = """
                        SELECT o.id offer_id, p.name publisher, o.start_date::varchar promotion_start, o.end_date::varchar promotion_end,
                                	ad.category_id category, o.headline promotion, o.name promotion_slug,
                                 	ad.name merchant, o.tom_source,
                                	(SELECT ag_acc.fullname agent
                                        	FROM core_account ag_acc, core_agent ag
                                        	WHERE ag_acc.id = ag.account_id and ag.id = o.agent_id) agent
                                FROM core_publisher p, core_advertiser ad, core_offer o
                                WHERE o.publisher_id = p.id and o.advertiser_id = ad.id
        """
		sql_user_info = """
				SELECT a.id, a.fullname as name, a.gender, a.birthday::DATE::VARCHAR, e.email, 
						a.date_joined::DATE::VARCHAR, a.zipcode
					FROM core_account a, core_emailaddress e
					WHERE a.email_id = e.id
			"""
		sql_deal_info = """
                        SELECT transaction_id, source deal_source, campaign deal_campaign, medium deal_medium
                                FROM core_referral
                                WHERE event ='offer-purchase'
                """
		sql_txn_info = """
                        WITH v_vouchers AS (
                                SELECT i.transaction_id,  max(i.offer_id) offer_id,
                                                sum(1) qty, sum(i.amount) amount
                                        FROM core_item i, core_voucher v
                                        WHERE v.item_ptr_id = i.id and
                                                v.status in ('issued', 'purchased', 'redeemed')
                                GROUP BY i.transaction_id
                        )
                        SELECT t.id transaction_id, t.occurrence::DATE::VARCHAR, t.account_id user_id, t.status status,
					t.amount::float txn_amount,
                                        v.offer_id, v.qty, v.amount::FLOAT voucher_amount, 
					(SELECT title 
						FROM core_channel
						WHERE id = t.channel_id) channel,
                                        (SELECT sum(p.amount)::FLOAT
                                                FROM core_payment p, core_creditpayment cp
                                                WHERE cp.payment_ptr_id = p.id and p.transaction_id = t.id) credit_amount
                                FROM core_transaction t, v_vouchers v
                                WHERE v.transaction_id = t.id 
					{% if COMPLETED_ONLY %} and t.status = 'completed' {% endif %}
                                        {% if TXNS_AFTER %} and t.occurrence::DATE >= '{{ TXNS_AFTER }}' {% endif %}
                                        {% if TXNS_BEFORE %} and t.occurrence::DATE <= '{{ TXNS_BEFORE }}' 
					-- ::DATE cast is trick to include the final day {% endif %} 
        """
		sql_container = """
                WITH    v_txns AS (
                                {{sql_txn_info}}
                        ),
			v_users AS (
				{{sql_user_info}}
			),
                        v_deals AS (
                                {{sql_deal_info}}
                        ),
                        v_offers AS (
                                {{sql_offer_info}}
                        )
                {{sql_main}}
        """
		sql_main = """
                SELECT  t.*,
                                /*transaction_id, occurrence, user_id, status, txn_amount, offer_id, qty, voucher_amount, channel,  credit_amount */
			u.*,
				/*id, name, gender, birthday, email, date_joined, zipcode*/
                        o.*,
                                /*offer_id, publisher, start_date, end_date, category, promotion, promotion_slug, merchant, o.tom_source*/
                        d.*
                                /*transaction_id, deal_source, deal_campaign, deal_medium*/
                        FROM v_txns t, v_users u, v_deals d, v_offers o
                        WHERE t.user_id = u.id and t.offer_id = o.offer_id and d.transaction_id = t.transaction_id
                                {% if PUB %} and o.publisher = '{{ PUB }}' {% endif %}
                                {% if OFFER_LIST %} and o.offer_id = any ('{ {{ OFFER_LIST|join(',') }} }') {% endif %}
			{% if LIMIT %} LIMIT {{ LIMIT }}{% endif %}  	
                                ;
        """

		build_sql = Template(sql_container).render( #combine
                        sql_main=sql_main,
                        sql_txn_info=sql_txn_info,
			sql_user_info=sql_user_info,
                        sql_offer_info=sql_offer_info,
                        sql_deal_info=sql_deal_info
					)

		build_sql = Template(build_sql).render( #then, substitute
			LIMIT=self.limit
                        ,TXNS_AFTER=self.qualifiers["start_dt"],
			TXNS_BEFORE=self.qualifiers["end_dt"],
			PUB=self.qualifiers["publisher"], 
			OFFER_LIST=self.qualifiers["offer_list"],
			COMPLETED_ONLY=self.qualifiers["completed_only"]
			)

        #expects order_list to be string,string,string -- not quoted.
        #todo: add the numerics: voucher#, net, gross, etc.

		self.sql = build_sql


class R_Txn_Detail(RepDef):
		"""
		All Completed Transactions for a given period.  Can be restricted to a publisher; also can show credits only. 
		"""
		require_query = Q_Txn_Detail
		name ='TRANSACTION DETAIL REPORT'
		version = 0.5
		slug= 'txn-det-rep'
		descript = "All Completed Transactions for a Period." 
		title= 'Transaction Detail Report'
		subtitle = ''
		lpp   = None

		custom_template = None

#       SUBTITLE = q_filter_pretty

        #COLS defines the COLS to output, and the details are used for various conversions, need not include all RS columns
        ##NOTE: the field_name matches the column name in the result set, without any table qualifier:
        ##       e.g. select a.x , b.x from tbl a, tbl2 b; will return two columns named x!!

		COLS_OUT = [#k:field_name           l:title(\n)             u:formatting   t!new: google-typ     w:width  	!!added x:example_text!! instead of w
		 {'k':'publisher' 	,'l':'publisher'        ,'u': None     ,'t':None	,'w':'104px' 	,'x': '225besteats'}
               	,{'k':'promotion_end' 	,'l':'promotion_end'    ,'u': 'date'   ,'t':'date'	,'w':'99px'	,'x': '01/01/2012'}
               	,{'k':'category' 	,'l':'category'     	,'u': None     ,'t':None       	,'w':'133px'	,'x': 'Health & Medicine'}
		,{'k':'merchant'	, 'l':'merchant'	,'u': None	,'t':None	,'w':'158px'	,'x': 'Medicine & Anti-Aging Clinic'}
                ,{'k':'promotion' 	,'l':'promotion'        ,'u': None     ,'t':None	,'w':'258px'	,'x': 'Chemical Peel & Microdermabrasion'}
               	,{'k':'agent' 		,'l':'agent'   		,'u': None     ,'t':None	,'w':'83px'  	,'x': 'jakob jingle-himer'}
               	,{'k':'qty' 		,'l':'qty'      	,'u': 'integer','t':'number'	,'w':'44px'     ,'x': '999'}
               	,{'k':'txn_amount' 	,'l':'amount'		,'u': 'currency','t':'number'    ,'w':'62px'      ,'x': '$10,000'}
               	,{'k':'credit_amount' 	,'l':'credits'    	,'u': 'currency','t':'number'    ,'w':'49px'      ,'x': '$10,000'}
               	,{'k':'name' 		,'l':'user_name'      	,'u': None	,'t':None        ,'w':'109px'    ,'x': 'jakob jingle-himer'}
               	,{'k':'email' 		,'l':'email'         	,'u': None	,'t':None        ,'w':'159px'   	,'x': 'able_baker@a_longaddr.com'}
               	,{'k':'zipcode' 	,'l':'zipcode'          ,'u': None	,'t':None      	,'w':'53px'	,'x': '94707'}
               	,{'k':'date_joined' 	,'l':'date_joined'      ,'u': 'date'	,'t':'date'    	,'w':'82px'	,'x': '01/01/2012'}
		]
		META = {#TODO: META data should ALWAYS be attached to the run-report!! to have an audit-trail of what generated this report.
                        # for JSON, we could have a META-block
                        # for csv file, we could have a seperate *.meta file
                        # for web-pages, there could be mouse-over or special pop-up modal
                        # for printed it should always say above the footer 
                'report': 'TRANSACTION DETAIL REPORT',
                'rpt_v' : 1.0,
                'slug'  : 'TXN-DET-REP',
                'title' : 'Transaction Detail Report',
                'subtitle': '',
                'lpp'   : None,
                'base_query': require_query.base_query,
                        #{'publisher':publisher, 'start_dt':start_dt, 'end_dt':end_dt, 'credits_only':credits_only}, 
                # ideas: incl_titles, best_width, best_height, is_use_color?, is_html_interactive? 
                # new idea: checksums (that we can't put in the csv), e.g. #rows, sum(<field>), MD5
                # other idea: profiling: it took x long for x rows, started at, finished at, against server X
		}		


class R_MSN_Detail(RepDef):
		"""
A special transaction detail report designed for Microsoft, showing school & deal source info.  Recently added ability to show non-completed transactions, and show user info.
		"""
#		req_query = 'txn_detil_dataset'
		require_query = Q_MSN_Detail
		name ='MS TRANSACTION DETAIL REPORT'
		version = 0.5
		slug= 'ms-txn-det-rep' 
		descript = "Deatiled TXN report for MSN"
		title= 'MS Transaction Detail Report'
		subtitle = ''
		lpp   = None

		custom_template = None

#       SUBTITLE = q_filter_pretty

        #COLS defines the COLS to output, and the details are used for various conversions, need not include all RS columns
        ##NOTE: the field_name matches the column name in the result set, without any table qualifier:
        ##       e.g. select a.x , b.x from tbl a, tbl2 b; will return two columns named x!!

		COLS_OUT = [#k:field_name           l:title(\n)             u:formatting   t!new: google-typ     w:width        !!added x:example_text!! instead of w
		{'k':'transaction_id'            ,'l':'transaction_id'        ,'u': None     ,'t':None   ,'w':'104px'    ,'x': '225besteats'}
		,{'k':'occurrence'      ,'l':'transaction_date'    ,'u': 'date'   ,'t':'date'   ,'w':'99px'     ,'x': '01/01/2012'}
		,{'k':'category'        ,'l':'category'         ,'u': None     ,'t':None        ,'w':'133px'    ,'x': 'Health & Medicine'}
                ,{'k':'merchant'        , 'l':'merchant'        ,'u': None      ,'t':None       ,'w':'158px'    ,'x': 'Medicine & Anti-Aging Clinic'}
                ,{'k':'promotion_start'         ,'l':'promotion_start'        ,'u': 'date'     ,'t':'date'      ,'w':'258px'    ,'x': ''}
                ,{'k':'promotion_end'   ,'l':'promotion_end'            ,'u': 'date'     ,'t':'date'    ,'w':'83px'     ,'x': ''}
                ,{'k':'promotion_slug'          ,'l':'promotion_slug'           ,'u': None      ,'t':None        ,'w':'109px'    ,'x': ''}
                ,{'k':'promotion'       ,'l':'promotion'        ,'u': None      ,'t':None        ,'w':'109px'    ,'x': ''}
                ,{'k':'offer_id'                ,'l':'promotion_id'             ,'u': None      ,'t':None        ,'w':'109px'    ,'x': ''}
                ,{'k':'channel'        ,'l':'city/channel'          ,'u': None ,'t':None       ,'w':'53px'     ,'x': ''}
                ,{'k':'qty'             ,'l':'qty'              ,'u': 'integer','t':'number'    ,'w':'44px'     ,'x': '999'}
                ,{'k':'txn_amount'      ,'l':'amount'           ,'u': 'currency','t':'number'    ,'w':'62px'      ,'x': '$10,000'}
		,{'k':'status'		,'l':'status'		,'u': None	,'t':None	,'w':'52px'	,'x': 'completed'}
                ,{'k':'credit_amount'   ,'l':'credits_used'     ,'u': 'currency','t':'number'    ,'w':'49px'      ,'x': '$10,000'}
               	,{'k':'name' 		,'l':'user_name'      	,'u': None	,'t':None        ,'w':'109px'    ,'x': 'jakob jingle-himer'}
               	,{'k':'email' 		,'l':'email'         	,'u': None	,'t':None        ,'w':'159px'   	,'x': 'able_baker@a_longaddr.com'}
               	,{'k':'zipcode' 	,'l':'zipcode'          ,'u': None	,'t':None      	,'w':'53px'	,'x': '94707'}
               	,{'k':'date_joined' 	,'l':'date_joined'      ,'u': 'date'	,'t':'date'    	,'w':'82px'	,'x': '01/01/2012'}
                ,{'k':'publisher'       ,'l':'publisher'         ,'u': None     ,'t':None        ,'w':'159px'   ,'x': 'msn'}
                ,{'k':'deal_source'     ,'l':'deal_source'       ,'u': None     ,'t':None       ,'w':'53px'     ,'x': ''}
                ,{'k':'deal_campaign'   ,'l':'deal_campaign'     ,'u': None     ,'t':None       ,'w':'82px'     ,'x': ''}
                ,{'k':'deal_medium'     ,'l':'deal_medium'      ,'u': None      ,'t':None       ,'w':'82px'     ,'x': ''}
                ,{'k':'tom_source'      ,'l':'tom_source'      ,'u': None       ,'t':None       ,'w':'82px'     ,'x': ''}
        ]

		META = {#TODO: META data should ALWAYS be attached to the run-report!! to have an audit-trail of what generated this report.
                        # for JSON, we could have a META-block
                        # for csv file, we could have a seperate *.meta file
                        # for web-pages, there could be mouse-over or special pop-up modal
                        # for printed it should always say above the footer
				'report': 'MS TRANSACTION DETAIL REPORT',
				'rpt_v' : 1.0,
                'slug'  : 'MS-TXN-DET-REP',
                'title' : 'MS Transaction Detail Report',
                'subtitle': '',
                'lpp'   : None,
                'base_query': require_query.base_query,
                # ideas: incl_titles, best_width, best_height, is_use_color?, is_html_interactive?
                # new idea: checksums (that we can't put in the csv), e.g. #rows, sum(<field>), MD5
                # other idea: profiling: it took x long for x rows, started at, finished at, against server X
        }

class R_TXNPayment_Detail(RepDef):
		"""
		"""
#		req_query = 'txn_detil_dataset'
		require_query = Q_TXNPayment_Detail
		name ='TRANSACTION PAYMENT REPORT'
		version = 0.5
		slug= 'pmt-txn-det-rep' 
		descript = "Deatiled Payment Report"
		title= 'Transaction Payment Report'
		subtitle = ''
		lpp   = None

		custom_template = None

#       SUBTITLE = q_filter_pretty

        #COLS defines the COLS to output, and the details are used for various conversions, need not include all RS columns
        ##NOTE: the field_name matches the column name in the result set, without any table qualifier:
        ##       e.g. select a.x , b.x from tbl a, tbl2 b; will return two columns named x!!

		COLS_OUT = [#k:field_name           l:title(\n)             u:formatting   t!new: google-typ     w:width        !!added x:example_text!! instead of w
#pmt#
		{'k':'pmt_id'       	,'l':'payment_id'   	,'u': None     ,'t':None	,'w':'104px'	,'x': 'adb0b478dd7e4f678f1aad19a7f07092'}
		,{'k':'pmt_date'    	,'l':'pmt_date' 	,'u': 'date'   ,'t':'date'	,'w':'99px'	,'x': '01/01/2012'}
		,{'k':'pmt_type'        ,'l':'type'   		,'u': None     ,'t':None	,'w':'104px'	,'x': 'monetarypayment.amazonpayment'}
                ,{'k':'charge_type'     ,'l':'credit/debit'     ,'u': None	,'t':None	,'w':'44px'	,'x': 'credit'}
                ,{'k':'pmt_amount'      ,'l':'pmt_amt'       ,'u': 'currency','t':'number'	,'w':'62px'	,'x': '$10,000'}
                ,{'k':'gateway'      	,'l':'pmt_gateway'      ,'u': None 	,'t':None	,'w':'82px'	,'x': 'braintree'}
                ,{'k':'gateway_txn_id'  ,'l':'gateway_txn_id'   ,'u': None	,'t':None	,'w':'62px'	,'x': '5gkhn2'}
		
#txn#
		,{'k':'transaction_id'   ,'l':'transaction_id'	,'u': None	,'t':None	,'w':'104px'	,'x': 'adb0b478dd7e4f678f1aad19a7f07092'}
		,{'k':'txn_date'	,'l':'txn_date'	,'u': 'date'	,'t':'date'	,'w':'99px'	,'x': '01/01/2012'}
		,{'k':'txn_status'	,'l':'status'		,'u': None	,'t':None	,'w':'52px'	,'x': 'completed'}
                ,{'k':'qty'             ,'l':'#vouchers'	,'u': 'integer'	,'t':'number'	,'w':'44px'	,'x': '999'}
                ,{'k':'txn_amount'      ,'l':'txn_$total'	,'u': 'currency','t':'number'	,'w':'62px'	,'x': '$10,000'}
                ,{'k':'txn_credits'   	,'l':'txn_$credits'	,'u': 'currency','t':'number'	,'w':'49px'	,'x': '$10,000'}
#context#
                ,{'k':'source'       	,'l':'source'        	,'u': None	,'t':None	,'w':'49px'	,'x': 'TOM'}
                ,{'k':'publisher'       ,'l':'publisher'        ,'u': None	,'t':None	,'w':'159px'	,'x': 'msn'}
		,{'k':'channel'		,'l':'channel'		,'u': None	,'t':None	,'w':'159px'	,'x': 'msn-austin'}
		,{'k':'agency'		,'l':'agency'		,'u': None	,'t':None	,'w':'69px'	,'x': 'tippr'}
		,{'k':'agent'		,'l':'agent'		,'u': None	,'t':None	,'w':'109px'	,'x': 'jakob jingle-himer'}
#ofr#
                ,{'k':'offer_id'        ,'l':'promotion_id'     ,'u': None      ,'t':None	,'w':'109px'    ,'x': 'adb0b478dd7e4f678f1aad19a7f07092'}
                ,{'k':'promotion_start' ,'l':'promotion_start'  ,'u': 'date'	,'t':'date'	,'w':'258px'    ,'x': '01/01/2012'}
                ,{'k':'promotion_end'   ,'l':'promotion_end'    ,'u': 'date'	,'t':'date'	,'w':'83px'     ,'x': '01/01/2012'}
                ,{'k':'promotion'       ,'l':'promotion'        ,'u': None      ,'t':None	,'w':'109px'    ,'x': ''}
		,{'k':'category'        ,'l':'category'         ,'u': None	,'t':None        ,'w':'133px'    ,'x': 'Health & Medicine'}
                ,{'k':'merchant'        , 'l':'merchant'        ,'u': None      ,'t':None       ,'w':'158px'    ,'x': 'Medicine & Anti-Aging Clinic'}
#usr#
               	,{'k':'name' 		,'l':'user_name'      	,'u': None	,'t':None        ,'w':'109px'    ,'x': 'jakob jingle-himer'}
               	,{'k':'email' 		,'l':'email'         	,'u': None	,'t':None        ,'w':'159px'  	,'x': 'able_baker@a_longaddr.com'}
               	,{'k':'date_joined' 	,'l':'date_joined'      ,'u': 'date'	,'t':'date'    	,'w':'82px'	,'x': '01/01/2012'}
               	,{'k':'city' 		,'l':'city'          	,'u': None	,'t':None      	,'w':'113px'	,'x': 'San Francisco'}
               	,{'k':'state' 		,'l':'state'          	,'u': None	,'t':None      	,'w':'33px'	,'x': 'CA'}
               	,{'k':'zipcode' 	,'l':'zipcode'          ,'u': None	,'t':None      	,'w':'53px'	,'x': '94707'}

                ,{'k':'tom_source'      ,'l':'tom_source'      	,'u': None       ,'t':None       ,'w':'82px'     ,'x': ''}

#                ,{'k':'deal_source'     ,'l':'deal_source'       ,'u': None     ,'t':None       ,'w':'53px'     ,'x': ''}
#                ,{'k':'deal_campaign'   ,'l':'deal_campaign'     ,'u': None     ,'t':None       ,'w':'82px'     ,'x': ''}
#                ,{'k':'deal_medium'     ,'l':'deal_medium'      ,'u': None      ,'t':None       ,'w':'82px'     ,'x': ''}
        ]

		META = {#TODO: META data should ALWAYS be attached to the run-report!! to have an audit-trail of what generated this report.
                        # for JSON, we could have a META-block
                        # for csv file, we could have a seperate *.meta file
                        # for web-pages, there could be mouse-over or special pop-up modal
                        # for printed it should always say above the footer
				'report': 'MS TRANSACTION DETAIL REPORT',
				'rpt_v' : 1.0,
                'slug'  : 'MS-TXN-DET-REP',
                'title' : 'MS Transaction Detail Report',
                'subtitle': '',
                'lpp'   : None,
                'base_query': require_query.base_query,
                # ideas: incl_titles, best_width, best_height, is_use_color?, is_html_interactive?
                # new idea: checksums (that we can't put in the csv), e.g. #rows, sum(<field>), MD5
                # other idea: profiling: it took x long for x rows, started at, finished at, against server X
        }


















