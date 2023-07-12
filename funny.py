# helvum
import subprocess
import pickle
import shlex
import sys
from flask import Flask, request

import pygame

def play_tts(user, res, config):
    tts = "dectalk"
    conf = {}
    try:
        cfg = config[user]
        tts = cfg.get("tts", "dectalk")
        conf = cfg.get("cfg", {})
    except KeyError:
        pass
    command = "echo invalid tts system;exit 1"
    words = res
    if words[0] == "'" or words[0] == '"':
        words = words[1:-1]
    match tts:
        case "dectalk":
            pre = conf.get("pre", "[:np]")
            print("pre" in conf, conf)
            command = f'dectalk -fo "{user}.wav" -pre "[:err ignore] [:phoneme on] {shlex.quote(pre)[1:-1]}" -a {shlex.quote(words)}'
        case "sam":
            phonetic = conf.get("phonetic", "0") != "0"
            pitch = conf.get("pitch", "64")
            speed = shlex.quote(conf.get("speed", "72"))
            throat = shlex.quote(conf.get("throat", "128"))
            mouth = shlex.quote(conf.get("mouth", "128"))
            sing = conf.get("sing", "0") != "0"
            fmt = f"-pitch {pitch} -speed {speed} -throat {throat} -mouth {mouth}"
            if phonetic:
                fmt += " -phonetic"
            if sing:
                fmt += " -sing"
            command = f"sam -wav '{user}.wav' {fmt} {shlex.quote(words)}"
        case "none":
            command = f"exit 1"
    print(command)
    try:
        proc = subprocess.run(command, shell=True, timeout=1)
        if 0 == proc.returncode:
            print("saying")
            sfx = pygame.mixer.Sound(f"{user}.wav")
            pygame.mixer.Sound.play(sfx)
        else: print("failed to play audio")
    except subprocess.TimeoutExpired:
        print("too too long to render audio")
        pass
    except FileNotFoundError:
        print("shit")
        pass
    sys.stdout.flush()



pygame.init()

config = {}
blank_cfg = {}

if not ("banned" in config):
    config["banned"] = []

app = Flask(__name__)

@app.route("/",methods=["POST"])
def post():
    with open("config", "rb") as cfg:
        config = pickle.load(cfg)
    chat = request.get_data().decode().replace("("," ").replace(")"," ").replace(";"," ").replace("`"," ")
    print(chat)
    com = []
    words = chat.split(" ")
    print(words)
    if words[0:3] == ["You", "whisper", "to"]:
        print("I whispering this")
        sys.stdout.flush()
        return "empty",400
    if words[0][0] != "<":
        words[0] = f"<{words[0]}>"
    if words[0] in config["banned"]:
        print("user is tts banned")
        sys.stdout.flush()
        return "empty",400
    cout = 0
    flag_whisper = False
    if words[1:4] == ["whispers", "to", "you:"]:
        flag_whisper = True
    com = []
    print(flag_whisper)
    if flag_whisper:
        com = words[4:]
    else:
        com = words[1:]
    res = " ".join(com)
    ignore = False
    if len(com) == 0:
        print(com)
        com = [""]
    message = "empty"
    if com[0] == "!tts" and flag_whisper:
        ignore = True
        if not (words[0] in config):
            config[words[0]] = blank_cfg.copy()
        conf = config[words[0]]
        if len(com) < 2:
            com.append("invalid_subcommand")
        match com[1]:
            case "help":
                if len(com) < 3:
                    message = (
                        "subcommands: tts,cfg, use !tts help [subcommand] for more help"
                    )
                else:
                    match com[2]:
                        case "tts":
                            message = "!tts tts [sam|dectalk], sets your tts engine"
                        case "cfg":
                            if len(com) < 4:
                                message = "!tts cfg [var=value...], supports quotes, do help cfg <tts> for all values"
                            else:
                                match com[3]:
                                    case "sam":
                                        message = "pitch,throat,mouth,speed, eg:speed=90 to be slightly faster"
                                    case "dectalk":
                                        message = 'pre, eg: pre="[:nd]" to sound like a doctor'
                                    case _:
                                        message = "invalid tts"
                        case _:
                            message = "invallid subcommand"
            case "tts":
                tte = com[2]
                if com[2] not in ["sam", "dectalk"]:
                    tte = "off"
                message = f"changed tts engine: {tte}"
                conf["tts"] = tte
            case "cfg":
                try:
                    message = "changed voice-specific configs: "
                    if not ("cfg" in config[words[0]]):
                        conf["cfg"] = {}
                    for part in shlex.split(" ".join(com[2:]).replace('\\"', '"')):
                        print("part", part)
                        parts = part.split("=")
                        print("parts", parts)
                        var = parts[0]
                        val = parts[1]
                        if (val == "") and var in conf["cfg"]:
                            del conf["cfg"][var]
                        else:
                            conf["cfg"][var] = val
                        message = message + f"{var} "
                except IndexError:
                    pass
            case "ban":
                if not words[0] == "<walksanator>":
                    message = "insufficent perms"
                    pass
                message = f"banned {com[2]}"
                config["banned"].append(f"<{com[2]}>")
            case "unban":
                if not words[0] == "<walksanator>":
                    message = "insufficent perms"
                    pass
                message = f"unbanned {com[2]}"
                config["banned"].remove(f"<{com[2]}>")
            case "clear":
                if not words[0] == "<walksanator>" or words[0] == f"<{com[2]}>":
                    message = "insufficent perms"
                    pass
                message = f"cleared configs for {com[2]}"
                config[f"<{com[2]}>"] = blank_cfg.copy()
            case _:
                message = "invalid command, use !tts help"
    with open("config", "wb") as cfg:
        pickle.dump(config, cfg)
    if ignore:
        sys.stdout.flush()
        return message, 200
    play_tts(words[0], res, config)
    return "empty",200

if __name__ == "__main__":
  app.run()
