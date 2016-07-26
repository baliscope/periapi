#!/usr/bin/env python3
"""
Periscope API for the masses
"""

from periapi.broadcast import Broadcast


class Listener:
    """Class to check notifications stream for new broadcasts and return new broadcast ids"""

    def __init__(self, api, check_backlog=False, cap_invited=False):

        self.api = api

        self.follows = set([i['username'] for i in self.api.following])
        self.config = self.api.session.config

        self.check_backlog = check_backlog
        self.cap_invited = cap_invited

    def check_for_new(self):
        """Check for new broadcasts"""
        current_notifications = self.api.notifications

        if len(current_notifications) == 0:
            return None

        new_broadcasts = self.process_notifications(current_notifications)

        if len(new_broadcasts) == 0:
            return None

        return new_broadcasts

    def process_notifications(self, notifications):
        """Process list of broadcasts obtained from notifications API endpoint."""
        new_broadcasts = list()
        new = self.new_follows()

        for i in notifications:

            broadcast = Broadcast(self.api, i)

            if self.check_if_wanted(broadcast, new):
                new_broadcasts.append(broadcast)

        if self.check_backlog:
            self.check_backlog = False

        self.update_latest_broadcast_time(new_broadcasts)

        return new_broadcasts

    def check_if_wanted(self, broadcast, new_follow):
        """Check if broadcast in notifications string is desired for download"""
        if self.check_backlog or broadcast.isnewer or (broadcast.islive and not self.last_new_bc):
            if self.cap_invited or broadcast.username in self.follows:
                return True

        elif new_follow and broadcast.username in new_follow:
            return True

        return None

    def new_follows(self):
        """Get set of new follows since last check"""
        cur_follows = set([i['username'] for i in self.api.following])
        new_follows = cur_follows - self.follows
        self.follows = cur_follows
        if len(new_follows) > 0:
            return new_follows
        return None

    def update_latest_broadcast_time(self, broadcasts):
        """Get most recent broadcast time from iterable of broadcast objects"""
        for broadcast in broadcasts:
            if broadcast.isnewer:
                self.last_new_bc = broadcast.start

    @property
    def last_new_bc(self):
        """Get the ATOM timestamp of when the last new broadcast was found."""
        return self.config.get('last_check')

    @last_new_bc.setter
    def last_new_bc(self, when):
        """Set the ATOM timestamp of when the last new broadcast was found."""
        self.config['last_check'] = when
        self.config.write()
