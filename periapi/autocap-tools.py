#!/usr/bin/env python3
"""
Periscope API for the masses
"""

import os

from subprocess import Popen
from dateutil import parser

from .login import PeriConfig

BROADCAST_URL_FORMAT = 'https://www.periscope.tv/w/'


class Listener:
    """Class to check notifications stream for new broadcasts and return new broadcast ids"""

    def __init__(self, api):
        self.api = api
        self.config = PeriConfig()

    def check_for_new(self):
        """Check for new broadcasts"""
        new_broadcast_ids = list()
        current_notifications = self.api.notifications

        if len(current_notifications) == 0:
            return None

        for i in current_notifications:
            if parser.parse(i['start']) >= parser.parse(self.last_check):
                bc_name = '{} {}'.format(i['user_display_name'], i['status'])
                new_broadcast_ids.append((i['id'], bc_name))

        self.last_check(current_notifications[0]['start'])

        return new_broadcast_ids

    @property
    def last_check(self):
        """Get the ISO 8601 timestamp of when the notification stream was last checked.
        If no value, sets to earliest broadcast time in notification stream"""
        if not self.config.get('last_check'):
            self.config['last_check'] = self.api.notifications[-1]['start']
            self.config.write()
        return self.config.get('last_check')

    @last_check.setter
    def last_check(self, when):
        """Set the ISO 8601 timestamp of when the notification stream was last checked."""
        self.config['last_check'] = when
        self.config.write()


class DownloadManager:
    """Class to start and track status of download processes."""

    def __init__(self):

        self.config = PeriConfig()

        self.active_downloads = dict()
        self.completed_downloads = list()
        self.failed_downloads = list()

    def start_dl(self, bc_id, bc_name):
        """Attempts to start a download using youtube-dl"""
        url = BROADCAST_URL_FORMAT + bc_id

        self.dl_status_update()

        if self.max_simultaneous_dls <= len(self.active_downloads):
            return None

        self.active_downloads[bc_id] = (bc_name, Popen(['youtube-dl', url], cwd=self.dl_directory))
        return True

    def dl_status_update(self):
        """Polls active downloads to check if they have completed, stores results"""
        if len(self.active_downloads) == 0:
            return None

        for bc_id in self.active_downloads:
            dl_object = self.active_downloads[bc_id]
            dl_status = dl_object[1].poll()
            dl_name = dl_object[0]

            if not dl_status:
                continue

            elif dl_status == 0:
                self.completed_downloads.append((bc_id, dl_name))
                del self.active_downloads[bc_id]

            elif dl_status != 0:
                self.failed_downloads.append((bc_id, dl_name))
                del self.active_downloads[bc_id]

    @property
    def dl_directory(self):
        """Gets current broadcast download directory from config.
        If no dl directory, sets it to a default."""
        if not self.config.get('download_directory'):
            self.config['download_directory'] = os.getcwd()
            self.config.write()
        return self.config.get('download_directory')

    @dl_directory.setter
    def dl_directory(self, directory):
        """Sets download directory for broadcasts"""
        self.config['download_directory'] = directory
        self.config.write()

    @property
    def max_simultaneous_dls(self):
        """Gets current maximum simultaneous downloads from config.
        If no value, sets it to a default."""
        if not self.config.get('max_simultaneous_dls'):
            self.config['max_simultaneous_dls'] = 10
            self.config.write()
        return self.config.get('max_simultaneous_dls')

    @max_simultaneous_dls.setter
    def max_simultaneous_dls(self, count):
        """Sets value for maximum number of simultaneous broadcast downloads"""
        self.config['max_simultaneous_dls'] = int(count)
        self.config.write()
