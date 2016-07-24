==========================
periscope.tv API (periapi)
==========================

WARNING: This script is a proof of concept only. It currently stores your personal peri credential key and secret on your hard drive, unencrypted, in a text file. It is strongly suggested you make a throwaway Twitter for use with this script.

NOTE: As of 7/14/2016 you will need the peri consumer secret and consumer key to use this script.

Getting Setup (for noobs)
-------------------------

0. Get a Twitter account setup with Periscope. You may need to re-verify your Twitter account if it's new after running this program the first time.
1. Install Python 3 if you don't have it.
2. Open a command prompt (Powershell or cmd on Windows, for example) and type :code:`pip3 install https://github.com/baliscope/periapi/archive/master.zip`
3. If you don't have ffmpeg already working with pyriscope, download ffmpeg and, for Windows, add it to path as shown here: http://stackoverflow.com/questions/23400030/windows-7-add-path or place :code:`ffmpeg.exe` in the same directory as :code:`pyriscope.exe` (typically the Scripts folder in your Python install directory).
4. Open a command prompt and type :code:`periapi`.
5. You will need to find the periscope consumer key and consumer secret and input it when you first run the program. Don't ask here for that information. Pastebin contains useful tips.

Requirements
------------

Python 3.4+ and whatever is in :code:`requirements.txt`

Usage
-----

1. Run :code:`periapi` in a console to execute a very simple command line interface that allows one to follow/unfollow/view followers and turn on autocapping of their broadcasts.
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
3. UI????
