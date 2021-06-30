#!/usr/bin/python3

from mpv import ShutdownError
from PIL import Image, ImageDraw, ImageFont
from time import sleep, time_ns
import argparse
import json
import os
import io
import sys
from datetime import datetime

import mpv
import requests

API_SECRET="YOUR KEY HERE"
API_ENDPOINT="https://www.handyfeeling.com/api/v1/"

TIMEOUT = 10 * 1000 # 10 seconds

time_sync_initial_offset = 0
time_sync_aggregate_offset = 0
time_sync_average_offset = 0
time_syncs = 0

parser = argparse.ArgumentParser(description='Handy MPV sync Utility')
parser.add_argument('file', metavar='file', type=str,
                   help='The file to play')
parser.add_argument("--double", action="store_true", help='enable 2x speed conversion')

# this code is actually really dumb, should refactor, an intern probably
# did this. I'm just copying the JS code from the site.

def save_server_time():
    with open("/home/kiniamaro/Git/Python/handy_mpv/server_time.json", 'w') as f:
        json.dump({
            "last_saved": time_ns(),
            "time_sync_average_offset": time_sync_average_offset,
            "time_sync_initial_offset": time_sync_initial_offset
        }, f)

def get_saved_time():
    with open("/home/kiniamaro/Git/Python/handy_mpv/server_time.json", 'r') as f:
        time = json.load(f)
        return time

def get_server_time():
    time_now = int(time_ns() / 1000000)
    return int(time_now + time_sync_average_offset + time_sync_initial_offset)

def update_server_time():
    global time_sync_initial_offset, time_sync_aggregate_offset, \
            time_sync_average_offset, time_syncs

    send_time = int(time_ns() / 1000000) # don't ask
    r = requests.get(f'{API_ENDPOINT}{API_SECRET}/getServerTime')
    data = json.loads(r.text)
    server_time = data['serverTime']
    print(server_time)
    time_now = int(time_ns() / 1000000)
    print(time_now)
    rtd = time_now - send_time
    estimated_server_time_now = int(server_time + rtd / 2)

    # this part here, real dumb.
    if time_syncs == 0:
        time_sync_initial_offset = estimated_server_time_now - time_now
        print(f'initial offset {time_sync_initial_offset} ms')
    else:
        offset = estimated_server_time_now - time_now - time_sync_initial_offset
        time_sync_aggregate_offset += offset
        time_sync_average_offset = time_sync_aggregate_offset / time_syncs

    time_syncs += 1
    if time_syncs < 30:
        update_server_time()
    else:
        print(f'we in sync, Average offset is: {int(time_sync_average_offset)} ms')
        return


def find_script(video_path):
    video_name = video_path.replace('.' + str.split(video_path, '.')[-1:][0], '')
    script_path = f'{video_name}.funscript'
    if (os.path.exists(script_path)):
        print(f'script found for video: {video_name}')
    return script_path

def script_2x(script_file):
    with open(script_file) as f:
        script = json.loads(f.read())

    edited = []
    for action in script['actions']:
        action['pos'] = 5
        edited.append(action)

    final = []
    for x in range(len(edited)):
        if edited[x]['pos'] == 95:
            edited[x]['pos'] = 99
        final.append(edited[x])

        if x == len(edited) - 1:
            break

        new_pos = {}
        new_pos['at'] = (edited[x + 1]['at'] + edited[x]['at']) / 2
        new_pos['pos'] = 99
        final.append(new_pos)

    script['actions'] = final
    return (script_file, json.dumps(script))

def upload_script(script, double=False):

    if not double:
        r = requests.post("https://www.handyfeeling.com/api/sync/upload", files={'syncFile': open(script, 'rb')})
    else:
        r = requests.post("https://www.handyfeeling.com/api/sync/upload", files={'syncFile': script})
    data = json.loads(r.text)
    payload = {
        "url": data['url'],
        "filename": data['filename'],
        "data": data['size'],
        "timeout": TIMEOUT
    }
    r = requests.get(f'{API_ENDPOINT}{API_SECRET}/syncPrepare', params=payload)
    print(r.text)
    data = json.loads(r.text)

print('Getting Handy Status')
r = requests.get(f'{API_ENDPOINT}{API_SECRET}/getStatus', params={'timeout': TIMEOUT})
data = json.loads(r.text)

if not data['success']:
    print('Couldn\'t Sync with Handy, Exiting.')
    exit()

print('Handy connected, Uploading script!')

args = parser.parse_args()
script = find_script(args.file)
if args.double:
    upload_script(script_2x(script), True)
else:
    upload_script(script)


saved_time = get_saved_time()

if  time_ns() - saved_time['last_saved'] < 3600000000000:
    time_sync_average_offset = saved_time['time_sync_average_offset']
    time_sync_initial_offset = saved_time['time_sync_initial_offset']
else :
    update_server_time()
    save_server_time()

player = mpv.MPV(input_default_bindings=True, input_vo_keyboard=True, osc=True)
player.play(args.file)
font = ImageFont.truetype('DejaVuSans.ttf', 40)


overlay = player.create_image_overlay()
img = Image.new('RGBA', (400, 150),  (255, 255, 255, 0))
d = ImageDraw.Draw(img)

sync = 0

def sync_play(time=0, play='true'):
    payload = {
        'play': play,
        'serverTime': get_server_time(),
        'time': time
    }
    r = requests.get(f'{API_ENDPOINT}{API_SECRET}/syncPlay', params=payload)
    print(r.text)

@player.on_key_press('up')
def my_up_binding():
    value = player._get_property('playback-time')
    time_ms = int(value * 1000)
    print(time_ms)
    sync_play(time_ms, 'false')

@player.on_key_press('q')
def my_q_binding():
    global player
    sync_play(0, 'false')
    player.quit()
    del player
    os._exit(-1)


@player.on_key_press('down')
def my_down_binding():
    value = player._get_property('playback-time')
    time_ms = int(value * 1000)
    print(time_ms)
    sync_play(time_ms, 'true')

@player.event_callback('playback-restart')
def file_restart(event):
    value = player._get_property('playback-time')
    time_ms = int(value * 1000)
    print(time_ms)
    sync_play(time_ms)
    print(f'Now playing at {time_ms}s')

@player.event_callback('shutdown')
def callback_shutdown(event):
    sync_play(0, 'false')
    player.quit()
    sys.exit()

@player.event_callback('pause')
def video_pause(event):
    sync_play(0, 'false')

@player.event_callback('unpause')
def video_unpause(event):
    value = player._get_property('playback-time')
    time_ms = int(value * 1000)
    sync_play(time_ms, 'true')


try:
    player.wait_for_playback()
except ShutdownError as e:
    sync_play(0, 'false')
    del player
    exit()