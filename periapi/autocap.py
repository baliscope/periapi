#!/usr/bin/env python3
"""
Periscope API for the masses
"""

import os
import time

from periapi.downloadmgr import DownloadManager
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
            self.config.write()
        if not os.path.exists(self.config.get("download_directory")):
            os.makedirs(self.config.get("download_directory"))

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
                print(self.downloadmgr.status)

            time.sleep(self.interval)

            self.downloadmgr.redownload_failed()

        self.downloadmgr.pool.close()
        self.downloadmgr.pool.join()

    def stop(self):
        """Stops autocapper loop"""
        input("Press enter at any time to stop the Autocapper on its next loop\n")
        self.keep_running = False

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
