#!/usr/bin/python3
# NodePoint 2 - (C) 2017 Patrick Lambert - http://nodepoint.ca

import os
import connix
import sqlite3
db = os.path.join("..", "..", "data", "users.db")
cfg = connix.load(os.path.join("..", "..", "data", "config.json"))

#
# Users database initialization
#
def init():
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	cur.execute("CREATE TABLE IF NOT EXISTS users (userid TEXT PRIMARY KEY, username TEXT, password TEXT, fullname TEXT, email TEXT, lastlogin INT)")
	cur.execute("CREATE TABLE IF NOT EXISTS sessions (authkey TEXT PRIMARY KEY, userid TEXT, ip TEXT, expires INT)")
	cur.execute("CREATE TABLE IF NOT EXISTS groups (groupid TEXT PRIMARY KEY, groupname TEXT, perms TEXT)")
	cur.execute("INSERT OR REPLACE INTO groups VALUES ('PRODUCT_ADMINS', 'Product Administrators', 'users:*,config:*,misc:*')")
	cur.execute("CREATE TABLE IF NOT EXISTS groupmembers (groupid TEXT, userid TEXT, time INT)")
	cur.execute("CREATE TABLE IF NOT EXISTS userattrs (userid TEXT, attribute TEXT, value TEXT)")
	cur.execute("DELETE FROM sessions WHERE expires < ?", [connix.unixtime()])
	conn.commit()
	conn.close()

#
# Users operations
#
def login(username, password):
	authkey = None
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	cur.execute("SELECT userid FROM users WHERE username = ? AND password = ?", [username, connix.hash(password)])
	rows = cur.fetchall()
	for row in rows:
		authkey = connix.guid(64)
		cur.execute("UPDATE users SET lastlogin = ? WHERE userid = ?", [connix.unixtime(), row[0]])
		cur.execute("DELETE FROM sessions WHERE userid = ? AND ip = ?", [row[0], connix.remote_ip()])
		cur.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)", [authkey, row[0], connix.remote_ip(), connix.unixtime() + cfg['authkey_expiry']*60*60])
		conn.commit()
	conn.close()
	return authkey

def add_user(username, password, fullname, email):
	username = connix.alphanum(username)
	password = connix.hash(password)
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	cur.execute("SELECT userid FROM users WHERE username = ?", [username])
	rows = cur.fetchall()
	for row in rows:
		return None
	userid = connix.guid()
	cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", [userid, username, password, fullname, email, 0])
	conn.commit()
	return userid

def auth_user(authkey):
	user = None
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	cur.execute("SELECT userid FROM sessions WHERE authkey = ? AND ip = ?", [authkey, connix.remote_ip()])
	rows = cur.fetchall()
	for row in rows:
		user = {'userid': row[0], 'perms': [], 'attrs': {}}
		cur.execute("SELECT username,fullname,email FROM users WHERE userid = ?", [user['userid']])
		rows2 = cur.fetchall()
		for row2 in rows2:
			user['username'] = row2[0]
			user['fullname'] = row2[1]
			user['email'] = row2[2]
		cur.execute("SELECT groupid FROM groupmembers WHERE userid = ?", [user['userid']])
		rows2 = cur.fetchall()
		for row2 in rows2:
			cur.execute("SELECT perms FROM groups WHERE groupid = ?", [row2[0]])
			rows3 = cur.fetchall()
			for row3 in rows3:
				for perm in connix.remove_spaces(row3[0]).split(','):
					user['perms'].append(perm)
		cur.execute("SELECT attribute,value FROM userattrs WHERE userid = ?", [user['userid']])
		rows2 = cur.fetchall()
		for row2 in rows2:
			 user['attrs'][row2[0]] = row2[1]
	return user

