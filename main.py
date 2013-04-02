# -*- coding: utf-8 -*-
# @copying:	GPL v3
# @author:	Dazzy Ding (dazzyd, @ks_magi)

import webapp2
import logging
import json, re
from datetime import *
import oauth, gdb

# ### SETTING ###
AUTH_KEY = '0x0'
VERSION = 'ver 0.2.2'
CONSUMER_KEY = 'CjUSfZ1IDHrBe9dLu5Viyw'
CONSUMER_SECRET = '3iUPswMl97gxxirCK5rVN3MvNqM5AcB1dTnxlmdMyQ'
TWEET_MIN = 16
TIMEZONE = 8
PERIOD_TIME = "153000" # 233000 - 080000
def get_period_time():
	''' Returns the farmatted time string of countting period. '''
	now_tz = datetime.now() + timedelta(hours=TIMEZONE)
	end = now_tz.strftime("%Y%m%d") + PERIOD_TIME
	start = (now_tz - timedelta(hours=24)).strftime("%Y%m%d") + PERIOD_TIME
	return start, end


class NameS(webapp2.RequestHandler):
	def get(self):
		# Ridirect to host if not call by cron.yaml
		if not (self.request.headers.has_key( "X-AppEngine-Cron" ) and self.request.headers['X-AppEngine-Cron']) :
			self.redirect(self.request.host_url)
			return
		
		all_users = gdb.all_users()
		client = oauth.TwitterClient( CONSUMER_KEY, CONSUMER_SECRET, "%s/oauth/verify" % self.request.host_url )
		
		for user in all_users:
			response = client.load_profile(user.token, user.secret)
			if response.status_code != 200:	#### Should be modified.
				logging.error("load_profile()")
				logging.error("status_code: %d\ncontent: %s" % (response.status_code, response.content) )
				continue # while
			
			profile = json.loads(response.content)
			gdb.save_name(user, profile["screen_name"])


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
			self.response.out.write( 'You have authorize this app. <br/>Your Twitter id: %s' % self.request.get("user_id") )
		

class PostS(webapp2.RequestHandler):
	def egg(self, sum, re, rt, rts, id):
		ra = id % 12 + 8
		return -sum*ra, -re*ra, -rt*ra, -rts*ra
	
	def get(self):
		# Ridirect to host if not call by cron.yaml
		if not (self.request.headers.has_key( "X-AppEngine-Cron" ) and self.request.headers['X-AppEngine-Cron']) :
			self.redirect(self.request.host_url)
			return
		
		all_users = gdb.all_users()
		client = oauth.TwitterClient( CONSUMER_KEY, CONSUMER_SECRET, "%s/oauth/verify" % self.request.host_url )
		today = date.today()
		egg = 1 if (today.month==4 and today.day==1) else 0
		
		for user in all_users:
			# Load count and tweet it.
			(sum, re, rt, rts, last) = gdb.load_count(user)
			gdb.reset_count(user)
			
			if sum > TWEET_MIN:
				if egg: (sum, re, rt, rts) = self.egg(sum, re, rt, rts, user.user_id)
				tweet = u"@%s 本日共发 %d 推，其中 @ %d 推（%.1f%%）、RT @ %d 推（%.1f%%）、Retweet %d 推（%.1f%%） #tweetcntd" %\
						( user.screen_name, sum, re, float(re)/sum*100 , rt, float(rt)/sum*100, rts, float(rts)/sum*100 )
				client.tweet(user.token, user.secret, tweet)
	

def format_time(ss, MONTH2NUMBER={'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06', 'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}):
	return ''.join(( ss[26:30],MONTH2NUMBER[ss[4:7]],ss[8:10],ss[11:13],ss[14:16],ss[17:19] ))

class UpdateS(webapp2.RequestHandler):
	def get(self):
		# Ridirect to host if not call by cron.yaml
		if not (self.request.headers.has_key( "X-AppEngine-Cron" ) and self.request.headers['X-AppEngine-Cron']) :
			self.redirect(self.request.host_url)
			return
		
		# init constant
		all_users = gdb.all_users()
		client = oauth.TwitterClient( CONSUMER_KEY, CONSUMER_SECRET, "%s/oauth/verify" % self.request.host_url )
		start_time, end_time = get_period_time()
		PATTERN_RE = re.compile( r'^(@\w+)\b.*$' )
		PATTERN_RT = re.compile( r'^.*?(RT ?@\w+)\b.*$' )
		
		for user in all_users:
			# init user's status
			(sum, sum_re, sum_rt, sum_rts, since_id) = gdb.load_count(user)
			skip = 0
			max_id = None
			timeline = []
			
			## fixed new user
			if since_id==0:
				block = [{"created_at":"Tue Feb 14 00:00:00 +0000 9999"}]	## Magic Number
			
			# Generate user's new tweets' blocks
			while (since_id != max_id) if since_id>0 else (format_time(block[len(block)-1]["created_at"]) > start_time):
				# Get the tweet block CONTAINS tweet of since_id.
				response = client.load_usrtl(user.token, user.secret, since_id-1, max_id, 200)
				if response.status_code != 200:	#### Should be modified.
					logging.error("load_usrtl()")
					logging.error("status_code: %d\ncontent: %s" % (response.status_code, response.content) )
					break # while
				
				block = json.loads(response.content)
				len_1 = len(block)-1
				if len_1:
					timeline.extend(block[0:len_1])
					max_id = block[len_1]["id"]
				else:
					break # while
			
			# Count user's tweets
			for tweet in timeline:
				tweet_time = format_time(tweet["created_at"])
				if tweet_time > end_time:
					skip +=1
				elif tweet_time > start_time:
					sum +=1
					if tweet.has_key( "retweeted_status" ):
						sum_rts += 1
					elif PATTERN_RE.match( tweet["text"] ):
						sum_re += 1
					elif PATTERN_RT.match( tweet["text"] ):
						sum_rt +=1
				else:
					break # for
			
			# Save user's status
			if len(timeline):
				logging.debug("$ %d: %d(%d,%d,%d), %d" % (user.user_id, sum, sum_re, sum_rt, sum_rts, timeline[skip]["id"]) )
				gdb.save_count(user, sum, sum_re, sum_rt, sum_rts, timeline[skip]["id"])
	

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
		(r'/update',	UpdateS	),
		(r'/post',		PostS	),
		(r'/name',		NameS	),
		(r'/oauth/(.*)',OauthS	),
		(r'/.*',		DefaultS)
		])