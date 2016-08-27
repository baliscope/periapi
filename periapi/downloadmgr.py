#!/usr/bin/env python3
"""
Periscope API for the masses
"""

import os
import sys
import time
from multiprocessing.pool import Pool
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

    def start_dl(self, broadcast):
        """Adds a download task to the multiprocessing pool"""
        if not broadcast.stutter_resume:
            print("[{0}] Adding Download: {1}".format(current_datetimestring(), broadcast.title))

        self.pool.apply_async(Download(broadcast).start, (), callback=self._callback_dispatcher)

        self.active_downloads[broadcast.id] = broadcast

    def review_broadcast_status(self, broadcast):
        """Starts download of broadcast replay if not already gotten; or, resumes interrupted
         live download. Print status to console.
         """
        old_title = broadcast.title
        broadcast.update_info()

        if broadcast.isreplay and broadcast.replay_downloaded:
            return None

        failure_message = None
        if broadcast.dl_failures > MAX_DOWNLOAD_ATTEMPTS:
            failure_message = "\n\tExceeded maximum download attempts "
            if broadcast.failure_reason is not None:
                failure_message += "with the following error:\n\t" + str(broadcast.failure_reason)

        elif not (broadcast.islive or broadcast.isreplay or broadcast.dl_failures == 0):
            failure_message = "\n\tBroadcast no longer available."

        elif broadcast.islive:
            if broadcast.num_restarts(span=15) > 4 or broadcast.num_restarts(span=60) > 10:
                print("[{0}] Too many live resume attempts: "
                      "{1}".format(current_datetimestring(), broadcast.title))

                if broadcast.available:
                    print("[{0}] Pausing and waiting for replay: "
                          "{1}".format(current_datetimestring(), broadcast.title))
                    broadcast.wait_for_replay = True

                else:
                    failure_message = "\n\tToo many broadcast restarts in a short timespan."

            elif not broadcast.stutter_resume:
                print("[{0}] Live capture was interrupted. "
                      "Broadcast still live, attempting to resume: {1}".format(
                          current_datetimestring(), broadcast.title))

        elif broadcast.dl_failures > 0:
            print("[{0}] Redownload Attempt ({1} of {2}): {3}".format(
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
            self.failed_downloads.append((current_datetimestring(), broadcast))
        else:
            self.start_dl(broadcast)

    def _callback_dispatcher(self, results):
        """Unpacks callback argument and passes to appropriate cleanup method"""
        download_ok, broadcast = results
        del self.active_downloads[broadcast.id]

        if download_ok:
            print("[{0}] Completed: {1}".format(current_datetimestring(), broadcast.title))
            self.completed_downloads.append((current_datetimestring(), broadcast))
        else:
            if broadcast.islive:
                broadcast.stutter_resume = True
            else:
                broadcast.dl_failures += 1

        self.review_broadcast_status(broadcast)

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
