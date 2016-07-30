#!/usr/bin/env python3
"""
Periscope API for the masses
"""
# pylint: disable=broad-except

import os
import shutil
import sys

from . import PeriAPI
from . import AutoCap


def run():
    """PeriAPI runner"""
    BadCLI()
    sys.exit(0)


def enditall():
    """Terminate program"""
    sys.exit(0)


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
                print("\t5 - Change default download directory")
                print("\t0 - Exit\n")
                choice = input("Please select an option (0-5): ")
                if choice == '0':
                    enditall()
                elif choice == '1':
                    self.show_followed_users()
                elif choice == '2':
                    self.follow_user(input("Enter their username: "))
                elif choice == '3':
                    self.unfollow_user(input("Enter their username: "))
                elif choice == '4':
                    if shutil.which('ffmpeg') is not None:
                        self.start_autocapper()
                    else:
                        print("ffmpeg could not be found. "
                              "Please put ffmpeg.exe in {}".format(os.getcwd()))
                elif choice == '5':
                    self.set_download_directory()
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

    def follow_user(self, username):
        """Tries to find and follow the entered username"""
        try:
            user_id = self.api.find_user_id(username)
        except ValueError:
            print("User could not be found.")
            return None
        self.api.follow(user_id)
        print("Now following {}.".format(username))

    def unfollow_user(self, username):
        """Tries to find and unfollow the entered username"""
        try:
            user_id = self.api.find_user_id(username)
        except ValueError:
            print("User could not be found.")
            return None
        self.api.unfollow(user_id)
        print("No longer following {}.".format(username))

    def start_autocapper(self):
        """Start autocapper running"""
        opts = {}

        disable_check = input("Check all prior broadcasts? Can be very resource intensive. (y/n): ")
        opts["check_backlog"] = bool(disable_check.strip()[:1] == "y")

        inv_check = input("Cap others' broadcasts people you're following invite you to? (y/n): ")
        opts["cap_invited"] = bool(inv_check.strip()[:1] == "y")

        cap = AutoCap(self.api, opts)
        cap.start()

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


if __name__ == "__main__":
    run()
