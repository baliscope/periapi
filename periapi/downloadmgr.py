#!/usr/bin/env python3
"""
Periscope API for the masses
"""

import os
import sys
import time
from multiprocessing.pool import Pool
from periapi.download import Download


CORES_TO_USE = -(-os.cpu_count() // 2)
MAX_DOWNLOAD_ATTEMPTS = 3


def current_datetimestring():
    """Return a string with the date and time"""
    return " ".join([time.strftime('%x'), time.strftime('%X')])


def initialize_download():
    """Write output from our download processes to devnull (or logs if you prefer!)"""
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")


class DownloadManager:
    """Class to start and track status of download processes."""

    def __init__(self, api):
        self.api = api

        self.config = self.api.session.config

        self.download_progress = dict()

        self.download_progress['active'] = dict()
        self.download_progress['completed'] = list()
        self.download_progress['failed'] = list()

        self.pool = Pool(CORES_TO_USE, initializer=initialize_download, maxtasksperchild=1)

    def start_dl(self, broadcast):
        """Adds a download task to the multiprocessing pool"""

        if broadcast.dl_failures > MAX_DOWNLOAD_ATTEMPTS or \
                not(broadcast.islive or broadcast.isreplay):
            print("[{0}] Failed: {1}".format(current_datetimestring(), broadcast.title))
            self.failed_downloads.append((current_datetimestring(), broadcast))
            return None

        elif broadcast.dl_failures > 0:
            print("[{0}] Redownload Attempt ({1} of {2}): {3}".format(
                current_datetimestring(),
                broadcast.dl_failures,
                MAX_DOWNLOAD_ATTEMPTS,
                broadcast.title))

        else:
            print("[{0}] Adding Download: {1}".format(current_datetimestring(), broadcast.title))

        self.pool.apply_async(Download(broadcast).start, (), callback=self._callback_dispatcher)

        self.active_downloads[broadcast.id] = broadcast

    def check_for_replay(self, broadcast):
        """Starts download of broadcast replay if not already gotten; or, resumes interrupted
         live download
         """
        if broadcast.islive:
            broadcast.update_info()
            if broadcast.num_restarts(span=15) > 4 or broadcast.num_restarts(span=60) > 10:
                print("[{0}] Too many live resume attempts: {1}".format(current_datetimestring(),
                                                                        broadcast.title))
                broadcast.dl_failures += 1
            elif broadcast.available and not broadcast.islive:
                print("[{0}] Downloading replay of: {1}".format(current_datetimestring(),
                                                                broadcast.title))
                self.start_dl(broadcast)
            elif broadcast.islive:
                print("[{0}] Resuming interrupted capture of: {1}".format(current_datetimestring(),
                                                                          broadcast.title))
                self.start_dl(broadcast)

    def _callback_dispatcher(self, results):
        """Unpacks callback argument and passes to appropriate cleanup method"""
        download_ok, broadcast = results
        if download_ok:
            self._dl_complete(broadcast)
        else:
            self._dl_failed(broadcast)

    def _dl_complete(self, broadcast):
        """Callback method when download completes"""
        print("[{0}] Completed: {1}".format(current_datetimestring(), broadcast.title))
        self.completed_downloads.append((current_datetimestring(), broadcast))
        del self.active_downloads[broadcast.id]
        self.check_for_replay(broadcast)

    def _dl_failed(self, broadcast):
        """Callback method when download fails"""
        del self.active_downloads[broadcast.id]
        broadcast.dl_failures += 1
        broadcast.update_info()
        self.start_dl(broadcast)

    @property
    def status(self):
        """Retrieve status string for printing to console"""
        active = len(self.active_downloads)
        complete = len(self.completed_downloads)
        failed = len(self.failed_downloads)

        cur_status = "{0} active downloads, {1} completed downloads, " \
                     "{2} failed downloads".format(active, complete, failed)

        return "[{0}] {1}".format(current_datetimestring(), cur_status)

    @property
    def active_downloads(self):
        """Return dictionary of active downloads"""
        return self.download_progress['active']

    @property
    def completed_downloads(self):
        """Return list of completed downloads"""
        return self.download_progress['completed']

    @property
    def failed_downloads(self):
        """Return list of failed downloads"""
        return self.download_progress['failed']
