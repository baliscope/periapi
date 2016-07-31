#!/usr/bin/env python3
"""
Periscope API for the masses
"""

import os
from dateutil.parser import parse as dt_parse


class BroadcastDownloadInfo:
    """Contains information about the broadcast's download but not about the broadcast itself"""

    def __init__(self, api):
        self.dl_info = dict()
        self.dl_info['dl_times'] = list()
        self.dl_info['dl_failures'] = 0
        self.dl_info['wait_for_replay'] = False
        self.dl_info['replay_downloaded'] = False
        self.dl_info['download_directory'] = api.session.config.get('download_directory')

    @property
    def dl_times(self):
        """List of timestamps broadcast download was started or restarted"""
        return self.dl_info['dl_times']

    @property
    def dl_failures(self):
        """Counter for how many times download has failed"""
        return self.dl_info['dl_failures']

    @dl_failures.setter
    def dl_failures(self, value):
        """Sets download failure count"""
        self.dl_info['dl_failures'] = value

    @property
    def download_directory(self):
        """Returns broadcast download directory"""
        return self.dl_info['download_directory']

    @property
    def wait_for_replay(self):
        """Check if broadcast live should be skipped and replay should be waited for"""
        return self.dl_info['wait_for_replay']

    @wait_for_replay.setter
    def wait_for_replay(self, boolean):
        """Return whether or not live download should be skipped and replay should be waited for"""
        self.dl_info['wait_for_replay'] = bool(boolean)

    @property
    def replay_downloaded(self):
        """Boolean indicating whether or not a replay of the broadcast has been downloaded"""
        return self.dl_info['replay_downloaded']

    @replay_downloaded.setter
    def replay_downloaded(self, boolean):
        """Set indicator for whether or not a replay of the broadcast has been downloaded"""
        self.dl_info['replay_downloaded'] = bool(boolean)


class Broadcast(BroadcastDownloadInfo):
    """Broadcast object"""

    def __init__(self, api, broadcast):
        super().__init__(api)
        self.api = api
        self.info = broadcast
        self.cookie = self.api.session.config.get('cookie')[:]

    def update_info(self):
        """Updates broadcast object with latest info from periscope"""
        updates = self.api.get_broadcast_info(self.id)
        if not updates:
            self.info['available_for_replay'] = False
            self.info['state'] = "DELETED"
        else:
            self.info = updates

    def num_restarts(self, span=10):
        """Gets number of times download has been started within past span seconds"""
        if len(self.dl_times) > 0:
            return len([i for i in self.dl_times if i > self.dl_times[-1]-span])
        return 0

    @property
    def id(self):
        """Returns broadcast id"""
        return self.info['id']

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
        suffix = []
        if not self.islive:
            suffix.append('REPLAY')
        if self.private:
            suffix.append('PRIVATE')
        if len(suffix) == 0:
            return ' '.join([self.username, self.startdate, self.starttime, self.id])
        return ' '.join([self.username, self.startdate, self.starttime, self.id, ' '.join(suffix)])

    @property
    def filepathname(self):
        """Get filename for broadcast, including path, without extension"""
        return os.path.join(self.download_directory, self.filetitle)

    @property
    def filetitle(self):
        """Version of title safe for use as a filename"""
        if self.islive:
            return self.title.replace('/', '-').replace(':', '-') + '.live'
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
        if self.available and not self.islive:
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

    @property
    def available(self):
        """Check if broadcast is available for replay"""
        return self.info['available_for_replay']

    @property
    def private(self):
        """Boolean indicating if broadcast is private or not"""
        return self.info['is_locked']
