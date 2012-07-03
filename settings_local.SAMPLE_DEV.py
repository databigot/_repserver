
#Settings File SAMPLE for DEVELOPMENT -- NOT PRODUCTION.
#  COPY TO settings_local.py, to setup a new box.

# DO NOT checkin settings_local.py to GIT!!!

# general settings (not machine specific) should be set in settings.py, and committed.
#*********************** DEVELOPMENT SETTINGS (not production!!) *********************

import os



IN_PRODUCTION = False 
UID = os.getuid()

WEBSERVER_PORT = 10000+UID
WEBSERVER_HOST = '0.0.0.0'
DEBUG = True


ACCESS_GROUPS = { #use these to whitelist a report to only certain people: !!please include full email addr w/the @tippr.com!
    'VIPS': []
    ,'DEVS': ['jeremy.elliott@tippr.com','aaron.krill@tippr.com']
    ,'TEST1': ['jeff.house@tippr.com']
    ,'TEST2': ['jeremy.elliott@tippr.com']		
}

#S3 Stuff
S3_ACCESS_KEY = "AKIAJIEVGZJ2RWZPUGUA"
S3_SECRET_KEY = "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"

S3_REPORT_BUCKET = 'reportserver.TEST.reports'



#Database Connections -- NOTE: DEV!
#'DATABASES': #add all db connections here, incl. mongo.
# note: since this is a read-only application, we have been known to point to live production dbs, even in dev, to get a good sample dataset.  this is ok.  however, if it becomes desirable, these settings could be changed to point to development databases, instead.
DB_PBT = {
	    'DATABASE_HOST': 'slave.db.production.kashless.com',
	    'DATABASE_NAME': 'pbt',
	    'DATABASE_PASS': '',
	    'DATABASE_PORT': '5432',
	    'DATABASE_USER': 'pbt',
	    }
DB_TOM = {
	    'DATABASE_HOST': 'slave.db.production.kashless.com',
	    'DATABASE_NAME': 'tom',
	    'DATABASE_PASS': '',
	    'DATABASE_PORT': '5432', #6432',
	    'DATABASE_USER': 'tom',
	    }
DB_JETEST_MONGO = {#MONGO
	    'DATABASE_HOST': '127.0.0.1',
	    'DATABASE_NAME': 'test',
	    'DATABASE_PORT': 27017
	    }
DB_EDW = {#MONGO DataWarehouse READ ONLY!
	    'DATABASE_HOST': 'dw.tippr.com',
	    'DATABASE_NAME': 'warehouse',
	    'DATABASE_PORT': 27017,
	    'DATABASE_USER': 'warehouse-ro',
	    'DATABASE_PASS': 'fr33$tuff'
	    }
DB_CODESTORE = {#MONGO
	    'DATABASE_HOST': 'master.dw.tippr.com',
	    'DATABASE_NAME': 'code_store',
	    'DATABASE_PORT': 27017,
	    'DATABASE_USER': 'code_store',
	    'DATABASE_PASS': 'fr33$tuff'
	    }
#	'default': 'DB_PBT'






