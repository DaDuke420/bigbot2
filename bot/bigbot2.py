import datetime
import discord
import logging
import random
from discord.ext import commands, tasks
from . import daily_highs
from . import config

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
        #print("generating")
        #newsletter = newsletter.generate_newsletter()
        #await message.channel.send(":smile:")
        await message.channel.send("Just wait until tomorrow bro")
    command, _, args = message.content.partition(' ')
    args = args.split(' ')
    if command in command_list.keys():
        try:
            await command_list[command](args, message)
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


async def daily_high(args, message):
    """Get daily high for a boss.

    Usage:
      /dailyhigh <BossName> [PlayerName]

    If PlayerName is omitted, returns the highest daily high among
    `config.NEWSLETTER_MEMBERS`.
    """
    if not args or not args[0]:
        await message.channel.send("Usage: /dailyhigh <BossName> [PlayerName]")
        return

    boss = args[0]
    player = args[1] if len(args) > 1 and args[1] else None

    try:
        if player:
            val = daily_highs.get_player_daily_high_for_boss(player, boss)
            if val is None:
                await message.channel.send(f"No recorded daily high for {boss} for player {player}.")
            else:
                await message.channel.send(f"{player} highest one-day {boss} kc: {val}")
        else:
            top = daily_highs.get_highest_daily_high_among_members(boss)
            if top is None:
                await message.channel.send(f"No recorded daily high for {boss} among newsletter members.")
            else:
                top_player, top_val = top
                await message.channel.send(f"Highest one-day {boss} kc among newsletter members: {top_val} by {top_player}")
    except Exception as e:
        logger.info(f"Error in daily_high command: {e}")
        await message.channel.send("Error fetching daily high.")

command_list = {"/roll": roll, "/dailyhigh": daily_high}

client.run(TOKEN)