#!/usr/bin/env python3
"""
Periscope API for the masses
"""

import os
import sys
import time
from multiprocessing.pool import Pool

import pyriscope.processor

BROADCAST_URL_FORMAT = 'https://www.periscope.tv/w/'
CORES_TO_USE = -(-os.cpu_count() // 2)
EXTENSIONS = ['.mp4', '.ts']
MAX_DOWNLOAD_ATTEMPTS = 3

pyriscope.processor.FFMPEG_LIVE = pyriscope.processor.FFMPEG_LIVE.replace('error', 'quiet')
pyriscope.processor.FFMPEG_ROT = pyriscope.processor.FFMPEG_ROT.replace('error', 'quiet')
pyriscope.processor.FFMPEG_NOROT = pyriscope.processor.FFMPEG_NOROT.replace('error', 'quiet')


def current_datetimestring():
    """Return a string with the date and time"""
    return " ".join([time.strftime('%x'), time.strftime('%X')])


def download_successful(broadcast):
    """Checks if download was successful"""
    checks = 3
    waittime = 5

    _ = 0
    while _ < checks:
        for bcdescriptor in ['', '.live']:
            for extension in EXTENSIONS:
                filename = broadcast.filename + bcdescriptor + extension
                if os.path.exists(os.path.join(broadcast.download_directory, filename)):
                    return True
        time.sleep(waittime)
        _ += 1

    return False


def initialize_download():
    """Write output from our pyriscope processes to devnull"""
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")


def rename_live(broadcast):
    """Gives live broadcast files a number indicating what order they were gotten in. Useful when
    capping a broadcast that cuts in and out.
    """
    fname = broadcast.filename
    for extension in EXTENSIONS:
        filename_start = os.path.join(broadcast.download_directory, fname + '.live')
        if os.path.exists(filename_start + extension):
            _ = 1
            while os.path.exists(filename_start + str(_) + extension):
                _ += 1
            os.rename(filename_start + extension, filename_start + str(_) + extension)
            return None


def replay_downloaded(broadcast):
    """Boolean indicating if given replay has been downloaded already"""
    for extension in EXTENSIONS:

        if os.path.exists(os.path.join(broadcast.download_directory,
                                       broadcast.filename + extension)):
            return True

    return False


def start_download(broadcast):
    """Starts download using pyriscope"""
    try:
        broadcast.dl_times.append(time.time())

        os.chdir(broadcast.download_directory)

        if broadcast.isreplay and replay_downloaded(broadcast):
            return True, broadcast

        url = BROADCAST_URL_FORMAT + broadcast.id

        pyriscope.processor.process([url, '-C', '-n', broadcast.filename])

        if download_successful(broadcast):
            return True, broadcast
        else:
            return False, broadcast

    except SystemExit as _:
        if not _.code or _.code == 0:
            return True, broadcast
        else:
            return False, broadcast

    except BaseException:
        return False, broadcast

    finally:
        if broadcast.islive:
            rename_live(broadcast)


class DownloadManager:
    """Class to start and track status of download processes."""

    def __init__(self, api):
        self.api = api

        self.config = self.api.session.config
        self.retry = dict()

        self.download_progress = dict()

        self.download_progress['active'] = dict()
        self.download_progress['completed'] = list()
        self.download_progress['failed'] = list()

        self.pool = Pool(CORES_TO_USE, initializer=initialize_download, maxtasksperchild=1)

    def start_dl(self, broadcast):
        """Adds a download task to the multiprocessing pool"""

        self.pool.apply_async(start_download, (broadcast,), callback=self._callback_dispatcher)

        self.active_downloads[broadcast.id] = broadcast

        print("[{0}] Adding Download: {1}".format(current_datetimestring(), broadcast.title))

    def check_for_replay(self, broadcast):
        """Starts download of broadcast replay if not already gotten; or, resumes interrupted
         live download
         """
        if broadcast.islive:
            broadcast.update_info()
            if broadcast.num_restarts(span=15) > 4 or broadcast.num_restarts(span=60) > 10:
                print("[{0}] Too many live resume attempts: {1}".format(current_datetimestring(),
                                                                        broadcast.title))
            elif broadcast.available and not broadcast.islive:
                print("[{0}] Downloading replay of: {1}".format(current_datetimestring(),
                                                                broadcast.title))
                self.start_dl(broadcast)
            elif broadcast.islive:
                print("[{0}] Continuing live download of: {1}".format(current_datetimestring(),
                                                                      broadcast.title))
                self.start_dl(broadcast)

    def redownload_failed(self):
        """Check list of retries and redownload or send to failed as appropriate"""
        if len(self.retry) == 0:
            return None

        purge_list = list()
        for bc_id in self.retry:

            broadcast = self.retry[bc_id]
            broadcast.dl_failures += 1
            broadcast.update_info()

            if broadcast.dl_failures <= MAX_DOWNLOAD_ATTEMPTS and \
                    (broadcast.islive or broadcast.available):

                print("[{0}] Redownload Attempt ({1} of {2}): {3}".format(
                    current_datetimestring(),
                    broadcast.dl_failures,
                    MAX_DOWNLOAD_ATTEMPTS,
                    broadcast.title
                )
                     )

                self.start_dl(broadcast)

            else:

                print("[{0}] Failed: {1}".format(current_datetimestring(), broadcast.title))
                self.failed_downloads.append((current_datetimestring(), broadcast))
                purge_list.append(bc_id)

        for bc_id in purge_list:
            del self.retry[bc_id]

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
        self.retry[broadcast.id] = broadcast
        del self.active_downloads[broadcast.id]

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
