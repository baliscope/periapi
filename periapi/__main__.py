#!/usr/bin/env python3
"""
Periscope API for the poor
"""
#pylint: disable=broad-except

import sys
import logging

from argparse import ArgumentParser

from . import PeriAPI
from . import __version__


def run():
    """PeriAPI runner"""
    args = ArgumentParser()
    args.add_argument("--verbose", "-v", action="store_true")
    args.add_argument("follow", nargs="*", help="Follow a user")

    args = args.parse_args()

    logging.basicConfig(
        level=logging.DEBUG
        if args.verbose else
        logging.INFO
        )
    logging.getLogger("requests").setLevel(
        level=logging.DEBUG
        if args.verbose else
        logging.WARN
        )

    logging.info("Running PeriAPI v%s", __version__)
    papi = PeriAPI()
    logging.info("You are %s [%s / %s]",
        papi.session.name, papi.session.uid, papi.pubid)
    for user in sys.argv[1:]:
        try:
            uid = papi.find_user_id(user)
            logging.info("Follow %s (%s): %r", user, uid, papi.follow(uid))
        except Exception:
            logging.exception("Failed to lookup user: %s", user)

    logging.info("following: %r",
        {u["display_name"]: u["username"] for u in  papi.following})
    logging.info("and their broadcasts: %r", {(b["id"], b["state"]): b["username"] for b in papi.notifications})
    sys.exit(0)

if __name__ == "__main__":
    run()
