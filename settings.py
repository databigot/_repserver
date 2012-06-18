import os
import sys



IN_PRODUCTION = '-production' in sys.argv
UID = os.getuid()




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



#Basic development settings
DEVELOPMENT_DEFAULTS = {
    #'DATABASES': #add all db connections here, incl. mongo.
    #TODO: pwd is ignored right now.
    'DB_PBT': {
	    'DATABASE_HOST': '127.0.0.1',
	    'DATABASE_NAME': 'silos',
	    'DATABASE_PASS': '',
	    'DATABASE_PORT': '',
	    'DATABASE_USER': 'django',
	    },
    'DB_TOM': {
	    'DATABASE_HOST': 'localhost',
	    'DATABASE_NAME': 'tom',
	    'DATABASE_PASS': '',
	    'DATABASE_PORT': '6432',
	    'DATABASE_USER': 'tom',
	    },
    'DB_JETEST_MONGO': {#MONGO
	    'DATABASE_HOST': '127.0.0.1',
	    'DATABASE_NAME': 'test',
	    'DATABASE_PORT': 27017
	    },
    'DB_EDW': {#MONGO DataWarehouse READ ONLY!
	    'DATABASE_HOST': 'dw.tippr.com',
	    'DATABASE_NAME': 'warehouse',
	    'DATABASE_PORT': 27017,
	    'DATABASE_USER': 'warehouse-ro',
	    'DATABASE_PASS': 'fr33$tuff'
	    },
    'DB_CODESTORE': {#MONGO
	    'DATABASE_HOST': 'master.dw.tippr.com',
	    'DATABASE_NAME': 'code_store',
	    'DATABASE_PORT': 27017,
	    'DATABASE_USER': 'code_store',
	    'DATABASE_PASS': 'fr33$tuff'
	    },
#	'default': 'DB_PBT'
    'WEBSERVER_PORT': 10000+UID,
    'WEBSERVER_HOST': '0.0.0.0',
    'DEBUG': True
}



PRODUCTION_DEFAULTS = {
#    'DATABASES':  #add all db connections here, incl. mongo.
    'DB_PBT': {
         'DATABASE_HOST': '127.0.0.1',
    	 'DATABASE_NAME': 'silos',
    	 'DATABASE_PASSWORD': '',
    	 'DATABASE_PORT': '',
    	 'DATABASE_USER': 'django',
    	 },
    'DB_TOM': {
         'DATABASE_HOST': 'localhost',
         'DATABASE_NAME': 'tom',
         'DATABASE_PASSWORD': '',
         'DATABASE_PORT': '6432',
         'DATABASE_USER': 'tom',
         },
    'DB_JETEST_MONGO': {#MONGO
	    'DATABASE_HOST': '127.0.0.1',
	    'DATABASE_NAME': 'test',
	    'DATABASE_PORT': 27017
	    },
    'DB_EDW': {#MONGO DataWarehouse READ ONLY!
	    'DATABASE_HOST': 'dw.tippr.com',
	    'DATABASE_NAME': 'warehouse',
	    'DATABASE_PORT': 27017,
	    'DATABASE_USER': 'warehouse-ro',
	    'DATABASE_PASS': 'fr33$tuff'
	    },
    'DB_CODESTORE': {#MONGO
	    'DATABASE_HOST': 'master.dw.tippr.com',
	    'DATABASE_NAME': 'code_store',
	    'DATABASE_PORT': 27017,
	    'DATABASE_USER': 'code_store',
	    'DATABASE_PASS': 'fr33$tuff'
	    },
#	'default': 'DB_PBT'
    'WEBSERVER_PORT': 80,
    'WEBSERVER_HOST': '0.0.0.0',
    'DEBUG': False
}

current_settings = globals()

import json
failures = False
for (k,v) in os.environ.iteritems():
    if k.startswith('OVERRIDE_'):
        try:
            var = k[len('OVERRIDE_'):]
            val = json.loads(v)
            current_settings[var] = val
        except Exception as e:
            print >>sys.stderr, 'Unable to decode %r (%r): %s' % (k, v, str(e)) # logging module not configured yet
            failures = True
if failures:
    raise e

for (k,v) in (PRODUCTION_DEFAULTS if IN_PRODUCTION else DEVELOPMENT_DEFAULTS).iteritems():
    current_settings.setdefault(k, v)





