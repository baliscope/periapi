#!/usr/bin/env python3
"""
Periscope API for the masses
"""
# pylint: disable=broad-except,import-error

from urllib.parse import parse_qsl

import json

import oauth2 as oauth
import requests

from path import path
from .logging import logging

RTOKEN_URL = 'https://api.twitter.com/oauth/request_token?oauth_callback=oob'
ATOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTH_URL = 'https://api.twitter.com/oauth/authorize'
VERIFY_URL = 'https://api.twitter.com/1.1/account/verify_credentials.json?'\
             'include_entities=false&skip_status=true'
PERI_LOGIN_URL = 'https://api.periscope.tv/api/v2/loginTwitter'


class PeriConfig(dict):
    """Persistent peri config dict"""
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.file = path(".peri.conf")
        if not self.file.isfile():
            self.file = path("~/.peri.conf").expand()
        if self.file.isfile():
            self.load()

    def load(self):
        """Load the config from file"""
        with self.file.open("r") as inp:
            self.update(json.load(inp))

    def write(self):
        """Persist the config to file"""
        tmp = path(self.file + ".tmp")
        try:
            with tmp.open("w") as tmpp:
                json.dump(self, tmpp, indent=2)
            try:
                self.file.unlink()
            except Exception:
                pass
            tmp.move(self.file)
        finally:
            try:
                tmp.unlink()
            except Exception:
                pass


class LoginSession(requests.Session):
    """Provides an authenticated requests.Session"""

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        # Periscope API keys
        config = self.config = PeriConfig()
        self.headers.update({
            'User-Agent': 'Periscope/3313 (iPhone; iOS 7.1.1; Scale/2.00)',
            "Accept-Encoding": "gzip, deflate",
            })

        cookie = config.get("cookie", "")

        # If Periscope login process doesn't work with the stored credentials
        # or if no stored credentials existed in the first place, then we need
        # to login to Twitter and grab a new auth token and secret.
        if not cookie:
            cookie = self.authenticate()
        self.cookie = cookie
        self.uid = config["uid"]
        self.name = config["name"]

        if not self.cookie:
            raise ValueError("Failed to obtain cookie")

    def authenticate(self):
        """Authenticate with the twitter/periscope API"""

        config = self.config
        cons_key = config.get("consumer_key")
        cons_sec = config.get("consumer_secret")
        if not cons_key or not cons_sec:
            cons_key = input("Please input the Periscope consumer key: ")
            cons_sec = input("please input the Periscope consumer secret: ")

        # Set up our OAuth request headers, sign the request, etc.
        consumer = oauth.Consumer(cons_key, cons_sec)
        client = oauth.Client(consumer)

        # Make initial OAuth request to Twitter (gets us a temporary token
        # used for the authorization process)
        resp, content = client.request(RTOKEN_URL, 'GET')
        if resp['status'] != '200':
            raise IOError(
                'Could not initialize authentication process with Twitter. Check'
                ' consumer key/consumer secret validity and try again.')

        # Parse the response from Twitter's API and use it to load the
        # authorization page
        request_token = dict(parse_qsl(content.decode('utf-8')))
        print('open this:\n{0}?oauth_token={1}'.format(
            AUTH_URL, request_token['oauth_token']))

        # Get the Twitter PIN number from the user
        oauth_verifier = input('Please enter the PIN: ')

        # Prepare our second OAuth request now that we have authorization
        token = oauth.Token(
            request_token['oauth_token'],
            request_token['oauth_token_secret']
            )
        token.set_verifier(oauth_verifier)
        client = oauth.Client(consumer, token)

        # Make request and parse the response from Twitter's API. The OAuth key
        # we need to login to Periscope is in access_token['oauth_token'] and
        # the secret is in access_token['oauth_token_secret']
        resp, content = client.request(ATOKEN_URL, 'POST')
        if resp['status'] != '200':
            raise IOError(
                'Could not complete authentication process with Twitter')
        access_token = dict(parse_qsl(content.decode('utf-8')))

        # Get the User ID and Username from Twitter
        token = oauth.Token(
            access_token['oauth_token'],
            access_token['oauth_token_secret']
            )
        client = oauth.Client(consumer, token)
        resp, content = client.request(VERIFY_URL, 'GET')
        if resp['status'] != '200':
            raise IOError(
                'Could not complete verification process with Twitter')
        user_info = json.loads(content.decode('utf-8'))

        config["token"] = access_token["oauth_token"]
        config["token_secret"] = access_token["oauth_token_secret"]
        config["name"] = user_info["screen_name"]
        config["uid"] = user_info["id_str"]
        logging.debug("access %r", access_token)
        logging.debug("user_info %r", user_info)

        login_payload = {
            'session_secret': config["token_secret"],
            'session_key': config["token"],
            'user_id': config["uid"],
            'user_name': config["name"],
            'phone_number': '',
            'vendor_id': '',
            'bundle_id': 'com.bountylabs.periscope',
        }

        # Send payload to login to Periscope using the credentials obtained
        resp = self.post(PERI_LOGIN_URL, json=login_payload)
        if resp.status_code != 200:
            raise IOError('Could not complete authentication with Periscope')
        cookie = config["cookie"] = resp.json()["cookie"]
        config.write()
        return cookie

    def post_peri(self, *args, **kw):
        """Make a post to the peri API"""

        # stuff in the cookie, if there is a payload
        payload = kw.get("json")
        if payload is not None:
            payload["cookie"] = self.cookie
            kw["json"] = payload
            logging.debug("payload: %r", payload)
        resp = self.post(*args, **kw)
        if resp.status_code != 200:
            raise IOError("API call failed: {}".format(resp.status_code))
        return resp.json()
