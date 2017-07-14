#!/usr/bin/python3
# NodePoint 2 - (C) 2017 Patrick Lambert - http://nodepoint.ca

import os
import connix
import sqlite3
db = os.path.join("..", "..", "data", "misc.db")
cfg = connix.load(os.path.join("..", "..", "data", "config.json"))

#
# Various misc database tables
#
def init():
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	cur.execute("CREATE TABLE IF NOT EXISTS log (time INT, userid TEXT, ip TEXT, operation TEXT, result INT, message TEXT)")
	conn.commit()
	conn.close()

#
# Misc functions
#
def log(user, operation, result, message):
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	userid = None
	if user:
		userid = user['userid']
	cur.execute("INSERT INTO log VALUES (?, ?, ?, ?, ?, ?)", [connix.unixtime(), userid, connix.remote_ip(), operation, int(result), message])
	conn.commit()
	conn.close()
	return

def show_log():
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	cur.execute("SELECT * FROM log ORDER BY time DESC LIMIT ?;", [cfg['query_limit']])
	results = []
	for row in cur.fetchall():
		results.append({'time': connix.unixtime2datetime(row[0]), 'userid': row[1], 'ip': row[2], 'operation': row[3], 'status': row[4], 'message': row[5]})
	conn.close()
	return results
