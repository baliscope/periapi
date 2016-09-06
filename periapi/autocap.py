#!/usr/bin/env python3
"""
Periscope API for the masses
"""

import os
import time

from periapi.downloadmgr import DownloadManager
from periapi.listener import Listener
from periapi.broadcast import Broadcast

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

        loops = 0
        while self.keep_running:

            new_broadcasts = self.listener.check_for_new()

            if new_broadcasts:
                for broadcast in new_broadcasts:
                    self.downloadmgr.start_dl(broadcast)

            if not self.quiet_mode:
                loops = self.print_current_status(loops)

            time.sleep(self.interval)

        self.downloadmgr.pool.close()
        self.downloadmgr.pool.join()

    def stop(self):
        """Stops autocapper loop"""
        self.keep_running = False

    def cap_one(self, broadcast_id):
        """Cap a single broadcast"""
        broadcast_info = self.api.get_access(broadcast_id).get('broadcast')
        broadcast = Broadcast(self.api, broadcast_info)
        self.downloadmgr.start_dl(broadcast)
        _ = len(self.downloadmgr.active_downloads)
        while _ > 0:
            if not self.quiet_mode:
                print(self.downloadmgr.status)
            time.sleep(self.interval)
            self.downloadmgr.sema.acquire()
            _ = len(self.downloadmgr.active_downloads)
            self.downloadmgr.sema.release()
        self.downloadmgr.pool.close()
        self.downloadmgr.pool.join()

    def cap_user(self, username):
        """Cap all broadcasts by a user"""
        user_id = self.api.find_user_id(username)
        broadcasts = self.api.get_user_broadcast_history(user_id)
        if len(broadcasts) < 1:
            print("No broadcast history found for {}".format(username))
            return None
        for i in broadcasts:
            broadcast = Broadcast(self.api, i)
            self.downloadmgr.start_dl(broadcast)
        _ = len(self.downloadmgr.active_downloads)
        while _ > 0:
            if not self.quiet_mode:
                print(self.downloadmgr.status)
            time.sleep(self.interval)
            self.downloadmgr.sema.acquire()
            _ = len(self.downloadmgr.active_downloads)
            self.downloadmgr.sema.release()
        self.downloadmgr.pool.close()
        self.downloadmgr.pool.join()

    def print_current_status(self, loops):
        """Prints current status and lists active downloads every so often"""
        print(self.downloadmgr.status)
        if (loops * self.interval) > 150:
            loops = 0
            if len(self.downloadmgr.currently_downloading) > 0:
                print("\tCurrently downloading:")
                for bc_title in self.downloadmgr.currently_downloading:
                    print("\t{}".format(bc_title))
        else:
            loops += 1
        return loops

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
