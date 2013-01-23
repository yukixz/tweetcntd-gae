# -*- coding: utf-8 -*-
# @copyright:	GPL v3
# @author:	Dazzy Ding (dazzyd, @ks_magi)

from google.appengine.ext import db
import logging

class UserModel(db.Model):
    username    = db.StringProperty(required=True)
    token       = db.StringProperty(required=True)  # Access token
    secret      = db.StringProperty(required=True)  # Access token secret
    auth_time   = db.DateTimeProperty(auto_now_add=True)
    user_sum    = db.IntegerProperty()  # user's tweet count
    user_last   = db.IntegerProperty()  # user's last tweet timestamp

def get_access(username):
    # get access token and token_secret by username
    
    res = UserModel.gql('''
        WHERE
            username = :1
        LIMIT
            1
    ''', username.lower()).get()

    if not res:
        access_token = None
        access_secret = None
    else:
        access_token = res.token
        access_secret = res.secret
        
    return access_token, access_secret
    
def save_access(username, token, secret):
    # save access token and token_secret by username
    
    res = UserModel.all().filter('username =', username.lower())
    if res.count() > 0:
        db.delete(res)
    
    auth = UserModel(username=username.lower(),
                     token=token,
                     secret=secret)
    auth.put()
    
def get_model(username):
    # get model by username
    
    res = UserModel.gql('''
        WHERE
            username = :1
        LIMIT
            1
    ''', username.lower()).get()
    
    if not res:
        return None
    else:
        return res

def get_all_model():
    # get all model
    
    return UserModel.all()

def delete_model(username, token, secret):
    # delete model by username
    # verify by token and token_secret
    
    res = UserModel.all().filter('username =', username.lower()).filter('token =', token).filter('secret =', secret)
    
    if res.count() > 0:
        db.delete(res)
    else:
        logging.error("delete_model mismatch. username: " + username)
        logging.error("delete_model mismatch. token: " + token)
        logging.error("delete_model mismatch. secret: " + secret)

# ==============================================================
    
class PosterModel(db.Model):
    username    = db.StringProperty(required=True)
    token       = db.StringProperty(required=True)  # Access token
    secret      = db.StringProperty(required=True)  # Access token secret
    auth_time   = db.DateTimeProperty(auto_now_add=True)

def get_poster():
    # get poster model
    
    res = PosterModel.all().get()

    if not res:
        return None
    else:
        return res

def save_poster(username, token, secret):
    # save access token and token_secret by username
    
    res = PosterModel.all()
    if res.count() > 0:
        db.delete(res)
    
    auth = PosterModel(username=username.lower(),
                     token=token,
                     secret=secret)
    auth.put()

def has_poster():
    # check if no poster exist
    
    res = PosterModel.all()
    if res.count() > 0:
        return True
    return False 