# handy-mpv

Simple script to play funscripts using mpv and the power of python.

## Shortcuts

```
Q : Quit application

up arrow: pause script playback but keep video playing.

down arrow: Re-sync script / restart script playback. use this if for some reason your script becomes out of sync.

all other mpv shortcuts should work as inteded.

```

## Installation / requirements

1. clone this repo
2. create a virtualenv `python -m venv venv`
3. activate venv `. venv/bin/activate`
4. install dependencies `pip install -r requirements.txt`
5. copy `config.py.example` to `config.py`, `cp config.py.example config.py`
6. Setup your handy key in the `config.py` file.
```python
# ...

API_SECRET="YOUR KEY HERE"
TIME_SYNC_FILE="/tmp/server_time.json"

#...
```

## Usage
```bash
# example usage
$ python app.py yourscript {args}

#arguments

--double: doubles every stroke in the provided script (does not modify the actual file)

This option is mostly created for fapheroes. results may vary for normal scripts but sometimes creates very interesting results.

for fapheroes however, this makes it so every beat is a full stroke. so assuming you have 4 beats such as:

O---O---O---O

the resulting motion will be:

up-down-up-down-up-down-up

instead of:

up---down---up---down


this was created to more closely match the way I would play fapheroes without the handy.

```

## aditional notes

* on startup, the script will do a time sync with the handy server to insure accurate strokes. The server delay is stored in a file and the sync will no re-happen for an hour after that.

* on the first sync with the device. it is usually required to run the script twice. if your video never starts. it's probably for this reason. simply re-run the script.

* pausing the video will pause the script. however, if you press the resync button. the script will start playing with the video still paused.

* scrubbing the player automatically scrubs  the script to the appropriate timestamp.

* If you have a looping video, the script will also loop.
