from sqlhelpers import *
from flask import Flask, url_for, render_template, g, session, request, redirect, abort


def subscriptions(id='None'):
	""" 
		A TEST REPORT!!
	first attempt at a report against mongo.
	pulls the # of subs per publisher per hour
	"""
	rows = mongo_data({}, ["publisher_id","dt_hour", "new_subs"],"subscribers")
	#returns [{_id:...,field1:...,field2:...}]


	COLS = ["publisher_id", "dt_hour", "new subs"]
	ROWS = [[y["publisher_id"],y["dt_hour"],y["new_subs"]] for y in rows]

	TITLE = 'SUBSCRIPTIONS'

	return render_template("simple_tester_report.html", cols=COLS, rows=ROWS, report_title=TITLE);




