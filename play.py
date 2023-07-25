#!/usr/bin/env python
from datetime import timedelta
from subprocess import run,PIPE,DEVNULL
import pygame
from random import shuffle
from sys import argv
from os import environ, path, listdir
from regex import compile
from time import time
from pynput.keyboard import Listener
from queue import LifoQueue
quoted = compile('"(.*?)"')

pygame.init()
fmts = run(["sh","-c","openmpt123 -h | grep xm,"],stdout=PIPE).stdout.decode().split(", ")
TRACKER_FORMATS = [f.strip() for f in fmts ]

global db_skip
global db_paused
global db_stop
global db_back
global paused


db_skip = False
db_paused = False
db_stop = False
db_back = False
paused = False


def on_press(key):
    global db_skip
    global db_paused
    global db_stop
    global db_back
    if str(key) == 'Key.media_next':
        db_skip = True
    elif str(key) == 'Key.media_play_pause':
        db_paused = True
    elif str(key) == '<269025045>':
        db_stop = True
    elif str(key) == 'Key.media_previous':
        db_back = True
    else: 
        #print("unknown key:", str(key))
        pass

def play_path(path:str ) -> bool:
    truename = path
    global db_skip
    global db_paused
    global db_stop
    global db_back
    global paused
    print("opening: ",path)
    if path.split(".")[-1] in TRACKER_FORMATS:
        print("rendering tracker: ",truename)
        t1 = time()
        t = run(["openmpt123","--force","--output","/tmp/tr_render.wav",path],stdout=DEVNULL,stderr=DEVNULL)
        print(f"converted in {timedelta(seconds=time()-t1)} seconds")
        path = "/tmp/tr_render.wav"
    sound = pygame.mixer.Sound(path)
    print("playing,",truename,"that is",timedelta(seconds=sound.get_length()),"seconds long")
    waiter = pygame.mixer.Sound.play(sound)
    while waiter.get_busy():
        if db_skip:
            waiter.stop()
            db_skip = False
            break

        if db_paused:
            if paused:
                waiter.unpause()
                paused = False
            else:
                waiter.pause()
                db_paused = False
                paused = True
            db_paused = False

        if db_stop:
            exit()

        if db_back:
            db_back = False
            waiter.stop()
            return True

        pygame.time.wait(100)
    return False

def get_songs(file_or_path: str) -> list[str]:
    if path.isdir(file_or_path):
        if file_or_path[-1] != "/": file_or_path = f"{file_or_path}/"
        q = []
        for file in sorted(listdir(file_or_path)):
            q.extend(
                get_songs(
                    f"{file_or_path}{file}",
                )
            )
        q.sort(reverse=True)
        return q
    else:
        file = file_or_path
        ext = file.split(".")[-1]
        match ext:
            case "m3u":
                contents = ""
                with open(file,"r") as f:
                    contents = f.read()
                lines = contents.splitlines()
                lines.reverse()
                final = []
                for l in lines:
                    if l.split(".")[-1] == "m3u":
                        s = get_songs(l)
                        final.extend(s)
                    else: final.append(l)
                return final
            case _:
                return [file]

listener_thread = Listener(on_press=on_press, on_release=None)
listener_thread.start()

queue = LifoQueue()
passed = [] #maximum back of 32
once_true = True
def filter(data):
    seen = set()
    seen_add = seen.add
    return [x for x in data if not (x in seen or seen_add(x))]

while environ.get("loop")!=None or once_true:
    once_true = False
    files = argv[1:]
    tq = []
    for file in files:
        tq.extend(get_songs(file))
    filt = filter(tq)
    if environ.get("shuf") != None:
        print("shuffle")
        shuffle(filt)
    for f in filt: queue.put(f)
    if queue.empty():
        raise ValueError("no songs were queued up")
    while not queue.empty():
        song_pat = queue.get()
        if song_pat[0] == "@":
            print("inlined: ",song_pat)
            sub = []
            for inline in quoted.finditer(song_pat):
                sub.append(inline.captures()[0][1:-1])
            sub.reverse()
            for l in sub: queue.put(l)
        else:
            back = play_path(song_pat)
            if back and len(passed) == 0:
                print("history is empty, suffer, playing next song anyways")
            if back and len(passed) != 0:
                queue.put(song_pat)
                queue.put(passed.pop())
            else:
                passed.append(song_pat)
                if len(passed) > 32:
                    del passed[0]
queue.pop()