#!/usr/bin/env python3
"""
Periscope API for the masses
"""

from functools import wraps

from .login import LoginSession
from .logging import logging


def bool_response(fun):
    """Decorates a function to be a boolean response"""

    @wraps(fun)
    def wrapper(*args, **kw):
        """Actual wrapper"""
        resp = fun(*args, **kw)
        success = resp.get("success")
        if success == "true" or success:
            return True
        if success == "false" or success:
            return False
        raise ValueError("Invalid boolean success response")

    return wrapper


class PeriAPI:
    """Implements some of the periscope.tv API"""

    def __init__(self):
        self.session = LoginSession()
        self._pubid = self.session.config.get("pubid")

    def _post(self, url, payload=None):
        """Post something to the API"""
        res = self.session.post_peri(url, json=payload or {})
        logging.debug("%s: params:%r result=%r", url, payload, res)
        return res

    def _get_unauth(self, url, payload=None):
        """Get request to API (Periscope uses query strings here, not json)"""
        res = self.session.get(url, params=payload)
        logging.debug("%s: params:%r result=%r", url, payload, res)
        try:
            return res.json()
        except ValueError:
            return dict()

    @property
    def pubid(self):
        if not self._pubid:
            self._pubid = self.find_user_id(self.session.name)
            self.session.config["pubid"] = self._pubid
            self.session.config.write()
        return self._pubid

    @bool_response
    def follow(self, user_id):
        """Follow a user"""
        return self._post(
            'https://api.periscope.tv/api/v2/follow',
            {"user_id": user_id}
            )

    @bool_response
    def unfollow(self, user_id):
        """Unfollow a user"""
        return self._post(
            'https://api.periscope.tv/api/v2/unfollow',
            {"user_id": user_id}
            )

    def get_user_broadcast_history(self, user_id):
        """Users have broadcasts, this lists them"""
        return self._post(
            'https://api.periscope.tv/api/v2/userBroadcasts',
            {"user_id": user_id}
            )

    @property
    def notifications(self):
        """Current notifications"""
        return self._post(
            'https://api.periscope.tv/api/v2/followingBroadcastFeed'
            )

    @property
    def following(self):
        """Current people you're following"""
        return self._post(
            'https://api.periscope.tv/api/v2/following',
            {"user_id": self.pubid}
            )

    def lookup_private(self, broadcast_id):
        """Gets broadcast info (like rtmps url) for private broadcasts"""
        return self._post(
            'https://api.periscope.tv/api/v2/accessChannel',
            {'broadcast_id': broadcast_id}
            )

    def get_broadcast_info(self, broadcast_id):
        """Returns broadcast dictionary"""
        return self._get_unauth(
            'https://api.periscope.tv/api/v2/getBroadcastPublic',
            {'broadcast_id': broadcast_id}
            ).get('broadcast')

    def find_user_id(self, username):
        """Most API calls require the user id, not name, so find it"""
        results = self._post(
            "https://api.periscope.tv/api/v2/userSearch",
            {"search": username}
            )
        username = username.casefold()
        for res in results:
            if res["username"].casefold() == username:
                return res["id"]
        raise ValueError("User not found")
