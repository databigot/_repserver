#! /usr/bin/python

import txn_detail_def #incl: txn-credits, and msn-txn

import datetime
import sys


#	*Pick Query: /list query (TD)
#	if source=fixture:(TD)
#		use fixture=name, source=stdin|-|local|s3|mongo /list fixtures
#	*else #source=db:
#		*Set qualifiers {}/list qualifiers /save as canned (TD)
#		use canned qual-set /list canned qual-set (TD)	e.g. last month, recent msn
#	if generate=SQL
#	elif generate=Fixture
#		FixtureOut = *stdout|-|local|s3|mongo
#DEBUGGING (ideas): (TD)
#	-dry-run just check params, makesure all ok, 
#	-check-params?
#	--debug
#	also:
#		 run_rpt report -h/--help
#	save as canned? 


# usage:
#	see --help for full usage, 
#	invoke_query_tester.py [--sql-only] <query-name> {<qualifiers>}	

QUERIES = [txn_detail_def.Q_Test_Query(), txn_detail_def.Q_Txn_Detail(), txn_detail_def.Q_MSN_Detail(), txn_detail_def.Q_TXNPayment_Detail()]
PROG = sys.argv[0]

def main():
	""" 
	A command-line query runner, that tests out using the optargs library, 
	especially the cut-out passthrough from the query-def to define the qualifiers
	"""
    	import argparse
	# load late to avoid version conflict
    	parser = argparse.ArgumentParser(
			formatter_class=argparse.ArgumentDefaultsHelpFormatter
			, prog=PROG
			, description="A command-line tester for running defined queries."
			, epilog="---c.2012 tippr.com---\n\n")

#	parser.add_argument('report', default=None, help='Report to run')
	#add_argument('-l','--list', help='List available Reports')

	parser.add_argument('--sql-only', dest='sqlonly', action='store_true', default=False, help='Generate the sql only')
	parser.add_argument('--limit', dest='limit', default=100, type=int,  help='Limit the query to ## rows only -- good for testing!')


	sub_mountpoint=parser.add_subparsers(
		title='Available Queries', 
		description='Long-running Queries that are defined in the Reporting System.  \nUse %s <query-name> --help, for help on a specific query'%PROG, 
#		help='use "%s <query-name> --help" to get help on a specific query'%PROG,) 
		help='query-specific qualifiers can include e.g.: start-dt=YYYYMMDD, end-dt=YYYYMMDD, publisher=MSN',) 
	for q in QUERIES:
		q.subparser_add(sub_mountpoint)

	args_obj = parser.parse_args(sys.argv[1:])
	print args_obj

	query_obj = args_obj.func
	print "you have picked: %s"% query_obj.base_query
	
	#args = vars(args_obj)
	qualifier_set = query_obj.parser_pull_qualifiers(args_obj)

	if args_obj.limit:
		query_obj.limit = getattr(args_obj,'limit')

	query_obj.qualify(**qualifier_set)


	if args_obj.sqlonly:
		print query_obj.sql
	else:
		result_set = query_obj.load_dataset()	
		print result_set
	#print arguments


if __name__ == '__main__':
    main()
		
# vim: ai et sts=4 sw=4 ts=4
