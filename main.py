# -*- coding: utf-8 -*-
# @copyright:	GPL v3
# @author:	Dazzy Ding (dazzyd, @ks_magi)

import webapp2
import logging

import oauth, gdb

CONSUMER_KEY = 'CjUSfZ1IDHrBe9dLu5Viyw'
CONSUMER_SECRET = '3iUPswMl97gxxirCK5rVN3MvNqM5AcB1dTnxlmdMyQ'
VERSION = 'dev'
TWEET_MIN = 16
AUTH_KEY = '0x0'

class OauthS(webapp2.RequestHandler):
	def get(self, mode=''):
		client = oauth.TwitterClient( CONSUMER_KEY, CONSUMER_SECRET, "%s/oauth/verify" % self.request.host_url )
		
		if mode=='auth':
			if self.request.get('key','QwQ') == AUTH_KEY:
				# step C Consumer Direct User to Service Provider
				try:
					url = client.get_authorization_url()
					self.redirect(url)
				except Exception,error_message:
					logging.error("/oauth/auth Error:")
					logging.error(error_message)
					self.response.out.write( error_message )
				
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
				
			except Exception,error_message:
				logging.error("/oauth/verity Error:")
				logging.error("auth_token: %s\nauth_verifier: %s" % (auth_token, auth_verifier))
				logging.error("user_id: %s\ntoken: %s\nsecret: %s" % (user_id, access_token, access_secret))
				logging.error( error_message )
				self.response.out.write( error_message )
			
		if mode=='succ':
			self.response.out.write( 'You have authorize this app. <br/>$username: %s' % self.request.get("user_id") )
		

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
		(r'/.*',		DefaultS)
		])