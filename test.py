# --- External Imports ---
import pyrogram
import pytgcalls

# --- STL Imports ---
import pathlib
import json


chatID = -1001675049403
scriptDirectory = pathlib.Path(__file__).absolute().parent
with open(scriptDirectory / "config.json", 'r') as file:
    configuration = json.load(file)

client = pyrogram.Client(
    "mya-nee",
    configuration["telegramAPIID"],
    configuration["telegramAPIHash"]
)

voiceClient = pytgcalls.PyTgCalls(client)

async def main():
    await client.start()
    await voiceClient.start()
    await client.send_message(chatID, f"joining group call")
    await voiceClient.join_group_call(
        chatID,
        pytgcalls.types.AudioPiped(scriptDirectory / "data" / "audio" / "explosion.mp3")
    )
    await pytgcalls.idle()

client.run(main())