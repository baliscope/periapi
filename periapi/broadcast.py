#!/usr/bin/env python3
"""
Periscope API for the masses
"""

from dateutil.parser import parse as dt_parse


class Broadcast:
    """Broadcast object"""

    def __init__(self, api, broadcast):
        self.api = api
        self.info = broadcast
        self.info['download_directory'] = self.api.session.config.get('download_directory')

    def update_info(self):
        """Updates broadcast object with latest info from periscope"""
        updates = self.api.get_broadcast_info(self.id)
        dl_directory = self.download_directory
        if not updates:
            self.available = False
            self.state = "DELETED"
        else:
            self.info = updates
            self.info['download_directory'] = dl_directory

    @property
    def id(self):
        """Returns broadcast id"""
        return self.info['id']

    @property
    def download_directory(self):
        """Returns broadcast download directory"""
        return self.info.get('download_directory')

    @property
    def username(self):
        """Returns broadcaster username"""
        return self.info['username']

    @property
    def start(self):
        """Returns ATOM string indicating when broadcast started"""
        return self.info['start']

    @property
    def start_dt(self):
        """Datetime object version of broadcast start time"""
        return dt_parse(self.info['start'])

    @property
    def startdate(self):
        """Human-readable date string of when broadcast started"""
        return self.start_dt.strftime('%m/%d/%Y')

    @property
    def starttime(self):
        """Human-readable time string of when broadcast started"""
        return self.start_dt.strftime('%H:%M:%S')

    @property
    def title(self):
        """Title of broadcast (in the context of the downloader)"""
        if not self.islive and self.available:
            return ' '.join([self.username, self.startdate, self.starttime, self.id, 'REPLAY'])
        return ' '.join([self.username, self.startdate, self.starttime, self.id])

    @property
    def filename(self):
        """Get title string adapted for use as filename"""
        return self.title.replace('/', '-').replace(':', '-')

    @property
    def islive(self):
        """Check if broadcast is running or not"""
        if self.info['state'] == 'RUNNING':
            return True
        return False

    @property
    def isreplay(self):
        """Check if broadcast is replay or not"""
        if not self.islive and self.available:
            return True
        return False

    @property
    def isnewer(self):
        """Check if broadcast is newer than last broadcast time"""
        last_broadcast = self.api.session.config.get('last_check')
        if not last_broadcast:
            return None
        elif self.start_dt > dt_parse(last_broadcast):
            return True
        else:
            return False

    @property
    def state(self):
        """Get broadcast state string"""
        return self.info['state']

    @state.setter
    def state(self, new_state):
        """Set broadcast state string (useful if broadcast is deleted since peri deletes entire
        broadcast object)"""
        self.info['state'] = new_state

    @property
    def available(self):
        """Check if broadcast is available for replay"""
        return self.info['available_for_replay']

    @available.setter
    def available(self, boolean):
        """Set broadcast availability (if broadcast is deleted - set to False)"""
        self.info['available_for_replay'] = boolean
