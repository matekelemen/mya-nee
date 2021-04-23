# --- External Imports ---
import discord

# --- STL Imports ---
import importlib.util
import pathlib
import json
import sys

# --- Internal Imports ---
driverPath  = pathlib.Path(__file__).absolute() # full path to this file
rootPath    = driverPath.parent.parent.parent   # path to the local mya-nee repo
modulePath  = rootPath / "src/packages"         # path to directory containing the mya-nee python module

# Import pymyaa
moduleSpec  = importlib.util.spec_from_file_location( "pymyaa", str(modulePath / "pymyaa/__init__.py") )
Myaa        = importlib.util.module_from_spec( moduleSpec )

sys.modules[moduleSpec.name] = Myaa
moduleSpec.loader.exec_module( Myaa )


while True:

    # ------------------------------------------------
    # DISCORD CLIENT SETUP
    # ------------------------------------------------


    discordClient = discord.Client()
    globalStatus  = Myaa.GlobalStatus.GlobalStatus()

    @discordClient.event
    async def on_ready():
        await globalStatus.initialize( discordClient )


    @discordClient.event
    async def on_message( message: discord.Message ):
        await globalStatus.guilds[message.guild.id].onMessage( message )


    # ------------------------------------------------
    # RUN DISCORD CLIENT
    # ------------------------------------------------

    # Get bot token
    configuration = {}

    with open( rootPath / "config.json", "r" ) as configFile:
        configuration = json.load( configFile )

    token         = configuration["token"]

    # Run mya-nee
    discordClient.run( token )