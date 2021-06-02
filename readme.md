## Short

Mya-nee is a magical discord bot that plays audio and posts images/gifs upon request.

Commands:
- mya-nee **echo** *string*: post *string* to the active text channel
- mya-nee **show** *partial_filename*: post a random image/gif whose file name contains *partial filename* from *data/images* to the active text channel
- mya-nee **connect**: connect to the voice channel of the caller
- mya-nee **disconnect**: disconnect from the active voice channel (automatically called if mya-nee is the last in the channel)
- mya-nee **play** *youtube_video_link / partial_file_name / #*: enqueue audio from a youtube link / local audio file either in *data/audio* or *data/downloads* / random local audio file subject to the 24-hour-rule
- mya-nee **skip**: skip the current audio track (its time stamp is not updated)
- mya-nee **next**: same as skip but the track's time stamp is updated
- mya-nee **stop**: stop playing audio (disable **radio** and empty the audio queue)
- mya-nee **radio**: play random local audio files until stopped
- mya-nee **status**: display the current audio status (current track, radio status, audio queue)
- mya-nee **list** *'commands' / 'queue' / data_dir_name*: list available commands / tracks in the audio queue / contents of a directory in *data*

## Requirements

python 3.6+

Required python packages:
- [discord](https://pypi.org/project/discord.py/)
- [youtube_dl](https://pypi.org/project/youtube_dl/)

## Usage

equired discord permissions: ```Send Messages``` ```Connect``` ```Speak```.

After setting up the bot on your discord server (guild), run *src/drivers/mya-nee.py*.

On linux, you can also run *run.sh* that dumps the log to *mya-nee.log* and detached the process from the shell (useful for an ssh connection).

(The bot is private for now because who knows what the situation is with ```youtube_dl```, but ask and you shall receive)
