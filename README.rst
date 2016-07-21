==========================
periscope.tv API (periapi)
==========================

WARNING: This script is a proof of concept only. It currently stores your personal peri credential key and secret on your hard drive, unencrypted, in a text file. It is strongly suggested you make a throwaway Twitter for use with this script.

NOTE: As of 7/14/2016 you will need the peri consumer secret and consumer key to use this script.
Please create either :code:`$PWD/.peri.conf` or :code:`$HOME/.peri.conf` containing a JSON dict with :code:`consumer_secret` and :code:`consumer_key`. Don't ask the authors for the values tho! See .peri.conf.example for an example of the structure you need to have in place.

Requirements
------------

Python 3 and whatever is in :code:`requirements.txt`

Getting Setup (for noobs)
-------------------------

1. Install Python 3 if you don't have it.
2. This needs the following packages: youtube-dl, OAuth2, requests, and path.py. To install them, open a terminal window (cmd or Powershell for Windows users). Type each of the following commands and press enter after each one: :code:`pip3 install youtube-dl`; :code:`pip3 install OAuth2`; :code:`pip3 install requests`; :code:`pip3 install path.py`.
3. Enable ffmpeg for youtube-dl: see https://github.com/rg3/youtube-dl#on-windows-how-should-i-set-up-ffmpeg-and-youtube-dl-where-should-i-put-the-exe-files for help. 
4. (Optional) Setup a .conf file for youtube-dl. This lets you set a default download directory among other things. https://github.com/rg3/youtube-dl#configuration
5. Clone this repo (download this repository as a .zip), unzip it somewhere, and 
6. Setup the :code:`.peri.conf` file (delete the :code:`.example` from the end of the filename), open it in a text editor, and replace the gibberish strings with the Periscope Consumer Key and Consumer Secret. If you don't have this info, best of luck, but we can't help.
7. Run :code:`example-cli.py`

Usage
-----

1. Run example-cli.py to execute a very simple command line interface that allows one to follow/unfollow/view followers and turn on autocapping of their broadcasts.
2. On first run, you will need to execute a PIN-based authentication with Twitter. The script will give you a twitter.com url to visit and once you are logged in it will display a PIN. Enter that number into the python console and press enter. 
3. Your credentials will be saved (see the WARNING at the beginning of this readme) so step 2 will not need to be repeated unless your credentials get revoked.
4. You will now be logged into the periscope API and can do a few fun things. More to come
5. (OPTIONAL) Start coding and send me pull requests :)

TODO
----

1. Test coverage
2. Add more API calls
3. UI????

Develop
-------

Just do the usual :code:`python setup.py develop` routine, and then test with the :code:`peritest` command that installs.
