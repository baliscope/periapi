#!/usr/bin/env python3
"""
Periscope API for the masses
"""

import os
import time

from periapi.downloadmgr import DownloadManager, current_datetimestring
from periapi.listener import Listener

DEFAULT_NOTIFICATION_INTERVAL = 15


class AutoCap:
    """Class to check notifications stream and start capping new broadcasts"""

    def __init__(self, api, listener_opts, quiet_mode=False):
        self.quiet_mode = quiet_mode
        self.keep_running = True

        self.api = api
        self.config = self.api.session.config

        if not self.config.get('download_directory'):
            self.config['download_directory'] = os.path.join(os.path.expanduser('~'), 'downloads')
            if not os.path.exists(self.config.get("download_directory")):
                os.makedirs(self.config.get("download_directory"))
            self.config.write()

        self.listener = Listener(api=self.api, **listener_opts)
        self.downloadmgr = DownloadManager(api=self.api)

    def start(self):
        """Starts autocapper loop"""

        while self.keep_running:

            new_broadcasts = self.listener.check_for_new()

            if new_broadcasts:
                for broadcast in new_broadcasts:
                    self.downloadmgr.start_dl(broadcast)

            if not self.quiet_mode:
                print(self._status)

            time.sleep(self.interval)

            self.downloadmgr.redownload_failed()

        self.downloadmgr.pool.close()
        self.downloadmgr.pool.join()

    def stop(self):
        """Stops autocapper loop"""
        input("Press enter at any time to stop the Autocapper on its next loop\n")
        self.keep_running = False

    def _(self, new_bcs):
        """Unpack results from listener and start download. Set latest dl time."""


    @property
    def _status(self):
        """Retrieve status string for printing to console"""
        active = len(self.downloadmgr.active_downloads)
        complete = len(self.downloadmgr.completed_downloads)
        failed = len(self.downloadmgr.failed_downloads)

        cur_status = "{0} active downloads, {1} completed downloads, " \
                     "{2} failed downloads".format(active, complete, failed)

        return "[{0}] {1}".format(current_datetimestring(), cur_status)

    @property
    def interval(self):
        """Get the interval (in seconds) to check for notifications.
        Set default if no value exists."""
        if not self.config.get('notification_interval'):
            self.config['notification_interval'] = DEFAULT_NOTIFICATION_INTERVAL
            self.config.write()
        return self.config.get('notification_interval')

    @interval.setter
    def interval(self, value):
        """Set the interval (in seconds) to check for notifications"""
        self.config['notification_interval'] = value
        self.config.write()
