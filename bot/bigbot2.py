import datetime
import discord
import logging
import random
from discord.ext import commands, tasks

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

with open("discord_token.txt", "r") as f:
    TOKEN = f.read().strip()

intents = discord.Intents.default()
intents.message_content = True # Required to read message content
bot = commands.Bot(command_prefix='!', intents=intents)

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    send_weekday_newsletter.start()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == "Bigbot, send a newsletter.":
        print("generating")
        newsletter = newsletter.generate_newsletter()
        await message.channel.send(":smile:")
        #await message.channel.send("Just wait until tomorrow bro")
    command, _, args = message.content.partition(' ')
    args = args.split(' ')
    if command in commands.keys():
        try:
            await commands[command](args, message)
        except Exception as e:
            logger.info(f"Error: {e}")
        

@tasks.loop(time=datetime.time(hour=14, minute=30))
async def send_weekday_newsletter():
    channel = client.get_channel(1164207289553662064)
    if channel:
        print("generating")
        newsletter = newsletter.generate_newsletter()
        if len(newsletter) > 2000:
            await channel.send("Woah there! This is a long newsletter! I'll break it up a bit.")
            newsletters = newsletter.split("\n\n")
            for letter in newsletters:
                await channel.send(letter)
        else:
            await channel.send(newsletter)

# The args passed should be only the max roll
async def roll(args, message):
    max_roll = 6
    if args:
        max_roll = int(args[0])
    roll = random.randint(1, max_roll)
    await message.channel.send(str(roll))

commands = {"/roll": roll}

client.run(TOKEN)