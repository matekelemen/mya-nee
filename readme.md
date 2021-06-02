## Short

Mya-nee is a magical discord bot that plays audio and posts images/gifs upon request.

Commands:
- mya-nee **echo** *string*: post *string* to the active text channel
- mya-nee **show** *partial_filename*: post a random image/gif whose file name contains *partial_filename* from *data/images* to the active text channel
- mya-nee **connect**: connect to the voice channel of the caller
- mya-nee **disconnect**: disconnect from the active voice channel
- mya-nee **play** *youtube_video_link / partial_file_name / '#'*: enqueue audio from a youtube link / local audio file either in *data/audio* or *data/downloads* / random local audio file subject to the 24-hour-rule
- mya-nee **skip**: skip the current audio track (its time stamp is not updated)
- mya-nee **next**: same as skip but the track's time stamp is updated
- mya-nee **stop**: stop playing audio (disable **radio** and empty the audio queue)
- mya-nee **radio**: play random local audio files until stopped
- mya-nee **status**: display the current audio status (current track, radio status, audio queue)
- mya-nee **list** *'commands' / 'queue' / data_dir_name*: list available commands / tracks in the audio queue / contents of a directory in *data*

When a command gets multiple arguments, it's executed separately with each. Example:
``` mya-nee play # # #``` queues three random audio files from *data/downloads*.

## Requirements

python 3.6+

Required python packages:
- [discord](https://pypi.org/project/discord.py/)
- [youtube_dl](https://pypi.org/project/youtube_dl/)

## Usage

Required discord permissions: ```Send Messages``` ```Connect``` ```Speak```.

After setting up the bot on your discord server (guild), run *src/drivers/mya-nee.py*.

On linux, you can also run *run.sh* that dumps the log to *mya-nee.log* and detaches the process from the shell (useful for an ssh connection).

(The bot is private for now because who knows what the situation is with ```youtube_dl```, but ask and you shall receive)

## Details

Most features of ```mya-nee``` are pretty trivial but handling audio needs a few clarifications. When ```mya-nee play some_youtube_video_link``` is executed, the audio is **downloaded and stored** is *data/downloads*. If you're wondering "*OMFG why not just stream the audio instead of downloading it?*", you're absolutely right, but you also clearly have no experience with German ISPs. Also, I'm running ```mya-nee``` from a raspberry whose WiFi receiver is not in top shape, so minimizing unnecessary throughput saves a lot of headaches. Consequently, downloading **new** audio files may interrupt the playback, as ```youtube_dl``` doesn't offer an asynchronous interface, and moving it to a subrocess is a hassle (I might do it in the near future tho). An extreme case of this *feature* is that, if the download takes long enough, ```mya-nee``` times out from discord and gets into a messed-up state. In this case ```mya-nee reboot``` can be used to reset the connection.

Some properties of local audio files (both in *data/downloads* and *data/audio*) are stored in json files that are regularly refreshed during execution. Most importantly, these properties include a time stamp that shows when a file was last played. This is used when queueing **random** audio files (either by ```mya-nee play #``` or ```mya-nee radio```): files that were played in the last 24 hours cannot be queued this way (though they can be queued by directly asking for them).
