# -*- coding: utf-8 -*-
# @copying:	GPL v3
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
def delete_user(user):
	db.delete(user)


# Save user's count
def save_count(user, sum, re, rt, rts, last):
	json_str = json.dumps( {"sum":sum, "re":re, "rt":rt, "rts":rts} )
	user.tweet_count = json_str
	user.tweet_last = last
	user.put()

# Load user's count
def load_count(user):
	json_obj = json.loads( user.tweet_count )
	return (json_obj['sum'], json_obj['re'], json_obj['rt'], json_obj['rts'], user.tweet_last)
	
# Reset user's count
def reset_count(user):
	user.tweet_count = '{"rt": 0, "re": 0, "sum": 0, "rts": 0}'
	user.put()