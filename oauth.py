# -*- coding: utf-8 -*-
# Copyright under the latest Apache License 2.0

from google.appengine.api import urlfetch

from cgi import parse_qs,parse_qsl
from hashlib import sha1, sha256, sha512
from hmac import new as hmac
from random import getrandbits
from time import time
from urllib import urlencode,quote as urlquote,unquote as urlunquote
import urlparse, logging, base64
from Crypto.Cipher import AES

class OAuthException(Exception):
	pass


class OAuthClient():

	def __init__(self, consumer_key, consumer_secret, request_url, access_url, callback_url=None):
		""" Constructor."""

		self.consumer_key = consumer_key
		self.consumer_secret = consumer_secret
		self.request_url = request_url
		self.access_url = access_url
		self.callback_url = callback_url

	def prepare_request(self, url, token="", secret="", additional_params=None,
					  method=urlfetch.GET):
		"""Prepare Request.

		Prepares an authenticated request to any OAuth protected resource.

		Returns the payload of the request.
		"""

		def encode(text):
		  return urlquote(str(text), "")

		params = {
			"oauth_consumer_key": self.consumer_key,
			"oauth_signature_method": "HMAC-SHA1",
			"oauth_timestamp": str(int(time())),
			"oauth_nonce": str(getrandbits(64)),
			"oauth_version": "1.0"
		}

		if token:
			params["oauth_token"] = token
		elif self.callback_url:
			params["oauth_callback"] = self.callback_url

		if additional_params:
			params.update(additional_params)

		for k,v in params.items():
			if isinstance(v, unicode):
				params[k] = v.encode('utf8')
			if type(v) is str:
				params[k] = params[k].replace("~","~~~")
			
		# Join all of the params together.
		params_str = "&".join(["%s=%s" % (encode(k), encode(params[k]))
							   for k in sorted(params)])

		# Join the entire message together per the OAuth specification.
		message = "&".join(["GET" if method == urlfetch.GET else "POST",
							encode(url), encode(params_str)])

		# Create a HMAC-SHA1 signature of the message.
		key = "%s&%s" % (self.consumer_secret, secret) # Note compulsory "&".
		message = message.replace('%257E%257E%257E', '~')
		signature = hmac(key, message, sha1)
		digest_base64 = signature.digest().encode("base64").strip()
		params["oauth_signature"] = digest_base64

		# Construct the request payload and return it
		return urlencode(params).replace('%7E%7E%7E', '~')
	
	
	def make_async_request(self, url, token="", secret="", additional_params=None,
				   protected=False, method=urlfetch.GET):
		"""Make Request.

		Make an authenticated request to any OAuth protected resource.

		If protected is equal to True, the Authorization: OAuth header will be set.

		A urlfetch response object is returned.
		"""
		
		(scm, netloc, path, params, query, _) = urlparse.urlparse(url)
		url = None
		query_params = None
		if query:
			query_params = dict([(k,v) for k,v in parse_qsl(query)])
			if not additional_params:   # hot fix. for NoneType obj Error
				additional_params = {}
			additional_params.update(query_params)
		url = urlparse.urlunparse(('https', netloc, path, params, '', ''))
		
		payload = self.prepare_request(url, token, secret, additional_params, method)

		if method == urlfetch.GET:
			url = "%s?%s" % (url, payload)
			payload = None
		headers = {"Authorization": "OAuth"} if protected else {}

		rpc = urlfetch.create_rpc(deadline=10.0)
		urlfetch.make_fetch_call(rpc, url, method=method, headers=headers, payload=payload)
		return rpc

	def make_request(self, url, token="", secret="", additional_params=None,
									  protected=False, method=urlfetch.GET):
		data = self.make_async_request(url, token, secret, additional_params, protected, method).get_result()
		
		if data.status_code != 200:
			logging.debug(data.status_code)
			logging.debug(url)
			logging.debug(token)
			logging.debug(secret)
			logging.debug(additional_params)
			logging.debug(data.content)
		return data
  
	def get_authorization_url(self):
		"""Get Authorization URL.

		Returns a service specific URL which contains an auth token. The user
		should be redirected to this URL so that they can give consent to be
		logged in.
		"""

		raise NotImplementedError, "Must be implemented by a subclass"

	def get_access_token(self, auth_token, auth_verifier):
		auth_token = urlunquote(auth_token)
		auth_verifier = urlunquote(auth_verifier)

		response = self.make_request(self.access_url,
								token=auth_token,
								additional_params={"oauth_verifier": auth_verifier}
								)

		# Extract the access token/secret from the response.
		result = self._extract_credentials(response)
		return result['token'], result['secret'],result['screen_name']

	def _get_auth_token(self):
		"""Get Authorization Token.

		Actually gets the authorization token and secret from the service. The
		token and secret are stored in our database, and the auth token is
		returned.
		"""
		response = self.make_request(self.request_url)
		result = self._extract_credentials(response)

		auth_token = result["token"]
		auth_secret = result["secret"]

		return auth_token

	def _extract_credentials(self, result):
		"""Extract Credentials.

		Returns an dictionary containing the token and secret (if present).
		Throws an Exception otherwise.
		"""

		token = None
		secret = None
		screen_name = None
		parsed_results = parse_qs(result.content)

		if "oauth_token" in parsed_results:
			token = parsed_results["oauth_token"][0]

		if "oauth_token_secret" in parsed_results:
			secret = parsed_results["oauth_token_secret"][0]

		if "screen_name" in parsed_results:
			screen_name = parsed_results["screen_name"][0]

		if not (token and secret) or result.status_code != 200:
			logging.error("Response Status Code is : %s" % result.status_code)
			logging.error("Could not extract token/secret: %s" % result.content)
			raise OAuthException("Problem talking to the service")

		return {
			"token": token,
			"secret": secret,
			"screen_name": screen_name
		}
	
class TwitterClient(OAuthClient):

	def __init__(self, consumer_key, consumer_secret, callback_url):
		"""Constructor."""

		OAuthClient.__init__(self,
				consumer_key,
				consumer_secret,
				"https://api.twitter.com/oauth/request_token",
				"https://api.twitter.com/oauth/access_token",
				callback_url)

	def get_authorization_url(self):
		"""Get Authorization URL."""

		token = self._get_auth_token()
		return "https://api.twitter.com/oauth/authorize?oauth_token=%s" % token

	# Request for timetime
	# auto fill request url by params 
	def get_user_timeline( self, user, size='40', max_id=0 ):
		try:
			if not max_id:
				response = self.make_request( "https://api.twitter.com/1.1/statuses/user_timeline.json?trim_user=1&count=%s" % size,
												user.token, user.secret, protected=True )
			else:
				response = self.make_request( "https://api.twitter.com/1.1/statuses/user_timeline.json?trim_user=1&count=%s&max_id=%s" % (size, str(max_id)), 
												user.token, user.secret, protected=True )
		except Exception,error_message:
			pass
		
		return response

	# Tweet the count result
	# auto fill tweet status by params 
	def tweet( self, user, poster, sum, re, rt, rts ):
		status = u"@%s 本日共发 %s 推，其中 @ %s 推（%s%%）、RT @ %s 推（%s%%）、Retweet %s 推（%s%%） #tweetcntd" % (
					user.username, sum,
											re, round(float(re)/sum*100, 1),
																rt, round(float(rt)/sum*100, 1),
																					rts, round(float(rts)/sum*100, 1) )
		try:
			response = self.make_request( "https://api.twitter.com/1.1/statuses/update.json", user.token, user.secret, protected=True,
										  additional_params={"status": (status).encode("utf-8") }, method=urlfetch.POST )
		except Exception,error_message:
			# try:
				# response = self.make_request( "https://api.twitter.com/1.1/statuses/update.json", poster.token, poster.secret, protected=True,
												  # additional_params={"status": (status).encode("utf-8") }, method=urlfetch.POST )
			# except Exception,error_message:
				# logging.error( "Tweet by poster Fail" )
				# logging.error( "user: %s\nstatus: %s" % (user.username, status) )
				# logging.error( "response.status_code: %s" % str(response.status_code) )
				# logging.error( "response.content: %s" % response.content )
			
			logging.error( "Tweet Fail" )
			logging.error( "user: %s\nstatus: %s" % (user.username, status) )
			logging.error( "response.status_code: %s" % str(response.status_code) )
			logging.error( "response.content: %s" % response.content )
	