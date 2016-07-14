#!/usr/bin/env python3
"""
The MIT License (MIT)
Copyright © 2016 Baliscope
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from urllib.parse import parse_qsl

import json
import oauth2 as oauth
import os
import requests
import webbrowser


def stash_credentials(access_token, user_info):
    with open('perikeys.txt', 'w') as f:
        f.write('Access Token: ' + access_token['oauth_token'] + '\n')
        f.write('Access Token Secret: ' + access_token['oauth_token_secret'] + '\n')
        f.write('Username: ' + user_info['screen_name'] + '\n')
        f.write('User ID: ' + user_info['id_str'] + '\n')


def check_for_stored_credentials():
    if os.path.isfile('perikeys.txt'):
        with open('perikeys.txt', mode='r') as f:
            credentials = {}
            for line in f:
                credentials[line.split(':')[0].strip()] = line.split(':')[1].strip()
        return credentials
    else:
        return False


class Login:
    def __init__(self):
        # Periscope API keys
        self._periscope_consumer_key = ''
        self._periscope_consumer_secret = ''

        self.cookie = ''
        self.header = {
            'user-agent': 'Periscope/3313 (iPhone; iOS 7.1.1; Scale/2.00)',
        }

        stored_credentials = check_for_stored_credentials()
        if stored_credentials:
            self.cookie = self._get_periscope_cookie(stored_credentials)

        # If Periscope login process doesn't work with the stored credentials or if no stored credentials
        # existed in the first place, then we need to login to Twitter and grab a new auth token and secret.
        if not self.cookie or not stored_credentials:
            access_token, user_info = self._get_twitter_credentials()
            stash_credentials(access_token, user_info)
            stored_credentials = check_for_stored_credentials()
            self.cookie = self._get_periscope_cookie(stored_credentials)

    def _get_twitter_credentials(self):

        # Twitter OAuth endpoint urls needed for getting authorization from Twitter
        request_token_url = 'https://api.twitter.com/oauth/request_token?oauth_callback=oob'
        access_token_url = 'https://api.twitter.com/oauth/access_token'
        authorize_url = 'https://api.twitter.com/oauth/authorize'
        verify_url = 'https://api.twitter.com/1.1/account/verify_credentials.json?include_entities=false&skip_status=true'

        # Set up our OAuth request headers, sign the request, etc.
        consumer = oauth.Consumer(self._periscope_consumer_key, self._periscope_consumer_secret)
        client = oauth.Client(consumer)

        # Make initial OAuth request to Twitter (gets us a temporary token used for the authorization process)
        resp, content = client.request(request_token_url, 'GET')
        if resp['status'] != '200':
            raise Exception('Invalid response. Could not initialize authentication process with Twitter.')

        # Parse the response from Twitter's API and use it to load the authorization page
        request_token = dict(parse_qsl(content.decode('ascii')))
        webbrowser.open('{0}?oauth_token={1}'.format(authorize_url, request_token['oauth_token']))

        # Get the Twitter PIN number from the user
        oauth_verifier = input('Please enter the PIN: ')

        # Prepare our second OAuth request now that we have authorization
        token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        token.set_verifier(oauth_verifier)
        client = oauth.Client(consumer, token)

        # Make request and parse the response from Twitter's API. The OAuth key we need to login to Periscope is in
        # access_token['oauth_token'] and the secret is in access_token['oauth_token_secret']
        resp, content = client.request(access_token_url, 'POST')
        if resp['status'] != '200':
            raise Exception('Invalid response. Could not complete authentication process with Twitter.')
        access_token = dict(parse_qsl(content.decode('ascii')))

        # Get the User ID and Username from Twitter
        token = oauth.Token(access_token['oauth_token'], access_token['oauth_token_secret'])
        client = oauth.Client(consumer, token)
        resp, content = client.request(verify_url, 'GET')
        if resp['status'] != '200':
            raise Exception('Invalid response. Could not complete verification process with Twitter.')
        user_info = json.loads(content.decode('ascii'))

        return access_token, user_info

    def _get_periscope_cookie(self, credentials):
        login_payload = {
            'session_secret': credentials['Access Token Secret'],
            'session_key': credentials['Access Token'],
            'user_id': credentials['User ID'],
            'user_name': credentials['Username'],
            'phone_number': '',
            'vendor_id': '',
            'bundle_id': 'com.bountylabs.periscope',
        }

        # Send payload to login to Periscope using the credentials obtained from Twitter
        r = requests.post('https://api.periscope.tv/api/v2/loginTwitter', json=login_payload, headers=self.header)
        if r.status_code != 200:
            print('Invalid response. Could not complete authentication with Periscope.')
            return None
        else:
            return r.json()['cookie']


if __name__ == '__main__':
    print(Login().cookie)
