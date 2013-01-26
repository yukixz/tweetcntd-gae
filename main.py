# -*- coding: utf-8 -*-
# @copyright:	GPL v3
# @author:	Dazzy Ding (dazzyd, @ks_magi)

import webapp2
import logging
import oauth, gdb

CONSUMER_KEY = 'CjUSfZ1IDHrBe9dLu5Viyw'
CONSUMER_SECRET = '3iUPswMl97gxxirCK5rVN3MvNqM5AcB1dTnxlmdMyQ'
TWEET_MIN = 16
AUTH_KEY = '0x0'
VERSION = 'dev'

class OauthS(webapp2.RequestHandler):
	def get(self, mode=''):
		client = oauth.TwitterClient( CONSUMER_KEY, CONSUMER_SECRET, "%s/oauth/verify" % self.request.host_url )
		
		if mode=='auth':
			if self.request.get('key','QwQ') == AUTH_KEY:
				# step C Consumer Direct User to Service Provider
				try:
					url = client.get_authorization_url()
					self.redirect(url)
				except Exception, msg:
					logging.error("/oauth/auth:")
					logging.error(msg)
					self.response.out.write( msg )
				
			else:
				# Redirect unauth user to main page
				self.redirect(self.request.host_url)
			
		if mode=='verify':
			# step D Service Provider Directs User to Consumer
			auth_token = self.request.get("oauth_token")
			auth_verifier = self.request.get("oauth_verifier")
			
			# step E Consumer Request Access Token 
			# step F Service Provider Grants Access Token
			try:
				user_id, access_token, access_secret = client.get_access_token(auth_token, auth_verifier)
				gdb.save_user(int(user_id), access_token, access_secret)
				self.redirect( "%s/oauth/succ?user_id=%s" % (self.request.host_url, user_id) )
				
			except Exception, msg:
				logging.error("/oauth/verity:")
				logging.error("auth_token: %s\nauth_verifier: %s" % (auth_token, auth_verifier))
				logging.error("user_id: %s\ntoken: %s\nsecret: %s" % (user_id, access_token, access_secret))
				logging.error( msg )
				self.response.out.write( msg )
			
		if mode=='succ':
			self.response.out.write( 'You have authorize this app. <br/>$username: %s' % self.request.get("user_id") )
		
	
class PostS(webapp2.RequestHandler):
	def get(self):
		# Ridirect to host if not call by cron.yaml
		if not self.request.headers.has_key( "X-AppEngine-Cron" ) or not self.request.headers['X-AppEngine-Cron'] :
			self.redirect(self.request.host_url)
			return
		
		all_users = gdb.all_users()
		client = oauth.TwitterClient( CONSUMER_KEY, CONSUMER_SECRET, "%s/oauth/verify" % self.request.host_url )
		
		for user in all_users:
			# Load count and tweet it.
			try:
				(sum, re, rt, rts, last) = gdb.load_count(user.user_id)
			except Exception, msg:
				logging.error("/post:gdb")
				logging.error("user_id: %d", user.user_id)
				logging.error(msg)
			try:
				client.tweet(user.token, user.secret, (sum, re, rt, rts))
			except Exception, msg:
				logging.error("/post:tweet")
				logging.error("user_id: %d", user.user_id)
				logging.error(msg)
			

def format_date(ss, MONTH2NUMBER={'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06', 'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}):
	return ''.join([ ss[26:30],MONTH2NUMBER[ss[4:7]],ss[8:10],ss[11:13],ss[14:16],ss[17:19] ])

class UpdateS(webapp2.RequestHandler):
	def get(self):
		pass
	

class DefaultS(webapp2.RequestHandler):
	def get(self):
		message = '''
<html>
	<head><title>tweetcntd</title></head>
	<body>
		<h2>tweetcntd #version#</h2>
		<p>Non-Public, but <a href="https://github.com/dazzyd/tweetcntd">Open Source</a>.</p>
		<p><i>统计时段：-0:30~23:30、推数 #MIN# 以下不发统计<br/>
		Powered by <a href="https://twitter.com/ks_magi">@ks_magi</a></i></p>
	</body>
</html>'''
		self.response.out.write( message.replace('#version#', VERSION).replace('#MIN#', str(TWEET_MIN)) )

app = webapp2.WSGIApplication([
		(r'/oauth/(.*)',OauthS	),
		(r'/post',		PostS	),
		(r'/update',	UpdateS	),
		(r'/.*',		DefaultS)
		])