==========================
periscope.tv API (periapi)
==========================

NOTE: This script is a proof of concept only. It currently stores your personal Periscope credential key and secret on your hard drive, unencrypted, in a text file. Your Twitter account cannot be accessed with this information but your Periscope can.

Features
--------

* Download periscope broadcasts (single broadcast or a user's entire broadcast history)
* Auto-capture broadcasts (autocap)
* Captures live broadcasts, replays, and private replays (capturing private live broadcasts coming soon)
* Implements the Periscope.tv API - enable autocap in this program and use Periscope on your phone as normal. When you follow a user on your phone, autocap will start watching for their broadcasts.
* Or, just follow and unfollow users right from within periapi!
* Detects when a live broadcast "stutters" and resumes capture
* Automatically grabs replay after live broadcast ends

Getting Setup (for noobs)
-------------------------

For Windows Users: Download https://github.com/baliscope/periapi/blob/master/baliscope.zip to get a folder containing everything you need to run periapi. This version is entirely portable - the default download location and configuration file location are in the same folder you extract it to. Run :code:`periapi-standalone.exe` and then go to step 5 below.

0. Have or make a Twitter account. (You may need to re-verify your Twitter account if it's brand new after running this program the first time.)
1. Install Python 3 if you don't have it. Python 3.4 or better is needed. https://www.python.org/downloads/
2. Open a command prompt (Powershell or cmd on Windows, for example) and type :code:`pip3 install https://github.com/baliscope/periapi/archive/master.zip`. This will install periapi and its dependencies.
3. Download ffmpeg and, for Windows, add :code:`ffmpeg.exe` to path as shown here: http://stackoverflow.com/questions/23400030/windows-7-add-path or place :code:`ffmpeg.exe` in the same directory as :code:`periapi.exe` (typically the Scripts folder in your Python install directory).
4. Open a command prompt and type :code:`periapi`.
5. You will need to have the periscope consumer key and consumer secret and input it the first time you run the program. Don't ask here for that information. Pastebin contains useful tips.
6. Default download directory is :code:`~\Downloads` (on Windows, this is :code:`C:\Users\<your name>\Downloads`).

Requirements
------------

Python 3.4+ and whatever is in :code:`requirements.txt`

Usage
-----

1. Run :code:`periapi` in a console to execute a  simple command line interface.
2. On first run, you will need to execute a PIN-based authentication with Twitter. The script will give you a twitter.com url to visit and once you are logged in, Twitter will give you a temporary PIN. Enter that number into the python console and press enter. 
3. Your Periscope (not Twitter) credentials will be saved (see the NOTE at the beginning of this readme) so step 2 will not need to be repeated unless your credentials get revoked.
4. You will now be logged into the periscope API and can do a few things. More to come.

Functionality Notes
-------------------

1. Once Autocap is started, the program can only be exited by killing it. (Sending a Keyboard Interrupt (Ctrl + C) typically brings it back to the main menu but sometimes Multiprocessing throws a fit over this. Downloads should be killed immediately but their process may be orphaned.)
2. At Autocap startup you have the option to download ALL broadcasts in your notification stream, whether or not they are "new". Broadcasts that exist on disk will be marked as "completed" but not re-downloaded. If you follow many people this can be very resource intensive.
3. At Autocap startup you also have the option to download broadcasts you are invited to in addition to the broadcasts of people you're following. If you are following people who share a lot of broadcasts that you don't care about, turning this off is recommmended.
4. If you add a new account to your "following" list while Autocap is running, this program attempts to download ALL of their broadcasts in your notification stream (i.e. in the past 24 hours), whether or not those broadcasts are "new".
5. At first start, Autocap will start download of all currently live broadcasts regardless of the broadcast start time. Other than this, its behavior is only to cap broadcasts that start after Autocap is started except when check backlog is flagged to yes or if a new user is added to follows.
6. The notification stream only contains the past 24 hours of broadcasts. 
7. All downloads will automatically be converted to mp4 during or after download.
8. Once a live broadcast is finished, an attempt will be made to download the replay for that live broadcast.
9. If a replay is being downloaded and the replay is deleted during download, the replay download will stop and leave behind a folder containing what fragments of the replay it was able to grab.

Acknowledgements
----------------

* Dolos for teaching me how to actually write Python (blame for all errors and shitty programming is on me, though!)
* Russel Harkanson for pyriscope, from which I took ideas for how to arrange the download logic
* crusherw for providing a patch to pyriscope that fixes threadpool starvation bugs
* All the folks who've helped me find bugs and provided suggestions for features (too many to name ;) )

TODO
----

1. Test coverage
2. Add more API calls
3. UI????
