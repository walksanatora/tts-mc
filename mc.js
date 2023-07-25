function main() {
    context.releaseLock()
    const uname = Player.getPlayer().getName().getString();
    const message = event.text.getStringStripFormatting();
    const words = message.split(' ');
    let flag_whisper = false;

    if (words.slice(1, 4).join(' ') === 'whispers to you:') {
        flag_whisper = words[0][0] !== '<';
    }

    if (words.slice(1, 4).join(' ') === 'joined the game') {
        Time.sleep(5000)
        Chat.say(`/voicechat invite ${words[0]}`)
    }

    if (words.slice(0, 3).join(' ') === 'You whisper to') {
        return; // I am whispering...
    }

    const client = Request.post("http://127.0.0.1:5000", message);
    const buf = client.text();
    if (buf !== 'empty' && flag_whisper) {
        if (words.slice(0, 4).join(' ') === uname + ' whispers to you:') {
            //Chat.toast('resp', buf);
        } else {
            Chat.say(`/msg ${words[0]} ${buf}`);
        }
    }
}

try {
    main();
} catch (error) {
    console.log(error);
}
