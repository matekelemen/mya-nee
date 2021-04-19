// --- External Imports ---
const Discord = require( "discord.js" )
const prefix = require( "../../config.json" )

module.exports = {

onMessage: function( message ) {

    // Do nothing if the message was sent by the bot
    if ( message.author.bot )
        return;

    // Do nothing if the message wasn't intended for mya-nee
    msg = message.content

    if ( !msg.startsWith(prefix) )
        return;
    else
        msg = msg.slice( prefix.length )
}

};