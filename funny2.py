#!/usr/bin/env python
from datetime import timedelta
from subprocess import run,PIPE,DEVNULL
import pygame
from random import shuffle
import hashlib

pygame.init()
last = None
while True:
    md5Hashed = None
    with open("out.wav","rb") as f:
        md5Hash = hashlib.md5(f.read())
        md5Hashed = md5Hash.hexdigest()
    print(md5Hashed)
    print(last)
    if md5Hashed == last:
        pygame.time.wait(100)
    else:
        last = md5Hashed
        pygame.mixer.music.load('out.wav')
        pygame.mixer.music.play(0, 0.0)
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        last = md5Hashed
