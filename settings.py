

#############
#
# common settings.
#
############

import os

#NOTE: settings_local is imported at bottom, to override general settings.

UID = os.getuid()

#S3 Stuff
S3_ACCESS_KEY = "AKIAJIEVGZJ2RWZPUGUA"
S3_SECRET_KEY = "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"

S3_REPORT_BUCKET = 'reportserver.reports'


DEBUG = False


#**********Please keep this line at bottom of file **********
from settings_local import *	#Machine specific settings!





