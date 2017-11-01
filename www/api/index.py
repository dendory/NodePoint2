#!/usr/bin/env python3
# NodePoint 2 - (C) 2017 Patrick Lambert - http://nodepoint.ca

import cgitb
import connix
import json
import os
import datetime
import users
import misc

#
# Initialization
#
__VERSION__ = "2.0.0-alpha1"
print(connix.header("application/javascript"))
q = connix.form()
cgitb.enable(context=1, format="text")
cfg = connix.load(os.path.join("..", "..", "data", "config.json"))
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
	if e != "ERR_INVALID_CMD":
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

elif q['cmd'].lower() == "add_group": # Add a new group
	if not user:
		err("ERR_NOT_AUTHORIZED")
	elif "users:add_group" not in user['perms'] and "users:*" not in user['perms']:
		err("ERR_NOT_AUTHORIZED")
	elif "groupname" not in q or "perms" not in q:
		err("ERR_MISSING_FIELDS")
	elif len(q['groupname']) < 3 or len(q['groupname']) > 255 or connix.alphanum(q['groupname'], spaces=True) != q['groupname']:
		err("ERR_MISFORMED_GROUPNAME")
	else:
		output = ok()
		output['groupid'] = users.add_group(connix.alphanum(q['groupname']), q['perms'])
		if not output['groupid']:
			err("ERR_GROUP_CREATION")
		out(output)

elif q['cmd'].lower() == "ban_user": # Ban a user
	if not user:
		err("ERR_NOT_AUTHORIZED")
	elif "users:ban_user" not in user['perms'] and "users:*" not in user['perms']:
		err("ERR_NOT_AUTHORIZED")
	elif "userid" not in q or "minutes" not in q:
		err("ERR_MISSING_FIELDS")
	elif not connix.is_int(q['minutes']) or int(q['minutes']) < 0 or int(q['minutes']) > 5256000:
		err("ERR_INVALID_MINUTES")
	else:
		output = ok()
		users.set_attr(q['userid'], "_banned", int(int(q['minutes'])*60+connix.unixtime()))
		out(output)

elif q['cmd'].lower() == "mod_user": # Modify a user
	if not user:
		err("ERR_NOT_AUTHORIZED")
	elif "users:mod_user" not in user['perms'] and "users:*" not in user['perms']:
		err("ERR_NOT_AUTHORIZED")
	elif "userid" not in q:
		err("ERR_MISSING_FIELDS")
	else:
		email = None
		fullname = None
		username = None
		if "email" in q:
			if "@" not in q['email'] or "." not in q['email'] or len(q['email']) < 3 or len(q['email']) > 255:
				err("ERR_MISFORMED_EMAIL")
			else:
				email = q['email']
		if "username" in q:
			if len(q['username']) < 3 or len(q['username']) > 255 or connix.alphanum(q['username']) != q['username']:
				err("ERR_MISFORMED_USERNAME")
			else:
				username = q['username']
		if "fullname" in q:
			fullname = q['fullname']
		output = ok()
		users.mod_user(q['userid'], username, fullname, email)
		out(output)

elif q['cmd'].lower() == "mod_group": # Modify a group
	if not user:
		err("ERR_NOT_AUTHORIZED")
	elif "users:mod_group" not in user['perms'] and "users:*" not in user['perms']:
		err("ERR_NOT_AUTHORIZED")
	elif "groupid" not in q:
		err("ERR_MISSING_FIELDS")
	else:
		groupname = None
		perms = None
		if "groupname" in q:
			if len(q['groupname']) < 3 or len(q['groupname']) > 255 or connix.alphanum(q['groupname'], spaces=True) != q['groupname']:
				err("ERR_MISFORMED_GROUPNAME")
			else:
				groupname = q['groupname']
		if "perms" in q:
			perms = q['perms']
		output = ok()
		users.mod_group(q['groupid'], groupname, perms)
		out(output)

elif q['cmd'].lower() == "show_log": # Show log entries
	output = ok()
	if not user:
		err("ERR_NOT_AUTHORIZED")
	elif "misc:show_log" not in user['perms'] and "misc:*" not in user['perms']:
		err("ERR_NOT_AUTHORIZED")
	else:
		output['log'] = misc.show_log()
		out(output)

elif q['cmd'].lower() == "login": # Login as a user
	output = ok()
	if "username" not in q or "password" not in q:
		err("ERR_MISSING_CREDENTIALS")
	if cfg['auth'] == "simple":
		authkey = users.login(q['username'], q['password'])
		if authkey:
			user = users.user_info(username=q['username'])
			banned = users.get_attr(user['userid'], "_banned")
			if banned and int(banned) > connix.unixtime():
				err("ERR_USER_BANNED")
			output['authkey'] = authkey
			output['valid_until'] = datetime.datetime.utcfromtimestamp(connix.unixtime()+cfg['authkey_expiry']*60*60).isoformat()
			output['valid_for'] = connix.remote_ip()
			output['user'] = user
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
	if not user:
		err("ERR_NOT_AUTHORIZED")
	elif "username" not in q and "userid" not in q:
		output['user'] = user
		out(output)
	elif "users:*" not in user['perms'] and "users:user_info" not in user['perms']:
		err("ERR_NOT_AUTHORIZED")
	elif "userid" not in q:
		output['user'] = users.user_info(username=q['username'])
		if not output['user']:
			err("ERR_INVALID_USER")
		else:
			out(output)
	else:
		output['user'] = users.user_info(userid=q['userid'])
		if not output['user']:
			err("ERR_INVALID_USER")
		else:
			out(output)

elif q['cmd'].lower() == "list_users": # List existing users
	output = ok()
	if not user:
		err("ERR_NOT_AUTHORIZED")
	elif "users:*" not in user['perms'] and "users:list_users" not in user['perms']:
		err("ERR_NOT_AUTHORIZED")
	else:
		output['users'] = users.list_users()
		out(output)

elif q['cmd'].lower() == "list_groups": # List existing groups
	output = ok()
	if not user:
		err("ERR_NOT_AUTHORIZED")
	elif "users:*" not in user['perms'] and "users:list_groups" not in user['perms']:
		err("ERR_NOT_AUTHORIZED")
	else:
		output['groups'] = users.list_groups()
		out(output)

elif q['cmd'].lower() == "help": # Show available commands
	output = ok()
	output['commands'] = {
		"user_info": ["username", "userid"],
		"texts": [],
		"login": ["username", "password"],
		"status": [],
		"list_users": [],
		"list_groups": [],
		"ban_user": ["userid", "minutes"],
		"add_user": ["username", "password", "fullname", "email"],
		"add_group": ["groupname", "perms"],
		"show_log": []
	}
	output['options'] = ["authkey"]
	out(output)

else:
	err("ERR_INVALID_CMD")

quit(0)
