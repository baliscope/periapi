=========================
periscope.tv API (periapi)
==========================

WARNING: This script is a proof of concept only. It currently stores your personal peri credential key and secret on your hard drive, unencrypted, in a text file. It is strongly suggested you make a throwaway Twitter for use with this script.

NOTE: As of 7/14/2016 you will need the peri consumer secret and consumer key to use this script.
Please create either `$PWD/.peri.conf` or `$HOME/.peri.conf` containing a JSON dict with `consumer_secret` and `consumer_key`. Don't ask the authors for the values tho!

Requirements
------------

Python 3 and whatever is in `requirements.txt`

Usage
-----

1. Run examples.py to execute a brief demonstration of the functionality enabled so far.
2. On first run, you will need to execute a PIN-based authentication with Twitter. The script will launch a web browser window and once you are logged in it will display a PIN. Enter that number into the python console and press enter. 
3. Your credentials will be saved (see the WARNING at the beginning of this readme) so steps 1 and 2 will not need to be repeated unless your credentials get revoked.
4. You will now be logged into the periscope API, a few API functions will get executed, and the results will be printed to console.
5. (OPTIONAL) Start coding and send me pull requests :)

TODO
----

1. Implement autocapper (pyriscope? youtube-dl?)
2. Add a listener that reviews the notifications stream and autocaps any new broadcasts.
