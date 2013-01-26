# -*- coding: utf-8 -*-
# @copyright:	GPL v3
# @author:	Dazzy Ding (dazzyd, @ks_magi)

from google.appengine.ext import db
import json
import logging

class User(db.Model):
	user_id		= db.IntegerProperty(required=True)
	token		= db.StringProperty(required=True)	# Access token
	secret		= db.StringProperty(required=True)	# Access token secret
	auth_time	= db.DateTimeProperty(auto_now_add=True)
	tweet_last	= db.IntegerProperty()
	tweet_count	= db.StringProperty()


# Get all users
def all_users():
	return User.all()

# Save new user
def save_user(user_id, new_token, new_secret):
	res = User.all().filter('user_id = ', user_id)
	if res.count() > 0:
		db.delete(res)
	
	user = User(user_id=user_id, token=new_token, secret=new_secret, tweet_last=0, tweet_count='{"rt": 0, "re": 0, "sum": 0, "rts": 0}')
	user.put()

# Delete user
def delete_user(user_id, del_token, del_secret):
	res = User.all().filter('token = ', del_token).filter('secret = ', del_secret)
	
	if res.count > 0:
		db.delete(res)
	else:
		logging.error("gdb.delete() Mismatch.")
		logging.error("user_id: %d\ntoken: %s\nsecret: %s" % (user_id, del_token, del_token))


# Save user's count
def save_count(user_id, sum, re, rt, rts, last):
	res = User.all().filter("user_id = ", user_id)
	if res.count()==1:
		json_str = json.dumps( {"sum":sum, "re":re, "rt":rt, "rts":rts} )
		user = res.get()
		user.tweet_count = json_str
		user.tweet_last = last
		user.put()
	else:
		logging.error("gdb.save_count():")
		logging.error("user_id: %d\ncount: %d, %d, %d, %d" % (user_id, sum, re, rt, rts))

# Load user's count
def load_count(user_id):
	res = User.all().filter("user_id = ", user_id)
	if res.count()==1:
		user = res.get()
		json_obj = json.loads( user.tweet_count )
		return (json_obj['sum'], json_obj['re'], json_obj['rt'], json_obj['rts'], user.tweet_last)
	else:
		logging.error("gdb.load_count():")
		logging.error("user_id: %d" % (user_id))
	
# Reset user's count
def reset_count(user_id):
	res = User.all().filter("user_id = ", user_id)
	if res.count()==1:
		user = res.get()
		user.tweet_count = '{"rt": 0, "re": 0, "sum": 0, "rts": 0}'
		user.put()
	else:
		logging.error("gdb.load_count():")
		logging.error("user_id: %d" % (user_id))