#!/usr/bin/env python3
"""
Periscope API for the masses
"""

import os
import sys
import time
import threading
import youtube_dl

from multiprocessing import Pool
from dateutil.parser import parse as dt_parse

BROADCAST_URL_FORMAT = 'https://www.periscope.tv/w/'
DOWNLOAD_CMD = 'youtube-dl'
DEFAULT_NOTIFICATION_INTERVAL = 15
CORES_TO_USE = 2


def start_download(bc_id):
    """Sends Periscope URL to Youtube-DL for downloading and conversion"""
    url = BROADCAST_URL_FORMAT + bc_id
    ydl_opts = {}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return bc_id


def current_datetimestring():
    """Return a string with the date and time"""
    return " ".join([time.strftime('%x'), time.strftime('%X')])


def mute():
    """Write output from our youtube-dl processes to devnull"""
    sys.stdout = open(os.devnull, "w")


class AutoCap:
    """Class to check notifications stream and start capping new broadcasts"""

    def __init__(self, api, print_status=True, kb_stop=True):
        self.print_status = print_status
        self.kb_stop = kb_stop
        self.keep_running = True

        self.api = api
        self.config = self.api.session.config

        self.listener = Listener(api=self.api)
        self.downloadmgr = DownloadManager(api=self.api)

    def start(self):
        """Starts autocapper loop"""
        if self.kb_stop:
            threading.Thread(target=self.stop).start()
        while self.keep_running:

            new_broadcasts = self.listener.check_for_new()

            if new_broadcasts:
                self._send_to_downloader(new_broadcasts)

            if self.print_status:
                print(self._status)

            time.sleep(self.interval)

        killstr = "If you wish to terminate any unfinished downloads, please enter 'killall', " \
                  "otherwise, just press Return."

        if input(killstr).strip().lower() == 'killall':
            self.downloadmgr.pool.terminate()
        else:
            self.downloadmgr.pool.close()
            self.downloadmgr.pool.join()

    def stop(self):
        """Stops autocapper loop"""
        input("Press enter at any time to stop the Autocapper on its next loop\n")
        self.keep_running = False

    def _send_to_downloader(self, new_bcs):
        """Unpack results from listener and start download if new. Set latest dl time."""
        for bc_id, bc_name, bc_dtstring in new_bcs:
            self.downloadmgr.start_dl(bc_id, bc_name)

            if self.listener.last_new_bc:
                if dt_parse(bc_dtstring) > dt_parse(self.listener.last_new_bc):
                    self.listener.last_new_bc = bc_dtstring
            else:
                self.listener.last_new_bc = bc_dtstring

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


class Listener:
    """Class to check notifications stream for new broadcasts and return new broadcast ids"""

    def __init__(self, api):
        self.api = api

        self.config = self.api.session.config

    def check_for_new(self):
        """Check for new broadcasts"""
        current_notifications = self.api.notifications

        if len(current_notifications) == 0:
            return None

        new_broadcast_ids = self.process_notifications(current_notifications)
        if len(new_broadcast_ids) == 0:
            return None

        return new_broadcast_ids

    def process_notifications(self, notifications):
        """Process list of broadcasts obtained from notifications API endpoint."""
        new_broadcast_ids = list()

        for i in notifications:
            bc_dtstring = i['start']
            bc_datetime = dt_parse(bc_dtstring)

            if self.last_new_bc:
                if bc_datetime <= dt_parse(self.last_new_bc):
                    print('skipping broadcast at' + bc_dtstring)
                    continue

            bc_id = i['id']
            username = i['username']

            bc_date = bc_datetime.strftime('%m/%d/%Y')
            bc_time = bc_datetime.strftime('%H:%M:%S')

            bc_name = ' '.join([username, bc_date, bc_time, bc_id])

            new_broadcast_ids.append((bc_id, bc_name, bc_dtstring))

        return new_broadcast_ids

    @property
    def last_new_bc(self):
        """Get the ATOM timestamp of when the last new broadcast was found."""
        return self.config.get('last_check')

    @last_new_bc.setter
    def last_new_bc(self, when):
        """Set the ATOM timestamp of when the last new broadcast was found."""
        self.config['last_check'] = when
        self.config.write()


class DownloadManager:
    """Class to start and track status of download processes."""

    def __init__(self, api):

        self.api = api

        self.config = self.api.session.config

        self.active_downloads = dict()
        self.completed_downloads = list()
        self.failed_downloads = list()

        self.pool = Pool(CORES_TO_USE, initializer=mute, maxtasksperchild=1)

    def start_dl(self, bc_id, bc_name):
        """Adds a download task to the multiprocessing pool"""

        self.pool.apply_async(start_download, (bc_id,), callback=self._dl_complete,
                              error_callback=self._dl_failed)

        self.active_downloads[bc_id] = bc_name

    def _dl_complete(self, bc_id):
        bc_name = self.active_downloads[bc_id]
        print("{0} Completed: {1}".format(current_datetimestring(), bc_name))
        self.completed_downloads.append(bc_name)
        del self.active_downloads[bc_id]

    def _dl_failed(self, bc_id):
        bc_name = self.active_downloads[bc_id]
        print("{0} Failed: {1}".format(current_datetimestring(), bc_name))
        self.failed_downloads.append(bc_name)
        del self.active_downloads[bc_id]
