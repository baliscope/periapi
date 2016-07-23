==========================
periscope.tv API (periapi)
==========================

WARNING: This script is a proof of concept only. It currently stores your personal peri credential key and secret on your hard drive, unencrypted, in a text file. It is strongly suggested you make a throwaway Twitter for use with this script.

NOTE: As of 7/14/2016 you will need the peri consumer secret and consumer key to use this script.
Please create either :code:`$PWD/.peri.conf` or :code:`$HOME/.peri.conf` containing a JSON dict with :code:`consumer_secret` and :code:`consumer_key`. Don't ask the authors for the values tho! See .peri.conf.example for an example of the structure you need to have in place.

Requirements
------------

Python 3.4+ and whatever is in :code:`requirements.txt`

Getting Setup (for noobs)
-------------------------

0. Get a Twitter account setup with Periscope. (If you don't have a phone to do this with, check out OpenPeriscope.)
1. Install Python 3 if you don't have it.
2. This needs the following packages: pyriscope, OAuth2, requests, and path.py. To install them, open a terminal window (cmd or Powershell for Windows users). Type each of the following commands and press enter after each one: :code:`pip3 install pyriscope`; :code:`pip3 install OAuth2`; :code:`pip3 install requests`; :code:`pip3 install path.py`.
3. If you don't have ffmpeg already working with pyriscope, download ffmpeg and place ffmpeg.exe in the same directory as :code:`example-cli.py`
4. Clone this repo (download this repository as a .zip) and unzip it somewhere.
5. Go to the :code:`.peri.conf.example` file, delete the :code:`.example` from the end of the filename, open it in a text editor, and replace the gibberish strings with the Periscope Consumer Key and Consumer Secret. If you don't have this info, best of luck, but we can't help.
6. Run :code:`example-cli.py`

Usage
-----

1. Run :code:`example-cli.py` to execute a very simple command line interface that allows one to follow/unfollow/view followers and turn on autocapping of their broadcasts.
2. On first run, you will need to execute a PIN-based authentication with Twitter. The script will give you a twitter.com url to visit and once you are logged in it will display a PIN. Enter that number into the python console and press enter. 
3. Your credentials will be saved (see the WARNING at the beginning of this readme) so step 2 will not need to be repeated unless your credentials get revoked.
4. You will now be logged into the periscope API and can do a few fun things. More to come
5. (OPTIONAL) Start coding and send me pull requests :)

Functionality Notes
-------------------

1. Once Autocap is started, the program can only be exited by killing it. Graceful exit coming soon(ish).
2. At Autocap startup, this program attempts to download ALL broadcasts in your notification stream, whether or not they are "new". Broadcasts that exist on disk will be marked as "completed" but not re-downloaded.
3. If you add a new account to your "following" list while Autocap is running, this program attempts to download ALL broadcasts of theirs in your notification stream, whether or not they are "new".
4. Other than the two previous exceptions, this program will only download broadcasts with a start time newer than the most recent start time out of all broadcasts downloaded.
5. The notification stream only contains the past 24 hours of broadcasts. Option to download all broadcasts by a user coming soon.
6. All downloads will automatically be converted to mp4 during or after download.
7. Once a live broadcast is finished, an attempt will be made to download the replay for that live broadcast.
8. Every now and then, ffmpeg will print warning statements to console. These can typically be ignored.

TODO
----

1. Test coverage
2. Add more API calls
4. UI????

Develop
-------

Just do the usual :code:`python setup.py develop` routine, and then test with the :code:`peritest` command that installs.
