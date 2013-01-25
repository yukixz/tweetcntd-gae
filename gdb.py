# -*- coding: utf-8 -*-
# @copyright:	GPL v3
# @author:	Dazzy Ding (dazzyd, @ks_magi)

from google.appengine.ext import db
import logging

class UserModel(db.Model):
	user_id		= db.IntegerProperty(required=True)
	token		= db.StringProperty(required=True)	# Access token
	secret		= db.StringProperty(required=True)	# Access token secret
	auth_time	= db.DateTimeProperty(auto_now_add=True)
	screen_name	= db.StringProperty()
	tweet_sum	= db.IntegerProperty()	# user's tweet count
	tweet_last	= db.IntegerProperty()	# user's last tweet timestamp

# Save new user
def save_user(user_id, new_token, new_secret):
	res = UserModel.all().filter('user_id = ', user_id)
	if res.count() > 0:
		db.delete(res)
	
	user = UserModel(user_id=user_id, token=new_token, secret=new_secret)
	user.put()

# Get all users
def get_all_users():
	return UserModel.all()

# Delete user
def delete_user(user_id, del_token, del_secret):
	res = UserModel.all().filter('token = ', del_token).filter('secret = ', del_secret)
	
	if res.count > 0:
		db.delete(res)
	else:
		logging.error("Gdb.delete() mismatch.")
		logging.error("user_id:%d\ntoken: %s\nsecret:%s" % (user_id, del_token, del_token))