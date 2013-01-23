# -*- coding: utf-8 -*-
# @copyright:	GPL v3
# @author:	Dazzy Ding (dazzyd, @ks_magi)

from google.appengine.ext import webapp
import wsgiref.handlers, logging
from google.appengine.api import urlfetch
from django.utils import simplejson as json
from datetime import *
import re

import oauth
from database import *

CONSUMER_KEY = '{{CONSUMER_KEY}}'
CONSUMER_SECRET = '{{CONSUMER_SECRET}}'

# constant
VERSION = 'v0.1.0'
TWEET_MIN = 16
AUTH_KEY = '0v0'
POSTER_KEY = 'QVAr2z@p43rZ!*EuIhG173$hE21%tHW8rI7zrg$&Qi^z38^s@Cv*e#ct1viT@PON'


class OauthS(webapp.RequestHandler):
	def get(self, mode=""):
		client = oauth.TwitterClient( CONSUMER_KEY, CONSUMER_SECRET, ("%s/oauth/verify" % self.request.host_url) )
		
		if mode=='auth' :
		  # Redirect unauth user to use the app
		  if self.request.get('key','0x0') != AUTH_KEY:
			self.redirect(self.request.host_url)
			
		  else:
			# step C Consumer Direct User to Service Provider
			try:
				url = client.get_authorization_url()
				self.redirect(url)
			except Exception,error_message:
				self.response.out.write( error_message )
		
		elif mode=='verify' :
			# step D Service Provider Directs User to Consumer
			auth_token = self.request.get("oauth_token")
			auth_verifier = self.request.get("oauth_verifier")

			# step E Consumer Request Access Token 
			# step F Service Provider Grants Access Token
			try:
				access_token, access_secret, screen_name = client.get_access_token(auth_token, auth_verifier)
				
				# Save the auth token and secret in our database.
				save_access(screen_name, access_token, access_secret) 
				self.redirect( "%s/oauth/succ?username=%s" % (self.request.host_url, screen_name) )  
				
			except Exception,error_message:
				logging.error("oauth_token: %s" % auth_token)
				logging.error("oauth_verifier: %s" % auth_verifier)
				logging.error( error_message )
				self.response.out.write( error_message )
		
		elif mode=='succ' :
			self.response.out.write( 'You have authorize this app. Thanks for using.<br/>$username: %s' % self.request.get("username") )
		
		else:
			self.redirect(self.request.host_url)
	
	def post(self):
		pass

class PosterS(webapp.RequestHandler):
	def get(self, mode=""):
		client = oauth.TwitterClient( CONSUMER_KEY, CONSUMER_SECRET, ("%s/poster/verify" % self.request.host_url) )
		
		if mode=='auth' :
		  # Redirect unauth user to use auth poster
		  if self.request.get('key','0x0') != 'QVAr2z@p43rZ!*EuIhG173$hE21%tHW8rI7zrg$&Qi^z38^s@Cv*e#ct1viT@PON' or has_poster():
			self.response.out.write( 'Auth Failed. Please check the database.' )
			
		  else:
			# step C Consumer Direct User to Service Provider
			try:
				url = client.get_authorization_url()
				self.redirect(url)
			except Exception,error_message:
				self.response.out.write( error_message )
		
		elif mode=='verify' :
			# step D Service Provider Directs User to Consumer
			auth_token = self.request.get("oauth_token")
			auth_verifier = self.request.get("oauth_verifier")

			# step E Consumer Request Access Token 
			# step F Service Provider Grants Access Token
			try:
				access_token, access_secret, screen_name = client.get_access_token(auth_token, auth_verifier)
				
				# Save the auth token and secret in our database.
				save_poster(screen_name, access_token, access_secret) 
				self.redirect( "%s/poster/succ?username=%s" % (self.request.host_url, screen_name) )  
				
			except Exception,error_message:
				logging.error("oauth_token: %s" % auth_token)
				logging.error("oauth_verifier: %s" % auth_verifier)
				logging.error( error_message )
				self.response.out.write( error_message )
		
		elif mode=='succ' :
			self.response.out.write( 'Poster auth.<br/>$username: %s' % self.request.get("username") )
		
		else:
			self.redirect(self.request.host_url)
	
	def post(self):
		pass


def get_formattime_by_str( ss ):
	MONTH2NUMBER = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06',
					'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
	return ''.join([ ss[26:30],MONTH2NUMBER[ss[4:7]],ss[8:10],ss[11:13],ss[14:16],ss[17:19] ])

class CronS(webapp.RequestHandler):
	# Get an user's timeline statistics
	#   not need since_id and max_id from v010 (add it back on later version?)
	def single( self, client, user ):
		####	SETTING		####
		TWEET_BLOCK = '100' # str for %s
		PATTERN_RE = re.compile( r'^(@\w+)\b.*$' )
		PATTERN_RT = re.compile( r'^.*?(RT ?@\w+)\b.*$' )
		
		# return 0, 0, 0, 0  when error
		timeline = []
		
		# loop vars
		stime_dt = datetime.combine(date.today(),time(0,0,0)) - timedelta(hours=8,minutes=30) # midnight @ UTC+0830 (from -0:30 to 23:30)
		stime = stime_dt.strftime("%Y%m%d%H%M%S")
		quit = 0
		maxid = 0
		api_request = 0 # limit the api call. in case of mistake which cause endless loop
		
		# read timeline  and duel error
		while ( len(timeline) < 1000 and api_request < 32 ):
			api_request+=1
			response = client.get_user_timeline( user, TWEET_BLOCK, max_id=maxid )
			
			# 200
			if response.status_code == 200:
				res = json.loads( response.content )
				le = len(res)-1
				maxid = res[le]['id'] - 1
				
				# if the last tweet is posted today, skip this block
				if get_formattime_by_str(res[le]["created_at"]) > stime:
					timeline.extend( res )
					continue # while  len(timeline) < ~
				
				i = 0
				while i < le:
					if stime > get_formattime_by_str(res[i]["created_at"]):
						quit = 1
						break # while  i < ~
					i+=1
				# end while  i < ~
				
				if quit:
					timeline.extend( res[0:i] )
					break # while  len(timeline) < ~
				else:
					timeline.extend( res )
				#end if  quit
			
			else:
				# 401 
				if (response.status_code == 401):
					res = json.loads( response.content )
					
					# response.content = {"errors":[{"message":"Invalid or expired token","code":89}]}
					if res['errors'][0]['code'] == 89:
						logging.error( "Revoke Aceess: %s"  % user.username )
						delete_model( user.username, user.token, user.secret )
					
					# response.content = {"errors":[{"message":"Rate limit exceeded","code":88}]}
					if res['errors'][0]['code'] == 32:
						logging.error( "Could not authenticate: %s"  % user.username )
					
					# response.content = {"errors":[{"message":"Rate limit exceeded","code":88}]}
					if res['errors'][0]['code'] == 88:
						logging.error( "Rate limit exceeded: %s"  % user.username )
					
				else:
					logging.error( "Unknown Error: %s"  % user.username )
				
				quit = 2
				logging.error( "token: %s \nsecret: %s" % (user.token, user.secret) )
				logging.error( "response.status_code: %s" % str(response.status_code) )
				logging.error( "response.content: %s" % response.content )
				break # while  len(timeline) < ~
					
		# end while 
		
		# raise error when generating timeline
		if quit==2:
			logging.debug( "user:%s QUIT 2" % user.username )
			return 0, 0, 0, 0
		
		# count tweets' types
		sum = len(timeline)
		sum_rts = 0
		sum_re = 0
		sum_rt = 0
		for tweet in timeline:
			if tweet.has_key( "retweeted_status" ):
				sum_rts += 1
			elif PATTERN_RE.match( tweet["text"] ):
				sum_re += 1
			elif PATTERN_RT.match( tweet["text"] ):
				sum_rt +=1
			else:
				pass
			#end if
		#end for  in timeline
		
		return sum, sum_re, sum_rt, sum_rts
	
	
	def get(self, mode=""):
	  # verify if call by cron.yaml
	  if self.request.headers.has_key( "X-AppEngine-Cron" ) and self.request.headers['X-AppEngine-Cron'] :
	  # if True :   #### Debug line
		
		client = oauth.TwitterClient( CONSUMER_KEY, CONSUMER_SECRET, ("%s/oauth/verify" % self.request.host_url) )
		
		# make a tweet containing counting result
		if mode=='tweet' :
			all_users = get_all_model()
			poster = get_poster()
			for user in all_users:
				
				# check if local token invalid
				if (not user.token) or (not user.secret) :
					logging.error( "cron/tweet call a unavailable username: %s" % username ) 
				else:
					# call single function to process 
					sum, re, rt, rts = self.single( client, user )
					# send the tweet
					# Tweet when sum >= TWEET_MIN
					if sum >= TWEET_MIN: # valid return or no new tweet ?
						client.tweet( user, poster, sum, re, rt, rts )
					else:
						logging.debug( "No posting" )
						logging.debug( "user: %s\nsum: %s" % (user.username, str(sum)) )
			# end for  in all_users
			
		elif mode=='update':
			pass
		
		# create the instance for quick processing /cron/tweet
		elif mode=='preheat':
			pass
		
		# Debug code block
		elif mode=='debug':
			# pass
			user = get_model('ks_magi')
			sum, re, rt, rts = self.single( client, user )
			self.response.out.write( "<p>%s: %d.(%d,%d,%d)</p>" % (user.username, sum, re, rt, rts) )
		
		else :
			# mode undefined:
			# logging.error( "Unknown Cron action(mode): " + mode )
			self.redirect(self.request.host_url)
	  else:
		# not call by cron.yaml
		self.redirect(self.request.host_url)
	
	def post(self):
		pass



class DefaultS(webapp.RequestHandler):
	def get(self, mode=""):
		message = '''
<html>
	<head><title>tweetcntd</title></head>
	<body>
		<h2>tweetcntd #version#</h2></p>
		<p>Non-Public.</p>
		<p><i>统计时段：-0:30~23:30、推数 #MIN# 以下不发统计<br/>
		Powered by <a href="https://twitter.com/ks_magi">@ks_magi</a></i></p>
	</body>
</html>'''
		self.response.out.write( message.replace('#version#', VERSION).replace('#MIN#', str(TWEET_MIN)) )
	
	def post(self):
		pass

def main():
	# /oauth/auth	   ## oauth request
	# /oauth/verify	 ## oauth callback
	# /cron/tweet	   ## tweet daily count, call-only by cron.yaml
	# /cron/update	  ## update tweet count, call-only by cron.yaml
	# /poster/auth	  ## poster request
	# /poster/verify	## poster callback
	
	application = webapp.WSGIApplication( [
		(r'/oauth/(.*)',	OauthS  ),
		(r'/cron/(.*)',	 CronS   ),
		(r'/poster/(.*)',   PosterS ),
		(r'/(.*)',		  DefaultS)
		], debug=True)
	wsgiref.handlers.CGIHandler().run(application)
	
if __name__ == "__main__":
	main()
