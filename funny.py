# helvum
import subprocess
import pickle
import shlex
import sys
from flask import Flask, request
from gtts import gTTS

import pygame
import re
replace_pattern = r"<.+?, ?[qweasd]+?>"
def play_tts(user, words, config):
    chat = re.sub(replace_pattern,"compiled_pattern",words)
    tts = "dectalk"
    conf = {}
    try:
        cfg = config[user]
        tts = cfg.get("tts", "dectalk")
        conf = cfg.get("cfg", {})
    except KeyError:
        pass
    command = "echo invalid tts system;exit 1"
    match tts:
        case "dectalk":
            pre = conf.get("pre", "[:np]").replace("[m]","[:mode math on]").replace("[:nx]","[:nh][:dv ap 2511][:dv gv 652][:dv hs 50000][:volume set 10]")
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
        case "google":
            tts = gTTS(words)
            tts.save(f"{user}.wav")
            command = "echo google"
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
    req = request.get_data().decode()
    print("req:",req)
    chat = req\
        .replace("("," ").replace(")"," ")\
        .replace(";"," ").replace("`"," ")\
        .replace("[m]","[:mode math on]")\
        .replace("[:nx]","[:nh][:dv ap 2511][:dv gv 652][:dv hs 50000][:volume set 10]")
    print("chat:",chat)
    com = []
    words = chat.split(" ")
    if len(words) <= 1:
        return "empty", 400
    print("words:",words)
    if words[0:3] == ["You", "whisper", "to"]:
        print("I whispering this")
        sys.stdout.flush()
        return "empty",400
    if words[0][0] != "<":
        words[0] = f"<{words[0]}>"
    
    if words[0][1] == "@":
        words[0] = words[0].replace("@","",1)

    if words[0] == "<[Discord>":
        print(chat)
        message = re.search(r"\[Discord \| (.*?)\] (.*)",chat)
        new_uname = message.group(1).replace(" ","_")
        print("new username", new_uname)
        new_body = message.group(2)+"\n"+("\n".join(chat.split("\n")[1:]))
        print("new body",new_body)
        if new_body.startswith(" Replying to @"):
            print("Chat:",chatt)
            new_body = " ".join(chat.split("\n")[1:])
            print("removed reply",new_body)
        words = ("a "+new_body).split(" ")       
        words[0] = f"<{words[0][:-1]}>"
        if words[1] == "(Replying":
            words = " ".join(words).split(")")[1:].join(")").split(" ")
    

    print("post-processing", words)

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
                        "subcommands: tts,cfg,steal use !tts help [subcommand] for more help"
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
                if com[2] not in ["sam", "dectalk","google"]:
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
            case "allow":
                message = f"allowed {com[2]}"
                config["allowed"].append(f"<{com[2]}>")
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
            case "steal":
                if len(com) > 2:
                    print(f"stealing from {com[2]} and giving to {words[0]}")
                    config[words[0]] = config.get(f"<{com[2]}>")
                    message = f"stole configs from {com[2]}"
                else: message = f"you need to specify a username"
            case "remap":
                if len(com) > 2:
                    print("remapping username")
                    config[words[0]]["remap"] = com[2]
                    message = f"remapped /msg to {com[2]}"
                else: message = "you need to specify a username"
            case _:
                print(f"failed to steal from {com[2]} and giving to {words[0]}")
                message = "invalid command, use !tts help"
    
    if words[0] in config["banned"]:
        print("user is tts banned")
        sys.stdout.flush()
        return "empty",400
    # if config.get("allowed") is None: config["allowed"] = []
    # if (not (words[0] in config["allowed"])) and (words[0] != "<walksanator>"):
        # print("user is tts whitelisted")
        # print(config["allowed"])
        # sys.stdout.flush()
        # return "empty",400
    
    with open("config", "wb") as cfg:
        pickle.dump(config, cfg)
    if ignore:
        sys.stdout.flush()
        return "/msg "+ config.get(words[0],{}).get("remap",words[0][1:-1]) + " " + message, 200
    play_tts(words[0], res, config)
    return "empty",200

if __name__ == "__main__":
  app.run()
