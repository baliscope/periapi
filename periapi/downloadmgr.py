#!/usr/bin/env python3
"""
Periscope API for the masses
"""

import os
import sys
import time
from multiprocessing.pool import Pool
from multiprocessing import Semaphore
from periapi.download import Download


CORES_TO_USE = os.cpu_count()
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
        self.sema = Semaphore()

    def start_dl(self, broadcast):
        """Adds a download task to the multiprocessing pool"""
        print("[{0}] Adding Download: {1}".format(current_datetimestring(), broadcast.title))

        self.pool.apply_async(Download(broadcast).start, (), callback=self._callback_dispatcher)

        self.sema.acquire()
        self.active_downloads[broadcast.id] = broadcast
        self.sema.release()

    def review_broadcast_status(self, broadcast, download_ok):
        """Starts download of broadcast replay if not already gotten; or, resumes interrupted
         live download. Print status to console.
         """
        old_title = broadcast.title
        broadcast.lock_name = False
        broadcast.update_info()

        if broadcast.isreplay and broadcast.replay_downloaded:
            return None

        elif download_ok and broadcast.islive:
            broadcast.dl_failures += 1

        failure_message = None
        if broadcast.dl_failures > MAX_DOWNLOAD_ATTEMPTS:
            if broadcast.islive and broadcast.available:
                broadcast.wait_for_replay = True
                broadcast.dl_failures = 0
                print("[{0}] Too many live resume attempts, waiting for replay: {1} {2}".format(
                    current_datetimestring(), old_title, failure_message))
            else:
                failure_message = "\n\tExceeded maximum download attempts "
                if broadcast.failure_reason is not None:
                    failure_message += "with the following error:\n\t" + \
                                       str(broadcast.failure_reason)

        elif not (broadcast.islive or broadcast.isreplay or broadcast.dl_failures == 0):
            failure_message = "\n\tBroadcast no longer available."

        elif broadcast.dl_failures > 0:
            print("[{0}] Resuming download (Attempt {1} of {2}): {3}".format(
                current_datetimestring(), broadcast.dl_failures, MAX_DOWNLOAD_ATTEMPTS,
                broadcast.title))

        elif broadcast.isreplay and not broadcast.replay_downloaded:
            print("[{0}] Downloading replay of: "
                  "{1}".format(current_datetimestring(), broadcast.title))

        else:
            return None

        if failure_message is not None:
            print("[{0}] Failed: {1} {2}".format(current_datetimestring(),
                                                 old_title, failure_message))
            self.sema.acquire()
            self.failed_downloads.append((current_datetimestring(), broadcast))
            self.sema.release()
        else:
            self.start_dl(broadcast)

    def _callback_dispatcher(self, results):
        """Unpacks callback argument and passes to appropriate cleanup method"""
        download_ok, broadcast = results
        self.sema.acquire()
        del self.active_downloads[broadcast.id]
        self.sema.release()

        if download_ok:
            print("[{0}] Completed: {1}".format(current_datetimestring(), broadcast.title))
            self.sema.acquire()
            self.completed_downloads.append((current_datetimestring(), broadcast))
            self.sema.release()
        else:
            broadcast.dl_failures += 1

        self.review_broadcast_status(broadcast, download_ok)

    @property
    def status(self):
        """Retrieve status string for printing to console"""
        self.sema.acquire()
        active = len(self.active_downloads)
        complete = len(self.completed_downloads)
        failed = len(self.failed_downloads)
        self.sema.release()

        cur_status = "{0} active downloads, {1} completed downloads, " \
                     "{2} failed downloads".format(active, complete, failed)

        return "[{0}] {1}".format(current_datetimestring(), cur_status)

    @property
    def currently_downloading(self):
        """Returns list of the broadcast.title property of all active broadcast downloads"""
        self.sema.acquire()
        _ = [broadcast.title for _, broadcast in self.active_downloads.items()]
        self.sema.release()
        return _

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
