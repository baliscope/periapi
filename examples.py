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

from periapi import PeriAPI

# Initialize API
ac = PeriAPI()

# Get a user's ID number (we need this to refer to their account in other API calls)
uid = ac.find_user_id('Tito1990')

# Start following someone
ac.follow(uid)

# Show entire broadcast history of a user
bc_history = ac.get_user_broadcast_history(uid)
print(bc_history)

# show the URL of their most recent broadcast
if len(bc_history) > 0:
    bc_id = bc_history[0]['id']
    print('https://www.periscope.tv/w/' + bc_id)

# Get one frame of the notifications broadcast feed (i.e. get notifications from users you're following)
notifications_history = ac.notifications
print(notifications_history)

# Show the URL to the most recent broadcast in your notifications stream
if len(notifications_history) > 0:
    bc_id = notifications_history[0]['id']
    print('https://www.periscope.tv/w/' + bc_id)

# Unfollow someone
ac.unfollow(uid)
