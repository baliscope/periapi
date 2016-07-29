#!/usr/bin/env python3
"""
Periscope API for the masses
"""

import os
import time

import pyriscope.processor

BROADCAST_URL_FORMAT = 'https://www.periscope.tv/w/'
EXTENSIONS = ['.mp4', '.ts']
MAX_DOWNLOAD_ATTEMPTS = 3

pyriscope.processor.FFMPEG_LIVE = pyriscope.processor.FFMPEG_LIVE.replace('error', 'quiet')
pyriscope.processor.FFMPEG_ROT = pyriscope.processor.FFMPEG_ROT.replace('error', 'quiet')
pyriscope.processor.FFMPEG_NOROT = pyriscope.processor.FFMPEG_NOROT.replace('error', 'quiet')


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


class Download:
    """Downloads a broadcast"""

    def __init__(self, broadcast):
        self.broadcast = broadcast
        
    def start(self):
        try:
            self.broadcast.dl_times.append(time.time())

            os.chdir(self.broadcast.download_directory)

            if self.broadcast.isreplay and replay_downloaded(self.broadcast):
                return True, self.broadcast

            if self.broadcast.private and self.broadcast.isreplay:
                self.broadcast.api.lookup_private(self.broadcast.id)

            url = BROADCAST_URL_FORMAT + self.broadcast.id

            pyriscope.processor.process([url, '-C', '-n', self.broadcast.filename])

            if download_successful(self.broadcast):
                return True, self.broadcast
            else:
                return False, self.broadcast

        except SystemExit as _:
            if not _.code or _.code == 0:
                return True, self.broadcast
            else:
                return False, self.broadcast

        except BaseException:
            return False, self.broadcast

        finally:
            if self.broadcast.islive:
                rename_live(self.broadcast)
