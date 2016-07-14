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

import requests


class APICall:
    def __init__(self, cookie, header):
        self.cookie = cookie
        self.header = header

    def follow(self, user_id):
        payload = {
            'cookie': self.cookie,
            'user_id': user_id
        }
        r = requests.post('https://api.periscope.tv/api/v2/follow', json=payload, headers=self.header)
        if r.status_code != 200:
            print('Periscope API Call failed.')
            print(r)
            print(r.json())
        if r.json()['success'] == 'true':
            return True
        elif r.json()['success'] == 'false':
            return False

    def unfollow(self, user_id):
        payload = {
            'cookie': self.cookie,
            'user_id': user_id
        }
        r = requests.post('https://api.periscope.tv/api/v2/unfollow', json=payload, headers=self.header)
        if r.status_code != 200:
            print('Periscope API Call failed.')
            print(r)
            print(r.json())
        if r.json()['success'] == 'true':
            return True
        elif r.json()['success'] == 'false':
            return False

    def user_broadcast_history(self, user_id):
        payload = {
            'cookie': self.cookie,
            'user_id': user_id,
        }
        r = requests.post('https://api.periscope.tv/api/v2/userBroadcasts', json=payload, headers=self.header)
        if r.status_code != 200:
            print('Periscope API Call failed.')
            print(r)
            print(r.json())
        return r.json()

    def get_notifications(self):
        payload = {
            'cookie': self.cookie,
        }
        r = requests.post('https://api.periscope.tv/api/v2/followingBroadcastFeed', json=payload, headers=self.header)
        if r.status_code != 200:
            print('Periscope API Call failed.')
        return r.json()

    def get_user_id(self, username):
        payload = {
            'cookie': self.cookie,
            'search': username
        }
        r = requests.post('https://api.periscope.tv/api/v2/userSearch', json=payload, headers=self.header)
        if r.status_code != 200:
            print('Periscope API Call failed.')
        for i in r.json():
            if i['username'].lower() == username.lower():
                return i['id']
        return None
