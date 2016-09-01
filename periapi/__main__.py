#!/usr/bin/env python3
"""
Periscope API for the masses
"""
# pylint: disable=broad-except

import os
import re
import shutil
import sys
import time

from . import PeriAPI
from . import AutoCap

BROADCAST_ID_PATTERN = r'1[a-zA-Z]{12}'


def run():
    """PeriAPI runner"""
    BadCLI()
    sys.exit(0)


def enditall():
    """Terminate program"""
    sys.exit(0)


def get_bc_id():
    """Get broadcast id from user input"""
    bc_userinput = input("\nInput broadcast ID or broadcast URL: ")
    bc_id_match = re.search(BROADCAST_ID_PATTERN, bc_userinput)
    if not bc_id_match:
        print("Broadcast {} not found.".format(bc_userinput))
        return None
    return bc_id_match.group(0)


class BadCLI:
    """Start up a rudimentary CLI"""

    def __init__(self):
        print("Signing in...")
        self.api = PeriAPI()
        self.config = self.api.session.config

        while True:
            try:
                print("\nPlease select from one of the following options:\n")
                print("\t1 - Show followed users")
                print("\t2 - Follow a user")
                print("\t3 - Unfollow a user")
                print("\t4 - Start Autocapper")
                print("\t5 - Cap a single broadcast")
                print("\t6 - Cap all past broadcasts by a user")
                print("\t7 - Change default download directory")
                print("\t8 - Delete live recordings where replay has been downloaded")
                if self.config.get('separate_folders'):
                    print("\t9 - Turn OFF separate folder downloads for each user")
                else:
                    print("\t9 - Turn ON separate folder downloads for each user")
                print("\t0 - Exit\n")
                choice = input("Please select an option (0-9): ")
                if choice == '0':
                    enditall()
                elif choice == '1':
                    self.show_followed_users()
                elif choice == '2':
                    self.follow_user(input("Enter their username. If following more than one, "
                                           "separate them with commas: "))
                elif choice == '3':
                    self.unfollow_user(input("Enter their username. If unfollowing more than one, "
                                             "separate them with commas: "))
                elif choice == '4':
                    if shutil.which('ffmpeg') is not None:
                        self.start_autocapper()
                    else:
                        print("ffmpeg could not be found. "
                              "Please put ffmpeg.exe in {}".format(os.getcwd()))
                elif choice == '5':
                    self.cap_one()
                elif choice == '6':
                    self.cap_user()
                elif choice == '7':
                    self.set_download_directory()
                elif choice == '8':
                    self.cleanup()
                elif choice == '9':
                    self.config['separate_folders'] = not self.config.get('separate_folders')
                else:
                    print("Invalid selection. Please try again.")
            except ValueError as e:
                print(e)
            except KeyboardInterrupt:
                print("Stopping autocapper...")
            except OSError as e:
                print(e)

    def show_followed_users(self):
        """Shows who you're following"""
        for i in self.api.following:
            print(i['username'])

    def follow_user(self, usernames):
        """Tries to find and follow the entered username or usernames"""
        if len(usernames) == 0:
            return None

        for username in [_.strip() for _ in usernames.split(",")]:
            try:
                user_id = self.api.find_user_id(username)
            except ValueError:
                print("User {} could not be found.".format(username))
                continue
            self.api.follow(user_id)
            print("Now following {}.".format(username))

    def unfollow_user(self, usernames):
        """Tries to find and unfollow the entered username or usernames"""
        if len(usernames) == 0:
            return None

        for username in [_.strip() for _ in usernames.split(",")]:
            try:
                user_id = self.api.find_user_id(username)
            except ValueError:
                print("User {} could not be found.".format(username))
                continue
            self.api.unfollow(user_id)
            print("No longer following {}.".format(username))

    def start_autocapper(self, opts_override=None):
        """Start autocapper running"""

        if not opts_override:
            opts = {}

            disable_check = input("Check all prior broadcasts? Can be very resource intensive. "
                                  "(y/n): ")
            opts["check_backlog"] = bool(disable_check.strip()[:1] == "y")

            inv_check = input("Cap others' broadcasts people you're following invite you to? "
                              "(y/n): ")
            opts["cap_invited"] = bool(inv_check.strip()[:1] == "y")
        else:
            opts = opts_override

        try:
            cap = AutoCap(self.api, opts)
            cap.start()
        except OSError as _:
            if "404" in _:
                print(_)
                print("Attempting to re-start autocapper in 15 seconds....")
                time.sleep(15)
                self.start_autocapper(opts_override=opts)
            else:
                raise OSError(_)
        return None

    def set_download_directory(self):
        """Changes the download directory"""
        if not self.config.get('download_directory'):
            self.config['download_directory'] = os.path.join(os.path.expanduser('~'), 'downloads')
            self.config.write()
        print("\nCurrent download directory is: {}".format(self.config.get("download_directory")))
        new_dir = input("New Download Directory: ")
        if os.path.exists(new_dir):
            self.config['download_directory'] = new_dir
            self.config.write()
            print("New directory set.")
            return None
        print("Directory does not exist or is an invalid path.")

    def cleanup(self):
        """Clean up live broadcasts that are duplicates of a downloaded replay"""
        confirmation = input("\nThis may delete files you wish to keep. "
                             "Are you sure you want to do this? (y/n): ")
        if confirmation != 'y':
            print("Canceled.")
            return None

        files_deleted = 0
        for directory, subdirs, files in os.walk(self.config.get('download_directory')):
            ids_to_clean = list()

            for filename in files:
                if 'REPLAY.mp4' in filename:
                    ids_to_clean.append(re.search(BROADCAST_ID_PATTERN, filename).group(0))

            for filename in files:
                if '.live' in filename:
                    try:
                        if re.search(BROADCAST_ID_PATTERN, filename).group(0) in ids_to_clean:
                            os.remove(os.path.join(directory, filename))
                            files_deleted += 1
                    except:
                        print("{} could not be deleted.".format(filename))

            for idx in range(len(subdirs)-1, -1, -1):
                if '.periapi' in subdirs[idx]:
                    del subdirs[idx]

        print("{0} files were deleted.".format(files_deleted))

    def cap_one(self):
        """Get broadcast ID from user and run the cap_one method in autocap"""
        broadcast_id = get_bc_id()
        if not broadcast_id:
            return None
        dummy_opts = {"check_backlog": False, "cap_invited": False}
        cap = AutoCap(self.api, dummy_opts)
        cap.cap_one(broadcast_id)

    def cap_user(self):
        """Get username from user and run cap_user in autocap"""
        username = input("\nInput username: ")
        dummy_opts = {"check_backlog": False, "cap_invited": False}
        cap = AutoCap(self.api, dummy_opts)
        cap.cap_user(username)

    # def heartbomb(self):
    #     """Flood a broadcast with hearts"""
    #     try:
    #         hearts = int(input("\nHow many hearts per second? (Default is 5): "))
    #     except:
    #         hearts = 150
    #     broadcast_id = get_bc_id()
    #     if not broadcast_id:
    #         return None
    #     bc_access = self.api.get_access(broadcast_id)
    #     if bc_access.get('broadcast').get('state') != "RUNNING":
    #         print("Could not initiate heartbomb.")
    #         return None
    #     session = bc_access.get('session')
    #     total_hearts = 0
    #     bc_live = True
    #     while bc_live:
    #         time.sleep(1)
    #         ping = self.api.ping_watching(broadcast_id, session, hearts)
    #         if not ping.get('success'):
    #             bc_live = False
    #         else:
    #             print(ping)
    #             bc_live = \
    #                 bool(self.api.get_broadcast_info(broadcast_id).get('state') == "RUNNING")
    #         total_hearts += hearts
    #     self.api.ping_watching(broadcast_id, session, total_hearts, stop=True)

if __name__ == "__main__":
    run()
