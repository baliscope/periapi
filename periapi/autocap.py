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
CORES_TO_USE = -(-os.cpu_count() // 2)
MAX_DOWNLOAD_ATTEMPTS = 3
EXTENSIONS = ['.mp4', '.ts']

pyriscope.processor.FFMPEG_LIVE = pyriscope.processor.FFMPEG_LIVE.replace('error', 'quiet')
pyriscope.processor.FFMPEG_ROT = pyriscope.processor.FFMPEG_ROT.replace('error', 'quiet')
pyriscope.processor.FFMPEG_NOROT = pyriscope.processor.FFMPEG_NOROT.replace('error', 'quiet')


def replay_downloaded(broadcast):
    """Boolean indicating if given replay has been downloaded already"""
    for extension in EXTENSIONS:

        if os.path.exists(os.path.join(broadcast.download_directory,
                                       broadcast.filename + extension)):
            return True

    return False


def rename_live(broadcast):
    """Checks if there are any live broadcasts recorded with that name already and renames.
    Useful if a live drops out and then restarts - without this the previous
    recording would be overwritten"""
    fname = broadcast.filename
    for extension in EXTENSIONS:
        filename_start = os.path.join(broadcast.download_directory, fname + '.live')
        if os.path.exists(filename_start + extension):
            _ = 1
            while os.path.exists(filename_start + str(_) + extension):
                _ += 1
            os.rename(filename_start + extension, filename_start + str(_) + extension)
            return None


def start_download(broadcast):
    """Starts download using pyriscope"""
    try:
        os.chdir(broadcast.download_directory)

        if broadcast.isreplay and replay_downloaded(broadcast):
            return broadcast

        if broadcast.islive:
            rename_live(broadcast)

        url = BROADCAST_URL_FORMAT + broadcast.id

        pyriscope.processor.process([url, '-C', '-n', broadcast.filename])

        if download_successful(broadcast):
            return True, broadcast.id
        else:
            return False, broadcast.id

    except SystemExit as _:
        if not _.code or _.code == 0:
            return True, broadcast.id
        else:
            return False, broadcast.id

    except BaseException:
        return False, broadcast.id


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


def current_datetimestring():
    """Return a string with the date and time"""
    return " ".join([time.strftime('%x'), time.strftime('%X')])


def initialize_download():
    """Write output from our youtube-dl processes to devnull"""
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")


class Broadcast:
    """Broadcast object"""

    def __init__(self, api, broadcast):
        self.api = api
        self.info = broadcast
        self.info['download_directory'] = self.api.session.config.get('download_directory')

    def update_info(self):
        """Updates broadcast object with latest info from periscope"""
        updates = self.api.get_broadcast_info(self.id)
        dl_directory = self.download_directory
        if not updates:
            self.available = False
            self.state = "DELETED"
        else:
            self.info = updates
            self.info['download_directory'] = dl_directory

    @property
    def id(self):
        """Returns broadcast id"""
        return self.info['id']

    @property
    def download_directory(self):
        """Returns broadcast download directory"""
        return self.info.get('download_directory')

    @property
    def username(self):
        """Returns broadcaster username"""
        return self.info['username']

    @property
    def start(self):
        """Returns ATOM string indicating when broadcast started"""
        return self.info['start']

    @property
    def start_dt(self):
        """Datetime object version of broadcast start time"""
        return dt_parse(self.info['start'])

    @property
    def startdate(self):
        """Human-readable date string of when broadcast started"""
        return self.start_dt.strftime('%m/%d/%Y')

    @property
    def starttime(self):
        """Human-readable time string of when broadcast started"""
        return self.start_dt.strftime('%H:%M:%S')

    @property
    def title(self):
        """Title of broadcast (in the context of the downloader)"""
        if not self.islive and self.available:
            return ' '.join([self.username, self.startdate, self.starttime, self.id, 'REPLAY'])
        return ' '.join([self.username, self.startdate, self.starttime, self.id])

    @property
    def filename(self):
        """Get title string adapted for use as filename"""
        return self.title.replace('/', '-').replace(':', '-')

    @property
    def islive(self):
        """Check if broadcast is running or not"""
        if self.info['state'] == 'RUNNING':
            return True
        return False

    @property
    def isreplay(self):
        """Check if broadcast is replay or not"""
        if not self.islive and self.available:
            return True
        return False

    @property
    def state(self):
        """Get broadcast state string"""
        return self.info['state']

    @state.setter
    def state(self, new_state):
        """Set broadcast state string (useful if broadcast is deleted since peri deletes entire
        broadcast object)"""
        self.info['state'] = new_state

    @property
    def available(self):
        """Check if broadcast is available for replay"""
        return self.info['available_for_replay']

    @available.setter
    def available(self, boolean):
        """Set broadcast availability (if broadcast is deleted - set to False)"""
        self.info['available_for_replay'] = boolean


class AutoCap:
    """Class to check notifications stream and start capping new broadcasts"""

    def __init__(self, api, print_status=True, check_backlog=True):
        self.print_status = print_status
        self.keep_running = True

        self.api = api
        self.config = self.api.session.config

        if not self.config.get('download_directory'):
            self.config['download_directory'] = os.path.join(os.path.expanduser('~'), 'downloads')
            self.config.write()

        self.listener = Listener(api=self.api, check_backlog=check_backlog)
        self.downloadmgr = DownloadManager(api=self.api)

    def start(self):
        """Starts autocapper loop"""

        while self.keep_running:

            if not os.path.exists(self.config.get("download_directory")):
                os.makedirs(self.config.get("download_directory"))

            new_broadcasts = self.listener.check_for_new()

            if new_broadcasts:
                self._send_to_downloader(new_broadcasts)

            if self.print_status:
                print(self._status)

            time.sleep(self.interval)

            self.downloadmgr.redownload_failed()

        self.downloadmgr.pool.close()
        self.downloadmgr.pool.join()

    def stop(self):
        """Stops autocapper loop"""
        input("Press enter at any time to stop the Autocapper on its next loop\n")
        self.keep_running = False

    def _send_to_downloader(self, new_bcs):
        """Unpack results from listener and start download. Set latest dl time."""
        for broadcast in new_bcs:
            self.downloadmgr.start_dl(broadcast)

            if self.listener.last_new_bc:
                if broadcast.start_dt > dt_parse(self.listener.last_new_bc):
                    self.listener.last_new_bc = broadcast.start
            else:
                self.listener.last_new_bc = broadcast.start

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

        new_broadcasts = self.process_notifications(current_notifications)

        if len(new_broadcasts) == 0:
            return None

        return new_broadcasts

    def process_notifications(self, notifications):
        """Process list of broadcasts obtained from notifications API endpoint."""
        new_broadcasts = list()
        new = self.new_follows()

        for i in notifications:

            broadcast = Broadcast(self.api, i)

            if self.check_if_wanted(broadcast, new):
                new_broadcasts.append(broadcast)

        if self.check_backlog:
            self.check_backlog = False

        return new_broadcasts

    def check_if_wanted(self, broadcast, new):
        """Check if broadcast in notifications string is desired for download"""
        if self.check_backlog:
            return True

        elif new:
            if broadcast.username in new:
                return True

        elif self.last_new_bc:
            if broadcast.start_dt > dt_parse(self.last_new_bc):
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
        self.retries = dict()

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

    def get_replay(self, broadcast):
        """Starts download of broadcast replay if not already gotten; or, continues live download"""
        if broadcast.islive:
            broadcast.update_info()
            if broadcast.available and not broadcast.islive:
                print("[{0}] Downloading replay of: {1}".format(current_datetimestring(),
                                                                broadcast.title))
                self.start_dl(broadcast)
            elif broadcast.islive:
                print("[{0}] Continuing live download of: {1}".format(current_datetimestring(),
                                                                      broadcast.title))
                self.start_dl(broadcast)

    def redownload_failed(self):
        """Check list of retries and redownload or send to failed as appropriate"""
        if len(self.retries) == 0:
            return None

        for bc_id in self.retries:
            attempts = self.retries[bc_id][0]
            broadcast = self.retries[bc_id][1]
            if attempts <= MAX_DOWNLOAD_ATTEMPTS:

                "[{0}] Attempt ({1} of {2}): Redownloading {3}".format(current_datetimestring(),
                                                                       self.retries[bc_id],
                                                                       MAX_DOWNLOAD_ATTEMPTS,
                                                                       broadcast.title)

                self.start_dl(broadcast)
            else:
                print("[{0}] Failed: {1}".format(current_datetimestring(), broadcast.title))
                self.failed_downloads.append((current_datetimestring(), broadcast))
                del self.retries[bc_id]

    def _callback_dispatcher(self, results):
        """Unpacks callback argument and passes to appropriate cleanup method"""
        broadcast = self.active_downloads[results[1]]
        download_ok = results[0]
        if download_ok:
            self._dl_complete(broadcast)
        else:
            self._dl_failed(broadcast)

    def _dl_complete(self, broadcast):
        """Callback method when download completes"""
        print("[{0}] Completed: {1}".format(current_datetimestring(), broadcast.title))
        self.completed_downloads.append((current_datetimestring(), broadcast))
        del self.active_downloads[broadcast.id]
        self.get_replay(broadcast)

    def _dl_failed(self, broadcast):
        """Callback method when download fails"""
        self.retries[broadcast.id] = (self.retries.get(broadcast.id, 1) + 1, broadcast)
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
