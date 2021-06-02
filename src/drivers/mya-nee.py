# --- External Imports ---
import discord

# --- STL Imports ---
import importlib.util
import asyncio
import pathlib
import json
import sys

# --- Internal Imports ---
driverPath  = pathlib.Path(__file__).absolute() # full path to this file
rootPath    = driverPath.parent.parent.parent   # path to the local mya-nee repo
modulePath  = rootPath / "src/packages"         # path to directory containing the mya-nee python module

# Import pymyaa
moduleSpec  = importlib.util.spec_from_file_location( "myanee", str(modulePath / "myanee/__init__.py") )
myanee      = importlib.util.module_from_spec( moduleSpec )

sys.modules[moduleSpec.name] = myanee
moduleSpec.loader.exec_module( myanee )



while True:

    # Discord client setup
    configuration = {}
    with open( rootPath / "config.json", 'r' ) as configFile:
        configuration = json.load( configFile )

    discordClient = discord.Client()
    root          = myanee.MyaNee.MyaNee()

    @discordClient.event
    async def on_ready():
        await root.initialize( discordClient, configuration["prefix"] )

    @discordClient.event
    async def on_message( message: discord.Message ):
        await root.onMessage( message )

    @discordClient.event
    async def on_voice_state_update( member: discord.Member, before: discord.VoiceState, after: discord.VoiceState ):
        if before.channel != None and after.channel == None:
            await root.onChannelLeave( before.channel, member )

        elif before.channel == None and after.channel != None:
            await root.onChannelJoin( after.channel, member )

    # Run
    root.log( "run" )
    discordClient.run( configuration["token"] )
    root.log( "stop" )

    root.release()

    # Decide what to do after stopping
    if root.status == "rebooting": # restart the event loop and redefine everything
        asyncio.set_event_loop( asyncio.new_event_loop() )
    else: # terminate
        root.log( "terminate" )
        break