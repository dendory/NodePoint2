#!/usr/bin/env python3
# NodePoint 2 - (C) 2017 Patrick Lambert - http://nodepoint.ca

import cgitb
import connix
import json
import os
import datetime

#
# Initialization
#
__VERSION__ = "2.0.0-alpha1"
print(connix.header("application/javascript"))
q = connix.form()
cgitb.enable(context=1, format="text")
try:
	cfg = connix.load(os.path.join("..", "..", "data", "config.json"))
except:
	print(json.dumps({'status': 1, 'code': "ERR_INITIAL_SETUP", 'message': "Initial setup files missing. Please run setup.py"}, sort_keys = False, indent = 4))
	quit(1)

import users
import misc

strings = connix.load(os.path.join("..", "..", "texts", "strings.json"))
errors = connix.load(os.path.join("..", "..", "texts", "errors.json"))
misc.init()
users.init()
user = None

def out(output):
	misc.log(user, q['cmd'].lower(), 0, errors[cfg['lang']]['OK'])
	print(json.dumps(output, sort_keys = False, indent = 4))
	quit(0)

def err(e):
	misc.log(user, q['cmd'].lower(), 1, errors[cfg['lang']][e])
	output = {'status': 1, 'code': e, 'message': errors[cfg['lang']][e]}
	print(json.dumps(output, sort_keys = False, indent = 4))
	quit(1)

def ok():
	return {'status': 0, 'code': "OK", 'message': errors[cfg['lang']]['OK']}

if "cmd" not in q:
	err("ERR_INVALID_CMD")

if "authkey" in q:
	user = users.auth_user(q['authkey'])
	if not user:
		err("ERR_INVALID_AUTHKEY")

#
# Command processing
#
if q['cmd'].lower() == "status": # Display the status of the server
	output = ok()
	output['version'] = __VERSION__
	output['platform'] = os.uname()
	output['pid'] = os.getpid()
	output['path'] = os.path.realpath(__file__)
	output['config'] = cfg
	out(output)
elif q['cmd'].lower() == "add_user": # Add a new user
	if not user:
		err("ERR_NOT_AUTHORIZED")
	elif "users:add_user" not in user['perms'] and "users:*" not in user['perms']:
		err("ERR_NOT_AUTHORIZED")
	elif "username" not in q or "password" not in q or "fullname" not in q or "email" not in q:
		err("ERR_MISSING_FIELDS")
	elif "@" not in q['email'] or "." not in q['email'] or len(q['email']) < 3 or len(q['email']) > 255:
		err("ERR_MISFORMED_EMAIL")
	elif len(q['username']) < 3 or len(q['username']) > 255 or connix.alphanum(q['username']) != q['username']:
		err("ERR_MISFORMED_USERNAME")
	else:
		output = ok()
		output['userid'] = users.add_user(connix.alphanum(q['username']), q['password'], q['fullname'], q['email'])
		if not output['userid']:
			err("ERR_USER_CREATION")
		out(output)
elif q['cmd'].lower() == "show_log": # Show log entries
	if not user:
		err("ERR_NOT_AUTHORIZED")
	elif "misc:show_log" not in user['perms'] and "misc:*" not in user['perms']:
		err("ERR_NOT_AUTHORIZED")
	else:
		output = ok()
		output['log'] = misc.show_log()
		out(output)
elif q['cmd'].lower() == "login": # Login as a user
	if "username" not in q or "password" not in q:
		err("ERR_MISSING_CREDENTIALS")
	if cfg['auth'] == "simple":
		authkey = users.login(q['username'], q['password'])
		if authkey:
			output = ok()
			output['authkey'] = authkey
			output['valid_until'] = datetime.datetime.utcfromtimestamp(connix.unixtime()+cfg['authkey_expiry']*60*60).isoformat()
			output['valid_for'] = connix.remote_ip()
			out(output)
		else:
			err("ERR_INVALID_CREDENTIALS")
elif q['cmd'].lower() == "texts": # Retrieve all strings
	output = ok()
	output['errors'] = errors[cfg['lang']]
	output['strings'] = strings[cfg['lang']]
	out(output)
elif q['cmd'].lower() == "user_info": # Retrieve a user's information
	output = ok()
	if "username" not in q:
		output['info'] = user
		out(output)
	elif "users:*" in user['perms'] or "users:user_info" in user['perms']:
		output['info'] = user_info(q['username'])
		out(output)
elif q['cmd'].lower() == "help": # Show available commands
	output = ok()
	output['commands'] = {
		"user_info": ["username"],
		"texts": [],
		"login": ["username", "password"],
		"status": [],
		"add_user": ["username", "password", "fullname", "email"]
	}
	output['options'] = ["authkey"]
	out(output)
else:
	err("ERR_INVALID_CMD")
quit(0)
