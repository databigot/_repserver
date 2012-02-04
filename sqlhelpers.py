import psycopg2
from  settings import *

from pymongo import Connection

def db_connectstring(dbName=None):
    (user,dbname,host,port) = db_params(dbName)
    return "dbname='%s' user='%s' host='%s'"% (
	dbname, user, host )

def db_params(dbName=None):
	dbName=dbName or DB_PBT
	return [dbName[x] for x in 
		['DATABASE_USER','DATABASE_NAME','DATABASE_HOST','DATABASE_PORT']]

def shared_db(dbName=None):
    try:
	DB_CONNECT=db_connectstring(dbName)
        conn = psycopg2.connect(DB_CONNECT)
        return conn        
    except Exception as e:
        print "I am unable to connect to the db", e
        return None

g_conn = shared_db()

def throw_sql(sql, dbName=None):
    try:
        conn = psycopg2.connect(db_connectstring(dbName));
#        conn = g_conn
        curr = conn.cursor()
        curr.execute(sql)
        results = curr.fetchall();
        cols = [x.name for x in curr.description]
        return cols, results;
    except Exception as e:
        print "I am unable to connect to the database", e
        return None

def mongo_data( query, fields, collection, db='test', host='localhost', port=27017):
    (user,db,host,port) = db_params(DB_MONGO)
    try:
	conn = Connection(host,port)
	db = conn[db]
	coll = db[collection]
	query = coll.find(query, fields, limit=9999)
	return [z for z in query]
    except Exception as e:
	print "Database error",e
	return None

def sql_simple_fetchrow(sql,dbName=None):
    try:
        conn = psycopg2.connect(db_connectstring(dbName));
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

def sql_pull_lookup(sql,dbName=None): #for pulling id:value results, e.g. (publisher_id,publisher.title)
	#assumes unique id, and row result will be of form: [key,value]
    try:
        conn = psycopg2.connect(db_connectstring(dbName));
        curr = conn.cursor()
        curr.execute(sql)
        results = curr.fetchall();

#        return dict([(x[0],x[1]) for x in results])
        return [(x[0],x[1]) for x in results]
    except Exception as e:
        print "I am unable to connect to the database", e
        return None
