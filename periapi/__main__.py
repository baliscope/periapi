#!/usr/bin/env python3
"""
Periscope API for the masses
"""
# pylint: disable=broad-except

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

        while True:
            try:
                print("\nPlease select from one of the following options:\n")
                print("\t1 - Show followed users")
                print("\t2 - Follow a user")
                print("\t3 - Unfollow a user")
                print("\t4 - Start Autocapper")
                print("\t0 - Exit this piece of shit software\n")
                choice = input("Please select an option (0-4): ")
                if choice == '0':
                    enditall()
                elif choice == '1':
                    self.show_followed_users()
                elif choice == '2':
                    self.follow_user(input("Enter their username: "))
                elif choice == '3':
                    self.unfollow_user(input("Enter their username: "))
                elif choice == '4':
                    self.start_autocapper()
                else:
                    print("Invalid selection. Please try again.")
            except ValueError as e:
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

    def unfollow_user(self, username):
        """Tries to find and unfollow the entered username"""
        try:
            user_id = self.api.find_user_id(username)
        except ValueError:
            print("User could not be found.")
            return None
        self.api.unfollow(user_id)

    def start_autocapper(self):
        """Start autocapper running"""
        cap = AutoCap(self.api)
        cap.start()


if __name__ == "__main__":
    run()
