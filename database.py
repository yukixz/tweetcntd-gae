# -*- coding: utf-8 -*-
# @copyright:	GPL v3
# @author:	Dazzy Ding (dazzyd, @ks_magi)

from google.appengine.ext import db
import logging

class UserModel(db.Model):
	token		= db.StringProperty(required=True)  # Access token
	secret		= db.StringProperty(required=True)  # Access token secret
	auth_time	= db.DateTimeProperty(auto_now_add=True)
	username	= db.StringProperty(required=True)
	user_sum	= db.IntegerProperty()  # user's tweet count
	user_last	= db.IntegerProperty()  # user's last tweet timestamp

# Save new user
def db_save_new(new_token, new_secret):
	res = UserModel.all().filter('token = ', new_token)
	if res.count() > 0:
		db.delete(res)
	
	user = UserModel( token = new_token,
					  secret = new_secret)
	user.put()

# Get all users
def db_get_all():
	return UserModel.all()

# Delete user
def db_delete(del_token, del_secret):
	res = UserModel.all().filter('token = ', del_token).filter('secret = ', del_secret)
	
	if res.count > 0:
		db.delete(res)
	else:
		logging.error("delete_model mismatch. token: " + token)
        logging.error("delete_model mismatch. secret: " + secret)