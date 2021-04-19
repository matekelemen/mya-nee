// --- External Imports ---
const Discord = require("discord.js");
const { prefix, token } = require("../../config.json");
const ytdl = require("ytdl-core");

// ---------------------------------------------------------------------
// GLOBALS
// ---------------------------------------------------------------------

const client = new Discord.Client();

const queue = new Map();

// ---------------------------------------------------------------------
// CLASS DEFINITIONS
// ---------------------------------------------------------------------

// ---------------------------------------------------------------------
// STATUS LOG
// ---------------------------------------------------------------------

client.once("ready", () => {
  console.log("Ready!");
});

client.once("reconnecting", () => {
  console.log("Reconnecting!");
});

client.once("disconnect", () => {
  console.log("Disconnect!");
});

// ---------------------------------------------------------------------
// EVENTS
// ---------------------------------------------------------------------

client.on("message", async message => {
  
    // Do nothing if the message was sent by the bot
    if ( message.author.bot )
        return;

    // Do nothing if the message wasn't intended for mya-nee
    msg = message.content;

    if ( !msg.startsWith(prefix) )
        return;
    else
        msg = msg.slice( prefix.length );

    while ( msg.startsWith(' ') )
    {
        msg = msg.slice(1);
    }

    // Split message by spaces:
    //  - first: command
    //  - the rest: arguments
    msg = msg.split( " " );
    command = msg[0];
    args = msg.slice( 1 );

  const serverQueue = queue.get(message.guild.id);

    if ( command === "play" )
    {
        execute( message, args, serverQueue );
        message.delete();
        return;
    }
    
    else if ( command === "skip" )
    {
        skip( message, args, serverQueue );
        return;
    }
    
    else if ( command === "stop" )
    {
        stop( message, args, serverQueue );
        return;
    }

    else if ( command == "connect" )
    {
        message.channel.send( "Kon'nichiwa Senpai!" );
        connectServer( message );
        return;
    }

    else if ( command == "disconnect" )
    {
        message.channel.send( "Sayonara Senpai!" );
        disconnectServer( message );
        return;
    }
    
    else
    {
        message.channel.send( "Wakarimasen! >.<" );
        return;
    }
});

// ---------------------------------------------------------------------
// CALLBACKS
// ---------------------------------------------------------------------

async function execute( message, args, serverQueue ) 
{
    // Get youtube link info
    // TODO: check whether it really is a youtube link
    const songInfo = await ytdl.getInfo(args[0]);
    const song = {
        title: songInfo.videoDetails.title,
        url: songInfo.videoDetails.video_url,
    };

    if ( !serverQueue )
    {
        message.channel.send( "Senpaaai, I must connect to the channel first 😑" )
        return;
    }

    serverQueue.songs.push(song);

    if ( serverQueue.songs.length == 1 )
    { play(message.guild, serverQueue.songs[0]); }
    else
    { message.channel.send(`Enqueue ${song.title}`); }
}

function skip( message, args, serverQueue ) {
  if (!message.member.voice.channel)
    return message.channel.send(
        "Senpaaaai, I can't skip media on a text channel >.<'"
    );
  if (!serverQueue)
    return message.channel.send("There is no song that I could skip!");
  serverQueue.connection.dispatcher.end();
}

function stop( message, args, serverQueue ) {
  if (!message.member.voice.channel)
    return message.channel.send(
        "Senpaaaai, I can't stop media on a text channel >.<'"
    );
    
  if (!serverQueue)
    return message.channel.send("There is no song that I could stop!");
    
  serverQueue.songs = [];
  serverQueue.connection.dispatcher.end();
}

function play(guild, song)
{
    const serverQueue = queue.get(guild.id);
    if ( !song )
    { return; }

    const dispatcher = serverQueue.connection
        .play( ytdl(song.url) )
        .on("finish", () => {
            serverQueue.songs.shift();
            play(guild, serverQueue.songs[0]);
        })
        .on("error", error => console.error( error ));
    dispatcher.setVolumeLogarithmic(serverQueue.volume / 5);
    serverQueue.textChannel.send(`Now playing: **${song.title}**`);
}


function disconnectServer( message )
{
    const serverQueue = queue.get( message.guild.id )
    serverQueue.voiceChannel.leave()
    queue.delete( message.guild.id )
}


async function connectServer( message )
{
    const voiceChannel = message.member.voice.channel;
    if (!voiceChannel)
        return message.channel.send(
        "Senpaaaai, I can't play media on a text channel >.<'"
        );

    // Check permissions to join channel and broadcast audio on it
    const permissions = voiceChannel.permissionsFor(message.client.user);

    if ( !permissions.has( "CONNECT" ) )
    {
        message.channel.send( "Senpai, I don't have permission to join your channel 😭" );
        return;
    }

    if ( !permissions.has( "SPEAK" ) )
    {
        message.channel.send( "Senpai, I don't have permission to speak on your channel 😭" )
        return;
    }

    const queueContruct = {
        textChannel: message.channel,
        voiceChannel: voiceChannel,
        connection: null,
        songs: [],
        volume: 5,
        playing: true
    };

    queue.set( message.guild.id, queueContruct );

    try
    {
        var connection = await voiceChannel.join();
        queueContruct.connection = connection;
    }
    catch ( error )
    {
        console.log( error );
        queue.delete(message.guild.id);
        return message.channel.send( error );
    }
}


client.login(token);