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







#Basic development settings
DEVELOPMENT_DEFAULTS = {
    'DATABASE_HOST': '127.0.0.1',
    'DATABASE_NAME': 'silos',
    'DATABASE_PASSWORD': '',
    'DATABASE_PORT': '',
    'DATABASE_USER': 'django',
    'WEBSERVER_PORT': 10000+UID,
    'WEBSERVER_HOST': '0.0.0.0',
    'DEBUG': True
}



PRODUCTION_DEFAULTS = {
    'DATABASE_HOST': '127.0.0.1',
    'DATABASE_NAME': 'silos',
    'DATABASE_PASSWORD': '',
    'DATABASE_PORT': '',
    'DATABASE_USER': 'django',
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





