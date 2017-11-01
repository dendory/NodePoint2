#!/usr/bin/python3
# NodePoint 2 - (C) 2017 Patrick Lambert - http://nodepoint.ca

import os
import sqlite3
usersdb = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "users.db")
miscdb = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "misc.db")

try:
	import connix
except:
	print("Library 'connix' is missing - pip install connix")
	quit(1)

if os.geteuid() != 0:
	print("You must run this script as root")
	quit(1)

print("* Reading configuration")
try:
	cfg = connix.load(os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "config.json"))
except:
	print("* Could not load configuration, creating data/config.json")
	cfg = {
		"lang": "EN",
		"2fa": False,
		"auth": "simple",
		"authkey_expiry": 8,
		"query_limit": 5000
	}
	try:
		connix.save(os.path.join("data", "config.json"), cfg)
	except:
		print("Could not save to data/config.json - " + connix.error())
		quit(1)

print("* Checking users table")
try:
	conn = sqlite3.connect(usersdb)
	cur = conn.cursor()
	cur.execute("CREATE TABLE IF NOT EXISTS users (userid TEXT PRIMARY KEY, username TEXT, password TEXT, fullname TEXT, email TEXT, lastlogin INT)")
	cur.execute("CREATE TABLE IF NOT EXISTS groupmembers (groupid TEXT, userid TEXT, time INT)")
	conn.commit()
	conn.close()
except:
	print("Could not write to data/users.db - " + connix.error())
	quit(1)

print("* Checking log table")
try:
	conn = sqlite3.connect(miscdb)
	cur = conn.cursor()
	cur.execute("CREATE TABLE IF NOT EXISTS log (time INT, userid TEXT, ip TEXT, operation TEXT, result INT, message TEXT)")
	cur.execute("INSERT INTO log VALUES (?, ?, ?, ?, ?, ?)", [connix.unixtime(), None, "console", "setup.py", 0, ""])
	conn.commit()
	conn.close()
except:
	print("Could not write to data/misc.db - " + connix.error())
	quit(1)

print("Init done.")

choice = "-1"
while choice != "0":
	print("* Select a function:")
	print("0. Exit")
	print("1. Create admin user")
	print("2. Set folder permissions")
	print("3. Create web symlink")
	choice = connix.ask("Enter a menu entry:")
	if choice == "1":
		username = connix.alphanum(connix.ask("Username:", "admin"))
		password = connix.hash(connix.ask("Password:"))
		fullname = connix.ask("Full name:")
		email = connix.ask("Email address:")
		userid = connix.guid()
		try:
			conn = sqlite3.connect(usersdb)
			cur = conn.cursor()
			cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", [userid, username, password, fullname, email, 0])
			cur.execute("INSERT INTO groupmembers VALUES (?, ?, ?)", ["PRODUCT_ADMINS", userid, connix.unixtime()])
			conn.commit()
			conn.close()
			print("Admin user created: " + username)
		except:
			print("Could not write to data/users.db - " + connix.error())
	if choice == "2":
		apacheuser = connix.ask("Which user is Apache running under?", "apache")
		connix.cmd("chown -R " + apacheuser + " data")
		print("Owner set.")
	if choice == "3":
		folder = connix.ask("Where is your document root?", "/var/www/html")
		connix.cmd("ln -s " + os.path.dirname(os.path.realpath(__file__)) + "/www " + folder + "/nodepoint")
		print("Symlink created. The web interface should be accessible as http://localhost/nodepoint")

print("Exiting.")
