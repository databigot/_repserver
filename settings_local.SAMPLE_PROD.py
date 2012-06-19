
#Settings File SAMPLE for PRODUCTION -- NOT DEVELOPMENT.
#  COPY TO settings_local.py, to setup a new box.

# DO NOT checkin settings_local.py to GIT!!!

# general settings (not machine specific) should be set in settings.py, and committed.

#*********************** PRODUCTION SETTINGS (not development!!) *********************


import os



#IN_PRODUCTION = '-production' in sys.argv
IN_PRODUCTION = True
UID = os.getuid()

WEBSERVER_PORT= 80
WEBSERVER_HOST= '0.0.0.0'
DEBUG= False



ACCESS_GROUPS = { #use these to whitelist a report to only certain people: !!please include full email addr w/the @tippr.com!
    'VIPS': []
    ,'DEVS': ['jeremy.elliott@tippr.com','aaron.krill@tippr.com']
    ,'TEST1': ['jeff.house@tippr.com']
    ,'TEST2': ['jeremy.elliott@tippr.com']		
}

#S3 Stuff
S3_ACCESS_KEY = "AKIAJIEVGZJ2RWZPUGUA"
S3_SECRET_KEY = "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"

S3_REPORT_BUCKET = 'reportserver.reports'



#Database Connections -- NOTE: PROD!
#'DATABASES': #add all db connections here, incl. mongo.
DB_PBT = {
	    'DATABASE_HOST': 'slave.db.production.kashless.com',
	    'DATABASE_NAME': 'silos',
	    'DATABASE_PASS': '',
	    'DATABASE_PORT': '5432',
	    'DATABASE_USER': 'django',
	    }
DB_TOM = {
	    'DATABASE_HOST': 'slave.db.production.kashless.com',
	    'DATABASE_NAME': 'tom',
	    'DATABASE_PASS': '',
	    'DATABASE_PORT': '5432', #'6432',
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


