#!/usr/bin/env python3
"""
Periscope API for the masses
"""

import os
import sys
import time
from multiprocessing import Pool

import pyriscope.processor

from dateutil.parser import parse as dt_parse

BROADCAST_URL_FORMAT = 'https://www.periscope.tv/w/'
DEFAULT_NOTIFICATION_INTERVAL = 15
DEFAULT_DOWNLOAD_DIRECTORY = os.path.join(os.getcwd(), 'downloads')
CORES_TO_USE = -(-os.cpu_count() // 2)
MAX_REDOWNLOAD_ATTEMPTS = 3
EXTENSIONS = ['.mp4', '.ts']

pyriscope.processor.FFMPEG_LIVE = pyriscope.processor.FFMPEG_LIVE.replace('error', 'quiet')
pyriscope.processor.FFMPEG_ROT = pyriscope.processor.FFMPEG_ROT.replace('error', 'quiet')
pyriscope.processor.FFMPEG_NOROT = pyriscope.processor.FFMPEG_NOROT.replace('error', 'quiet')


def replay_downloaded(bc_name):
    """Boolean indicating if given replay has been downloaded already"""
    for extension in EXTENSIONS:
        fname = cleansefilename(bc_name)

        if os.path.exists(os.path.join(DEFAULT_DOWNLOAD_DIRECTORY, fname + extension)):
            return True
        fname += " REPLAY"
        if os.path.exists(os.path.join(DEFAULT_DOWNLOAD_DIRECTORY, fname + extension)):
            return True

    return False


def rename_live(bc_name):
    """Checks if there are any live broadcasts recorded with that name already and renames.
    Useful if a live drops out and then restarts - without this the previous
    recording would be overwritten"""
    fname = cleansefilename(bc_name)
    for extension in EXTENSIONS:
        filename_start = os.path.join(DEFAULT_DOWNLOAD_DIRECTORY, fname + '.live')
        if os.path.exists(filename_start + extension):
            _ = 1
            while os.path.exists(filename_start + str(_) + extension):
                _ += 1
            os.rename(filename_start + extension, filename_start + str(_) + extension)
            return None


def cleansefilename(bc_name):
    """Makes broadcast names usable as filenames"""
    return bc_name.replace('/', '-').replace(':', '-')


def start_download(bc_id, bc_name):
    """Starts download using pyriscope"""
    os.chdir(DEFAULT_DOWNLOAD_DIRECTORY)
    fname = cleansefilename(bc_name)
    try:
        if replay_downloaded(bc_name):
            return bc_id

        if "REPLAY" in bc_name:
            time.sleep(5)
        rename_live(bc_name)

        url = BROADCAST_URL_FORMAT + bc_id

        pyriscope.processor.process([url, '-C', '-n', fname])

        for bcdescriptor in ['', '.live']:
            for extension in EXTENSIONS:
                filename = fname + bcdescriptor + extension
                if os.path.exists(os.path.join(DEFAULT_DOWNLOAD_DIRECTORY, filename)):
                    return bc_id
        raise Exception(bc_id)

    except SystemExit as _:
        if _.code == 0:
            return bc_id
        else:
            raise Exception(bc_id)

    except BaseException as exceptiondetails:
        with open('{} error.log'.format(fname), mode='a') as errorlog:
            errorlog.write(exceptiondetails)
        raise Exception(bc_id)


def current_datetimestring():
    """Return a string with the date and time"""
    return " ".join([time.strftime('%x'), time.strftime('%X')])


def mute():
    """Write output from our youtube-dl processes to devnull"""
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")


def parse_bc_info(broadcast):
    """Get tuple of broadcast information"""
    bc_id = broadcast['id']
    username = broadcast['username']
    bc_dtstring = broadcast['start']
    bc_datetime = dt_parse(bc_dtstring)

    bc_date = bc_datetime.strftime('%m/%d/%Y')
    bc_time = bc_datetime.strftime('%H:%M:%S')

    bc_name = ' '.join([username, bc_date, bc_time, bc_id])

    return bc_id, bc_name, bc_dtstring


class AutoCap:
    """Class to check notifications stream and start capping new broadcasts"""

    def __init__(self, api, print_status=True):
        self.print_status = print_status
        self.keep_running = True

        self.api = api
        self.config = self.api.session.config

        self.listener = Listener(api=self.api, check_backlog=True)
        self.downloadmgr = DownloadManager(api=self.api)

    def start(self):
        """Starts autocapper loop"""

        while self.keep_running:

            if not os.path.exists(DEFAULT_DOWNLOAD_DIRECTORY):
                os.makedirs(DEFAULT_DOWNLOAD_DIRECTORY)

            new_broadcasts = self.listener.check_for_new()

            if new_broadcasts:
                self._send_to_downloader(new_broadcasts)

            if self.print_status:
                print(self._status)

            time.sleep(self.interval)

        self.downloadmgr.pool.close()
        self.downloadmgr.pool.join()

    def stop(self):
        """Stops autocapper loop"""
        input("Press enter at any time to stop the Autocapper on its next loop\n")
        self.keep_running = False

    def _send_to_downloader(self, new_bcs):
        """Unpack results from listener and start download. Set latest dl time."""
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

    def __init__(self, api, check_backlog=False):
        self.api = api

        self.follows = set([i['username'] for i in self.api.following])
        self.config = self.api.session.config

        self.check_backlog = check_backlog

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
        new = self.new_follows()

        for i in notifications:

            if self.check_if_wanted(i, new):
                new_broadcast_ids.append(parse_bc_info(i))

        if self.check_backlog:
            self.check_backlog = False

        return new_broadcast_ids

    def check_if_wanted(self, broadcast, new):
        """Check if broadcast in notifications string is desired for download"""
        if self.check_backlog:
            return True

        elif new:
            if broadcast['username'] in new:
                return True

        elif self.last_new_bc:
            if dt_parse(broadcast['start']) > dt_parse(self.last_new_bc):
                return True

        return None

    def new_follows(self):
        """Get set of new follows since last check"""
        cur_follows = set([i['username'] for i in self.api.following])
        new_follows = cur_follows - self.follows
        self.follows = cur_follows
        if len(new_follows) > 0:
            return new_follows
        return None

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
        self.retries = dict()
        self.completed_downloads = list()
        self.failed_downloads = list()

        self.pool = Pool(CORES_TO_USE, initializer=mute, maxtasksperchild=1)

    def start_dl(self, bc_id, bc_name):
        """Adds a download task to the multiprocessing pool"""

        self.pool.apply_async(start_download, (bc_id, bc_name), callback=self._dl_complete,
                              error_callback=self._dl_failed)

        self.active_downloads[bc_id] = bc_name

        print("[{0}] Adding Download: {1}".format(current_datetimestring(), bc_name))

    def check_replay(self, bc_id, bc_name):
        """Starts download of broadcast replay if not already gotten"""
        if not replay_downloaded(bc_name):
            print("[{0}] Downloading replay of: {1}".format(current_datetimestring(), bc_name))
            self.start_dl(bc_id, bc_name + " REPLAY")

    def _dl_complete(self, bc_id):
        """Callback method when download completes"""
        bc_name = self.active_downloads[bc_id]
        print("[{0}] Completed: {1}".format(current_datetimestring(), bc_name))
        self.completed_downloads.append((current_datetimestring(), bc_name))
        del self.active_downloads[bc_id]
        self.check_replay(bc_id, bc_name)

    def _dl_failed(self, bc_exception):
        """Callback method when download fails"""
        bc_id = str(bc_exception)
        bc_name = self.active_downloads[bc_id]
        print("[{0}] Failed: {1}".format(current_datetimestring(), bc_name))
        self.failed_downloads.append((current_datetimestring(), bc_name))
        del self.active_downloads[bc_id]
        self.retries[bc_id] = self.retries.get(bc_id, 0) + 1
        if self.retries[bc_id] <= MAX_REDOWNLOAD_ATTEMPTS:

            "[{0}] Attempt ({1} of {2}): Redownloading {3}".format(current_datetimestring(),
                                                                   self.retries[bc_id],
                                                                   MAX_REDOWNLOAD_ATTEMPTS, bc_name)

            self.start_dl(bc_id, bc_name)
