from pymongo import Connection
import psycopg2

pbt_conn = psycopg2.connect("dbname='silos' user='django' host='127.0.0.1'");
pull_subs_bypub_byhour = """
	select date_trunc('hour', s.occurrence), a.publisher_id, count(s.id)
  		from core_subscription s, core_account a
  		where s.account_id = a.id and s.status in ('subscribed','pending-subscribe')
			and s.occurrence > date_trunc('day',current_date - interval '1 day')
  	group by 1,2
  	order by date_trunc('hour',s.occurrence);
"""
pull_unsubs_bypub_byhour = """
	select date_trunc('hour', s.occurrence), a.publisher_id, count(s.id)
  		from core_subscription s, core_account a
  		where s.account_id = a.id and s.status ='unsubscribed'
			and s.occurrence > date_trunc('day',current_date - interval '1 day')
  	group by 1,2
  	order by date_trunc('hour',s.occurrence);
"""
pbt_cursor = pbt_conn.cursor()
pbt_cursor.execute(pull_subs_bypub_byhour)
rows = pbt_cursor.fetchall()


mongo_conn = Connection("localhost")
mongo_coll = mongo_conn.test.subscribers
mongo_coll.remove()
for row in rows:
	mongo_coll.insert({'publisher_id':row[1], 'dt_hour':row[0], 'new_subs':row[2] })


