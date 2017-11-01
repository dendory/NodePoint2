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

def add_group(groupname, perms):
	groupid = connix.guid()
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	cur.execute("SELECT groupid FROM groups WHERE groupname = ?", [groupname])
	rows = cur.fetchall()
	for row in rows:
		return None
	cur.execute("INSERT INTO groups VALUES (?, ?, ?)", [groupid, groupname, perms])
	conn.commit()
	conn.close()
	return groupid

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
	conn.close()
	return userid

def list_users():
	users = []
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	cur.execute("SELECT userid,username,fullname,email FROM users", [])
	rows = cur.fetchall()
	for row in rows:
		users.append({'userid': row[0], 'username': row[1], 'fullname': row[2], 'email': row[3]})
	conn.close()
	return users

def list_groups():
	groups = []
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	cur.execute("SELECT groupid,groupname,perms FROM groups", [])
	rows = cur.fetchall()
	for row in rows:
		groups.append({'groupid': row[0], 'groupname': row[1], 'perms': row[2]})
	conn.close()
	return groups

def set_attr(userid, attr, value):
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	cur.execute("DELETE FROM userattrs WHERE userid = ? AND attribute = ?", [userid, attr])
	conn.commit()
	if value:
		cur.execute("INSERT INTO userattrs VALUES (?, ?, ?)", [userid, attr, str(value)])
		conn.commit()
	conn.close()

def mod_user(userid, username=None, fullname=None, email=None):
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	if username:
		cur.execute("UPDATE users SET username = ? WHERE userid = ?", [username, userid])
	if fullname:
		cur.execute("UPDATE users SET fullname = ? WHERE userid = ?", [fullname, userid])
	if email:
		cur.execute("UPDATE users SET email = ? WHERE userid = ?", [email, userid])
	conn.commit()
	conn.close()

def mod_group(groupid, groupname=None, perms=None):
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	if groupname:
		cur.execute("UPDATE groups SET groupname = ? WHERE groupid = ?", [groupname, groupid])
	if perms:
		cur.execute("UPDATE groups SET perms = ? WHERE groupid = ?", [groupname, groupid])
	conn.commit()
	conn.close()

def user_info(userid=None, username=None):
	user = {'userid': None, 'username': username, 'perms': [], 'attrs': {}}
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	if username:
		cur.execute("SELECT userid,username,fullname,email,lastlogin FROM users WHERE username = ?", [username])
	else:
		cur.execute("SELECT userid,username,fullname,email,lastlogin FROM users WHERE userid = ?", [userid])
	rows = cur.fetchall()
	for row in rows:
		user['userid'] = row[0]
		user['username'] = row[1]
		user['fullname'] = row[2]
		user['email'] = row[3]
		user['lastlogin'] = connix.unixtime2datetime(int(row[4]))
	if not user['userid']:
		return None
	cur.execute("SELECT groupid FROM groupmembers WHERE userid = ?", [user['userid']])
	rows = cur.fetchall()
	for row in rows:
		cur.execute("SELECT perms FROM groups WHERE groupid = ?", [row[0]])
		rows2 = cur.fetchall()
		for row2 in rows2:
			for perm in connix.remove_spaces(row2[0]).split(','):
				user['perms'].append(perm)
	cur.execute("SELECT attribute,value FROM userattrs WHERE userid = ?", [user['userid']])
	rows = cur.fetchall()
	for row in rows:
		user['attrs'][row[0]] = row[1]
	conn.close()
	return user

def get_attr(userid, attr):
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	cur.execute("SELECT attribute,value FROM userattrs WHERE userid = ?", [userid])
	rows = cur.fetchall()
	for row in rows:
		if row[0] == attr:
			return row[1]
	conn.close()
	return None

def auth_user(authkey):
	user = None
	conn = sqlite3.connect(db)
	cur = conn.cursor()
	cur.execute("SELECT userid FROM sessions WHERE authkey = ? AND ip = ?", [authkey, connix.remote_ip()])
	rows = cur.fetchall()
	for row in rows:
		user = user_info(userid=row[0])
	if user:
		banned = get_attr(user['userid'], "_banned")
		if banned and int(banned) > connix.unixtime():
			return None
	conn.close()
	return user

