#!/usr/bin/env python3
"""
Periscope API for the masses

Portions of the code in this file are Copyright (c) 2015 Russell Harkanson and are available
under The MIT License as part of Pyriscope: https://github.com/rharkanson/pyriscope
"""

import os
import shutil
import time

from subprocess import Popen
from urllib.parse import quote

import requests

from periapi.threaded_download import ThreadPool

BROADCAST_URL_FORMAT = "https://www.periscope.tv/w/"
REPLAY_ACCESS = "https://api.periscope.tv/api/v2/replayPlaylist.m3u8?broadcast_id={}&cookie={}"
PUBLIC_ACCESS = "https://api.periscope.tv/api/v2/getAccessPublic?broadcast_id={0}"
PRIVATE_ACCESS = "https://api.periscope.tv/api/v2/accessChannel"

FAIL_RESUME_WAIT = 15
MAX_DOWNLOAD_ATTEMPTS = 3
DEFAULT_DL_THREADS = 6

EXTENSIONS = ['.mp4', '.ts']
FFMPEG_CONVERT = "ffmpeg -y -v quiet -i \"{0}.ts\" -bsf:a aac_adtstoasc -codec copy \"{0}.mp4\""
FFMPEG_LIVE = "ffmpeg -y -v quiet -i \"{0}\" -c copy \"{1}.ts\""


def convert_download(filename):
    """Uses FFMPEG to convert .ts to .mp4"""
    Popen(FFMPEG_CONVERT.format(filename), shell=True).wait()
    if not os.path.exists("{}.mp4".format(filename)):
        time.sleep(10)
        Popen(FFMPEG_CONVERT.format(filename), shell=True).wait()
    if os.path.exists("{}.mp4".format(filename)):
        try:
            os.remove("{}.ts".format(filename))
        except BaseException:
            pass


def download_successful(broadcast):
    """Checks if download was successful"""
    checks = 3
    waittime = 5

    _ = 0
    while _ < checks:
        for extension in EXTENSIONS:
            if os.path.exists(broadcast.filepathname + extension):
                return True
        time.sleep(waittime)
        _ += 1

    return False


def grab_chunk(url, path, headers, cookies):
    """Downloads one chunk from the periscope replay servers"""
    with open(path, 'wb') as temp_file:
        data = requests.get(url, stream=True, headers=headers, cookies=cookies)
        if not data.ok:
            raise Exception("Chunk download at {} failed.".format(url))
        for block in data.iter_content(4096):
            temp_file.write(block)


def replay_downloaded(broadcast):
    """Boolean indicating if given replay has been downloaded already"""
    for extension in EXTENSIONS:
        if os.path.exists(broadcast.filepathname + extension):
            return True
    return False


class Download:
    """Provides methods to download a broadcast"""

    def __init__(self, broadcast):
        self.broadcast = broadcast
        self.headers = {
            'User-Agent': 'Periscope/3313 (iPhone; iOS 7.1.1; Scale/2.00)',
            "Accept-Encoding": "gzip, deflate",
            }

    def start(self):
        """Start broadcast download"""
        self.broadcast.lock_name = True

        try:
            if self.broadcast.dl_failures > 0:
                time.sleep(FAIL_RESUME_WAIT)
                self.broadcast.update_info()

            if self.broadcast.isreplay and replay_downloaded(self.broadcast):
                self.broadcast.replay_downloaded = True
                return True, self.broadcast

            while (self.broadcast.private or self.broadcast.wait_for_replay) \
                    and self.broadcast.islive:
                time.sleep(FAIL_RESUME_WAIT)
                self.broadcast.update_info()

            if self.broadcast.isreplay:
                self.download_replay()
            elif self.broadcast.islive:
                self.capture_live()

            if download_successful(self.broadcast):
                try:
                    convert_download(self.broadcast.filepathname)
                except BaseException:
                    pass
                if self.broadcast.isreplay:
                    self.broadcast.replay_downloaded = True
                elif self.broadcast.islive:
                    self.broadcast.dl_failures = 0
                return True, self.broadcast

            else:
                self.broadcast.failure_reason = BaseException("Unknown error.")
                return False, self.broadcast

        except BaseException as _:
            self.broadcast.failure_reason = _
            return False, self.broadcast

    def capture_live(self):
        """Get necessary info to cap a live broadcast with FFMPEG, and send to FFMPEG"""

        payload = {'broadcast_id': self.broadcast.id, 'cookie': self.broadcast.cookie}

        access = requests.post(PRIVATE_ACCESS, json=payload).json()

        if not access.get('hls_url'):
            raise Exception("Couldn't get live stream download url. Usually means broadcast has"
                            " been deleted/broadcaster has been banned.")

        temp_dir = os.path.join(self.broadcast.download_directory,
                                ".periapi.{}".format(self.broadcast.filetitle))

        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        filepaths = []
        _ = 0
        while self.broadcast.islive:
            _ += 1
            self.broadcast.dl_times.append(time.time())
            filepaths.append(os.path.join(temp_dir, "chunk{}".format(_)))

            download_command = FFMPEG_LIVE.format(access.get('hls_url'), filepaths[-1])
            Popen(download_command, shell=True).wait()

            self.broadcast.update_info()

        for ext in EXTENSIONS:
            if os.path.isfile("{}{}".format(self.broadcast.filepathname, ext)):
                _ = 1
                while os.path.isfile("{}.old-{}{}".format(self.broadcast.filepathname, _, ext)):
                    _ += 1
                os.rename("{}{}".format(self.broadcast.filepathname, ext),
                          "{}.old-{}{}".format(self.broadcast.filepathname, _, ext))

        with open("{}.ts".format(self.broadcast.filepathname), 'wb') as handle:
            for path in filepaths:
                chunk = '{}.ts'.format(path)
                if not os.path.exists(chunk) or os.path.getsize(chunk) == 0:
                    continue
                with open(chunk, 'rb') as ts_file:
                    handle.write(ts_file.read())

        try:
            shutil.rmtree(temp_dir)
        except BaseException:
            pass

    def download_replay(self):
        """Download chunks of broadcast replay and assemble into single .ts"""
        if self.broadcast.private:
            replay_info, cookies = self._get_chunk_info_private()
        else:
            replay_info, cookies = self._get_chunk_info()

        server_directory = '/'.join(replay_info.url.split('/')[:-1])
        chunks = [i.strip() for i in replay_info.text.split() if "chunk" in i.lower()]

        if len(chunks) == 0:
            raise Exception("No chunks available for download. May be authentication issue.")

        temp_dir = os.path.join(self.broadcast.download_directory,
                                ".periapi.{}".format(self.broadcast.filetitle))

        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        chunk_pool = ThreadPool(self.broadcast.title, DEFAULT_DL_THREADS, len(chunks))

        for chunk in chunks:
            path = os.path.join(temp_dir, chunk)
            url = '/'.join((server_directory, chunk))
            chunk_pool.add_task(grab_chunk, url, path, self.headers, cookies)

        self.broadcast.dl_times.append(time.time())

        chunk_pool.wait_completion()

        with open("{}.ts".format(self.broadcast.filepathname), 'wb') as handle:
            for chunk in chunks:
                chunk_path = os.path.join(temp_dir, chunk)
                if not os.path.exists(chunk_path) or os.path.getsize(chunk_path) == 0:
                    break
                with open(chunk_path, 'rb') as ts_file:
                    handle.write(ts_file.read())

        if chunk_pool.is_complete() and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except BaseException:
                pass

    def _get_chunk_info(self):
        """Get the necessary credentials and list of chunks to download a replay"""
        with requests.Session() as _:
            _.headers.update(self.headers)
            access = _.get(PUBLIC_ACCESS.format(self.broadcast.id)).json()
            replay_info = _.get(access['replay_url'])
            self.headers = _.headers
            cookies = _.cookies

        return replay_info, cookies

    def _get_chunk_info_private(self):
        """Get the necessary credentials and list of chunks to download a private replay"""
        replay_url = REPLAY_ACCESS.format(self.broadcast.id, quote(self.broadcast.cookie))

        with requests.Session() as _:
            _.headers.update(self.headers)
            playlist = _.get(replay_url)
            replay_info = _.get(playlist.url)
            self.headers = _.headers
            cookies = _.cookies

        return replay_info, cookies
