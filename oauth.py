# -*- coding: utf-8 -*-
# @copyright:	GPL v3
# @author:	Dazzy Ding (dazzyd, @ks_magi)

from cgi import parse_qs, parse_qsl
from hashlib import sha1, sha256, sha512
from hmac import new as hmac
from random import getrandbits
from time import time
from urllib import urlencode,quote as urlquote,unquote as urlunquote
import urlparse, logging, base64
from google.appengine.api import urlfetch


class OAuthClient():
	def __init__(self, consumer_key, consumer_secret, request_url, access_url, callback_url=None):
		''' Constructor '''

		self.consumer_key = consumer_key
		self.consumer_secret = consumer_secret
		self.request_url = request_url
		self.access_url = access_url
		self.callback_url = callback_url
	
	def prepare_request(self, url, token="", secret="", additional_params={}, method=urlfetch.GET):
		''' Prepare Request
		Prepare an authenticated request to OAuth protected resource.
		Returns the payload of the request.
		'''
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
		else:
			params["oauth_callback"] = self.callback_url
		
		if additional_params:
			params.update(additional_params)
		
		for k,v in params.items():
			if isinstance(v, unicode):
				params[k] = v.encode('utf-8')
			if type(v) is str:
				params[k] = params[k].replace('~','~~~')
		
		# Join all of the params together.
		params_str = '&'.join([ '%s=%s' % (encode(k), encode(params[k]))
								for k in sorted(params) ])
		
		# Join the entire message together per the OAuth specification.
		message = '&'.join([ 'GET' if method==urlfetch.GET else 'POST',
								encode(url), encode(params_str) ])
		
		# Create a HMAC-SHA1 signature of the message.
		key = '%s&%s' % (self.consumer_secret, secret)
		message = message.replace('%257E%257E%257E', '~')
		signature = hmac(key, message, sha1)
		digest_base64 = signature.digest().encode("base64").strip()
		params["oauth_signature"] = digest_base64
		
		# Construct the request payload and return it
		return urlencode(params).replace('%7E%7E%7E', '~')
	
	def make_async_request(self, url, token="", secret="", additional_params={}, protected=False, method=urlfetch.GET):
		''' Make Request
		Make an authenticated request to OAuth protected resource.
		If protected is equal to True, the Authorization: OAuth header will be set.
		A urlfetch response object is returned.
		'''
		(scm, netloc, path, params, query, _) = urlparse.urlparse(url)
		query_params = None
		
		if query:
			query_params = dict([ (k,v) for k,v in parse_qsl(query) ])
			additional_params.update(query_params)
		url = urlparse.urlunparse(('https', netloc, path, params, "", ""))
		
		payload = self.prepare_request(url, token, secret, additional_params, method)
		if method == urlfetch.GET:
			url = "%s?%s" % (url, payload)
		headers = {"Authorization": "OAuth"} if protected else {}
		
		rpc = urlfetch.create_rpc(deadline=2.0)
		urlfetch.make_fetch_call(rpc, url, method=method, headers=headers, payload=payload)
		return rpc
	
	def make_request(self, url, token="", secret="", additional_params={}, protected=False, method=urlfetch.GET):
		data = self.make_async_request(url, token, secret, additional_params, protected, method).get_result()
		return data
	
	def get_authorization_url(self):
		''' Get Authorization URL
		Returns a service specific URL which contains an auth token.
		The user should be redirected to this URL
		so that they can give consent to be logged in.
		'''
		raise NotImplementedError, "Must be implemented by a subclass"
	
	def get_access_token(self, auth_token, auth_verifier):
		auth_token = urlunquote(auth_token)
		auth_verifier = urlunquote(auth_verifier)
		
		response = self.make_request( self.access_url, 
										token=auth_token,
										additional_params={"oauth_verifier": auth_verifier} )
		result = parse_qs(response.content)
		return result["user_id"][0], result["oauth_token"][0], result["oauth_token_secret"][0]
	
	def _get_auth_token(self):
		''' Get Authorization Token
		Gets the authorization token and secret from service.
		Returns the auth token.
		'''
		response = self.make_request(self.request_url)
		result = parse_qs(response.content)
		return result["oauth_token"][0]


class TwitterClient(OAuthClient):
	def __init__(self, consumer_key, consumer_secret, callback_url):
		''' Constructor '''
		OAuthClient.__init__(self,
							consumer_key,
							consumer_secret,
							"https://api.twitter.com/oauth/request_token",
							"https://api.twitter.com/oauth/access_token",
							callback_url)
	
	def get_authorization_url(self):
		''' Get Authorization URL '''
		token = self._get_auth_token()
		return "https://api.twitter.com/oauth/authorize?oauth_token=%s" % token
	
	def tweet(self, token, secret, tweet):
		''' Make tweet '''
		try:
			response = self.make_request( "https://api.twitter.com/1.1/statuses/update.json", token, secret, protected=True,
											additional_params={"status": tweet.encode("utf-8")}, method=urlfetch.POST )
		except Exception, msg:
			logging.error("client.tweet():")
			logging.error("token: %s\nsecret: %s", (token. secret) )
			logging.error("response.status_code: %d\nresponse.content: %s" % (response.status_code, response.content) )
			logging.error("message: %s" % msg)
		
		return response
	
	def load_usrtl(self, token, secret, since_id, max_id, count):
		''' Load User Timeline 
		response will contain one tweet at least( since_id ).
		'''
		params = {}
		params.update( {"since_id":since_id} if since_id else {} )
		params.update( {"max_id":max_id} if max_id else {} )
		params.update( {"count":count} if count else {} )
		
		try:
			response = self.make_request( "https://api.twitter.com/1.1/statuses/user_timeline.json?trim_user=1&%s" % urlencode(params),
											token, secret, protected=True, method=urlfetch.GET )
		except Exception, msg:
			logging.error("client.load_usrtl():")
			logging.error("token: %s\nsecret: %s", (token. secret) )
			logging.error("response.status_code: %d\nresponse.content: %s" % (response.status_code, response.content) )
			logging.error("message: %s" % msg)
		
		return response
	