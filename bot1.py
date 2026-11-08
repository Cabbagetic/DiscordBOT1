#Cabbagetic Discord BOT1 and it is a Discord bot usually for the Cabbagetic Discord servers alongside with any other Discord servers of any Discord users with various purposes to provide enjoyment, fun, responsibilities and engagement for the users.
#Copyright (C) 2026  Esterajisi, Cabbagex55g and Cabbagetic (AKA Cabbagetic 2.0)
# 
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
import aiosqlite
import asyncio
import discord
import os
import sqlite3
import subprocess
import sys
import time
from datetime import timedelta
from discord.ext import commands, tasks
from dotenv import load_dotenv

#1. SETUP & STARTUP
load_dotenv()
start_time = time.time()
TRUSTED_USERS = [int(i) for i in os.getenv("TRUSTED_USERS", "").split(",") if i]

#This dynamically pulls prefix from .env and defaults to '!' if missing.
BOT_PREFIX = os.getenv("COMMAND_PREFIX", "!")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents, help_command=None)

#How fast the bot gets hungry (in seconds)
HUNGER_DECAY_INTERVAL = 1800

last_message_content = {}
last_author_id = {}


#--- 💾  DATABASE ASYNC HELPER FUNCTIONS 💾 ---

async def get_bot_status():
    """Fetches the bot's health, hunger, ghost status, and condition safely using aiosqlite."""
    async with aiosqlite.connect("bot_stats.db") as db:
        async with db.execute("SELECT health, hunger, is_ghost, status FROM bot_stats WHERE id = 1") as cursor:
            res = await cursor.fetchone()
            if res:
                return {
                    "health": res[0] if res[0] is not None else 100, 
                    "hunger": res[1] if res[1] is not None else 100, 
                    "is_ghost": res[2] if res[2] is not None else 0,
                    "status": res[3] if res[3] is not None else "normal"
                }
    return {"health": 100, "hunger": 100, "is_ghost": 0, "status": "normal"}

async def update_bot_status(hunger_level, health=None, is_ghost=None, status=None):
    """Updates the bot's database stats via aiosqlite AND changes its Discord status text."""
    if hunger_level is None:
        hunger_level = 100

    async with aiosqlite.connect("bot_stats.db") as db:
        async with db.execute("SELECT health, is_ghost, status FROM bot_stats WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if row:
                if health is None: health = row[0] if row[0] is not None else 100
                if is_ghost is None: is_ghost = row[1] if row[1] is not None else 0
                if status is None: status = row[2] if row[2] is not None else "normal"
            else:
                if health is None: health = 100
                if is_ghost is None: is_ghost = 0
                if status is None: status = "normal"

        await db.execute(
            "UPDATE bot_stats SET health=?, hunger=?, is_ghost=?, status=? WHERE id = 1", 
            (health, hunger_level, is_ghost, status)
        )
        await db.commit()

    if is_ghost == 1:
        status_text = f"Spooking the server... 👻 | {BOT_PREFIX}revive"
        activity_type = discord.ActivityType.playing
    elif status == "irradiated":
        status_text = f"⚠️ Glowing & Anxious! | {BOT_PREFIX}cure"
        activity_type = discord.ActivityType.playing
    elif status == "acidic_and_fatigued":
        status_text = f"🤢 Suffering from Acidity | {BOT_PREFIX}status"
        activity_type = discord.ActivityType.playing
    elif hunger_level > 80:
        status_text = f"Happy & Full! | {BOT_PREFIX}ping"
        activity_type = discord.ActivityType.playing
    elif hunger_level < 20:
        status_text = f"Starving... | {BOT_PREFIX}feed 🍕"
        activity_type = discord.ActivityType.playing
    else:
        status_text = f"for 'Hi' | {BOT_PREFIX}ping"
        activity_type = discord.ActivityType.watching

    await bot.change_presence(activity=discord.Activity(type=activity_type, name=status_text))

async def add_user_xp(user_id, guild_id, xp_to_add):
    """Grants XP to users dynamically using an async database loop, saving guild_id."""
    async with aiosqlite.connect("bot_stats.db") as db:
        async with db.execute("SELECT xp, level FROM user_xp WHERE user_id = ?", (user_id,)) as cursor:
            res = await cursor.fetchone()
        
        if not res:
            await db.execute(
                "INSERT INTO user_xp (user_id, guild_id, xp, level) VALUES (?, ?, ?, ?)", 
                (user_id, guild_id, xp_to_add, 1)
            )
            await db.commit()
            return False 
            
        current_xp = (res[0] if res[0] is not None else 0) + xp_to_add
        current_level = res[1] if res[1] is not None else 1
        
        xp_needed = current_level * 100
        leveled_up = False
        
        if current_xp >= xp_needed:
            current_xp -= xp_needed
            current_level += 1
            leveled_up = True
            
        await db.execute(
            "UPDATE user_xp SET xp = ?, level = ?, guild_id = ? WHERE user_id = ?", 
            (current_xp, current_level, guild_id, user_id)
        )
        await db.commit()
        return leveled_up


#--- ⚙️ STARTUP SYSTEM EVENTS ⚙️ ---

async def init_db():
    async with aiosqlite.connect("bot_stats.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_stats (
                id INTEGER PRIMARY KEY,
                health INTEGER DEFAULT 100,
                hunger INTEGER DEFAULT 100,
                is_ghost BOOLEAN DEFAULT 0,
                status TEXT DEFAULT 'normal'
            )
        """)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS server_config (
                guild_id INTEGER PRIMARY KEY,
                death_channel_id INTEGER
            )
        ''')
        cursor = await db.execute("SELECT count(*) FROM bot_stats")
        count = await cursor.fetchone()
        if count[0] == 0:
            await db.execute("INSERT INTO bot_stats (id, health, hunger, is_ghost, status) VALUES (1, 100, 100, 0, 'normal')")
        await db.commit()

@bot.event
async def on_ready():
    await init_db()
    
    async with aiosqlite.connect("bot_stats.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_xp (
                user_id INTEGER PRIMARY KEY, 
                guild_id INTEGER,
                xp INTEGER DEFAULT 0, 
                level INTEGER DEFAULT 1,
                status TEXT DEFAULT 'normal'
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS server_config (
                guild_id INTEGER PRIMARY KEY,
                death_channel_id INTEGER
            )
        ''')
        
        # Safely attempt schema alterations for existing DBs
        try:
            await db.execute("ALTER TABLE bot_stats ADD COLUMN is_ghost BOOLEAN DEFAULT 0")
        except aiosqlite.OperationalError:
            pass
            
        try:
            await db.execute("ALTER TABLE user_xp ADD COLUMN guild_id INTEGER")
        except aiosqlite.OperationalError:
            pass

        try:
            await db.execute("ALTER TABLE bot_stats ADD COLUMN status TEXT DEFAULT 'normal'")
        except aiosqlite.OperationalError:
            pass
            
            
        await db.commit()
    print("✨ Database schemas verified and updated automatically!")

    if not hunger_decay.is_running():
        hunger_decay.start()
    if not health_regen.is_running():
        health_regen.start()

    print("--------------------------------------------------")
    print("Cabbagetic Discord BOT1")
    print("Copyright (C) 2026 Esterajisi, Cabbagex55g and Cabbagetic (AKA Cabbagetic 2.0)")
    print("This program comes with ABSOLUTELY NO WARRANTY.")
    print("This is free software under the GNU GPLv3; you are")
    print("welcome to redistribute it under certain conditions.")
    print("--------------------------------------------------")
    print(f'✅ Logged in as {bot.user.name}. Everything is loaded and ready for action!')

    async with aiosqlite.connect("bot_stats.db") as db:
        async with db.execute("SELECT hunger, is_ghost FROM bot_stats WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if row:
                fallback_hunger = row[0] if row[0] is not None else 100
                fallback_ghost = row[1] if row[1] is not None else 0
                await update_bot_status(fallback_hunger, is_ghost=fallback_ghost)
            else:
                await update_bot_status(100, health=100, is_ghost=0)


#--- Background Task: Decay Hunger/Health and Health Regeneration ---
@tasks.loop(seconds=HUNGER_DECAY_INTERVAL)
async def hunger_decay():
    async with aiosqlite.connect("bot_stats.db") as db:
        async with db.execute("SELECT is_ghost, hunger, health FROM bot_stats WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if not row:
                return
            is_ghost, current_hunger, current_health = row[0], row[1], row[2]

            if is_ghost == 1:
                return

        new_hunger = max(0, current_hunger - 10)
        new_health = current_health

        if new_hunger < 20:
            new_health = max(0, new_health - 5)

        await db.execute("UPDATE bot_stats SET hunger = ?, health = ? WHERE id = 1", (new_hunger, new_health))
        await db.commit()

    await update_bot_status(new_hunger, health=new_health)
    
    if new_health <= 0 or new_hunger <= 0:
        await check_for_death()

async def check_for_death():
    stats = await get_bot_status()
    if stats["health"] <= 0 or stats["hunger"] <= 0:
        await update_bot_status(hunger_level=0, health=0, is_ghost=1)

        async with aiosqlite.connect("bot_stats.db") as db:
            async with db.execute("SELECT guild_id, death_channel_id FROM server_config") as cursor:
                configs = dict(await cursor.fetchall())

        for guild in bot.guilds:
            try:
                await guild.me.edit(nick=f"Ghost 👻 of {bot.user.name}")
                target_channel = None
                if guild.id in configs and configs[guild.id]:
                    target_channel = guild.get_channel(configs[guild.id])
                if not target_channel:
                    target_channel = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
                if target_channel:
                    embed = discord.Embed(
                        title="💔 THE BOT HAS DIED...",
                        description=f"The bot's health reached zero! Its body collapsed, and its soul has turned into a server ghost!\n\nUse `{BOT_PREFIX}revive` to perform a revival and bring it back to life!",
                        color=discord.Color.dark_red()
                    )
                    await target_channel.send(embed=embed)

            except Exception as e:
                print(f"Error handling death actions in guild {guild.id}: {e}")


@tasks.loop(seconds=450)
async def health_regen():
    async with aiosqlite.connect("bot_stats.db") as db:
        async with db.execute("SELECT is_ghost, hunger, health FROM bot_stats WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if not row:
                return
            is_ghost, current_hunger, current_health = row[0], row[1], row[2]
            
            if is_ghost == 1 or current_health >= 100:
                return
                
        if current_hunger >= 75:
            new_health = min(100, current_health + 6)
            await db.execute("UPDATE bot_stats SET health = ? WHERE id = 1", (new_health,))
            await db.commit()
            await update_bot_status(current_hunger, health=new_health)

#--- 💬 CENTRALIZED MESSAGE CONTROLLER 💬 ---

@bot.event
async def on_message(message):
    if message.author == bot.user or not message.guild:
        return

    stats = await get_bot_status()
    content = message.content.strip()

    # ❌ EMERGENCY GHOST WALL ❌
    if stats["is_ghost"]:
        if content.lower().startswith(f"{bot.command_prefix.lower()}revive"):
            await bot.process_commands(message)
        return

    # ⭐ ALIVE: RUN CONTEXT SYSTEM FEATURES ⭐
    did_level_up = await add_user_xp(message.author.id, message.guild.id, 5)
    if did_level_up:
        async with aiosqlite.connect("bot_stats.db") as db:
            async with db.execute("SELECT level FROM user_xp WHERE user_id = ?", (message.author.id,)) as cursor:
                row = await cursor.fetchone()
                new_lvl = row[0] if row else 1
        
        # SAFELY ATTEMPT TO SEND LEVEL UP MESSAGE
        try:
            await message.channel.send(f"🎉 Gg {message.author.mention}, you leveled up to **Level {new_lvl}**!")
        except discord.Forbidden:
            pass  # Silently ignore if bot lacks 'Send Messages' permission in this specific channel

    words = content.lower().split()
    channel_id = message.channel.id
    author_id = message.author.id
    target_words = ["hi", "bye"]
    found_word = next((w for w in target_words if w in words), None)

    if found_word:
        if message.author.bot:
            return

        if (last_message_content.get(channel_id) == found_word and
            last_author_id.get(channel_id) == author_id):
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            return

        try:
            await message.channel.send(found_word.capitalize())
            last_message_content[channel_id] = found_word
            last_author_id[channel_id] = author_id
        except discord.Forbidden:
            pass
    else:
        if not content.lower().startswith(bot.command_prefix.lower()):
            last_message_content[channel_id] = None
            last_author_id[channel_id] = None

    await bot.process_commands(message)


#--- 🧪 BOT COMMANDS 🧪 ---

@bot.command(name="ping", aliases=["Ping"])
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latency: {latency}ms')

@bot.command(name="uptime", aliases=["Uptime"])
async def uptime(ctx):
    uptime_seconds = int(round(time.time() - start_time))
    await ctx.send(f"🕒 **Uptime:** {str(timedelta(seconds=uptime_seconds))}")

@bot.command(name="purge", aliases=["Purge"])
async def purge(ctx, amount: int):
    if not (ctx.author.guild_permissions.administrator or ctx.author.id in TRUSTED_USERS):
        return await ctx.send("❌ You don't have permission!", delete_after=5)
    if amount > 50:
        return await ctx.send("⚠️ Limit is 50 per purge.", delete_after=5)
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'✅ Deleted {len(deleted)-1} messages.', delete_after=5)

@bot.command(name="status", aliases=["Status"])
async def status(ctx):
    stats = await get_bot_status()
    h = "❤️" if stats["health"] > 50 else "💔"
    f = "🍖" if stats["hunger"] > 50 else "🦴"

    condition_map = {
        "normal": "✨ Normal & Healthy",
        "irradiated": "☢️ Irradiated (Anxious & Abnormal)",
        "acidic_and_fatigued": "🤢 Acidic & Fatigued (Vomiting risk)"
    }
    current_condition = condition_map.get(stats["status"], stats["status"].capitalize())

    embed = discord.Embed(
        title="Bot Status & Conditions",
        color=discord.Color.green()
    )
    embed.add_field(
        name=f"{h} Health",
        value=f"{stats['health']}/100"
    )
    embed.add_field(
        name=f"{f} Hunger",
        value=f"{stats['hunger']}/100"
    )
    embed.add_field(
        name="Health & DNA Condition",
        value=current_condition,
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name="feed", aliases=["Feed"])
async def feed(ctx, item: str):
    stats = await get_bot_status()
    current_hunger = stats["hunger"]
    current_health = stats["health"]
    
    #Radioactivity and dangerous items
    radioactive_items = ["uranium", "glowing-sludge", "toxic-waste", "weird-rock", "plutonium", "thorium", "radium", "radon", "tritium"]
    is_radioactive = item.lower() in radioactive_items
    
    if is_radioactive:
        # Radiation & Abnormal Behavior trigger
        new_health = max(0, current_health - 30)
        await update_bot_status(hunger_level=current_hunger, health=new_health, status="irradiated", is_ghost=0)
        await ctx.send(f"☢️ Yikes! You fed the bot a **{item}**! It got severe **radiations**, developed **anxiety**, and is now acting with **abnormal behavior**!")
        return

    #Overfeeding
    if current_hunger >= 100:
        new_health = max(10, current_health - 5) if current_health > 20 else current_health
        await update_bot_status(hunger_level=50, health=new_health, status="acidic_and_fatigued", is_ghost=0)
        await ctx.send(f"🤢 Blech! The bot was already completely full! It choked down the {item}, immediately **vomited everywhere**, and now has severe **acidity** and **fatigue**!")
        return

    #Normal
    new_hunger = min(100, current_hunger + 20)
    if current_hunger > 80:
        new_health = min(100, current_health + 5)
    else:
        new_health = current_health

    await update_bot_status(hunger_level=new_hunger, health=new_health, status="normal", is_ghost=0)
    await ctx.send(f"You fed the bot a {item}! It feels much better :D")
    

@bot.command(name="restart", aliases=["Restart"])
async def restart(ctx):
    if ctx.author.id not in TRUSTED_USERS:
        return await ctx.send("❌ Only admins can restart the bot.")
    await ctx.send("🔄 Restarting... See you in 3 seconds!")
    await bot.close()
    os._exit(1)

@bot.command(name="stop", aliases=["Stop"])
async def stop(ctx):
    if ctx.author.id not in TRUSTED_USERS:
        return await ctx.send("❌ Only admins can restart the bot.")
    await ctx.send("📴 Shutdown Complete. See you later.")
    await bot.close()
    os._exit(0)

@bot.command(name="battery", aliases=["Battery"])
async def battery(ctx):
    try:
        result = subprocess.check_output(["/data/data/com.termux/files/usr/bin/termux-battery-status"])
        await ctx.send(f"```json\n{result.decode('utf-8')}\n```")
    except Exception as e:
        await ctx.send("❌ Failed to read battery info.")

@bot.command(name="revive", aliases=["Revive"])
async def revive(ctx):
    stats = await get_bot_status()
    if stats["is_ghost"] == 1:
        await update_bot_status(hunger_level=20, health=10, is_ghost=0)
        for guild in bot.guilds:
            try:
                await guild.me.edit(nick=bot.user.name) 
            except Exception as e:
                print(f"Couldn't change nickname in guild {guild.id}: {e}")
        await ctx.send("✨ **HEALED GLOBAL ACTION!** I have returned from the spirit world. My health is at 10💔 and my hunger is at 20🍗. Feed me quick!")
    else:
        await ctx.send(f"❤️ I'm still alive and kicking! Current Health: {stats['health']}")


#--- 📊 NEW LEVEL & LEADERBOARD SYSTEM COMMANDS 📊 ---

@bot.command(name="level", aliases=["Level"])
async def level(ctx, target: discord.Member = None):
    """Checks the user's current level and XP statistics."""
    user = target or ctx.author
    async with aiosqlite.connect("bot_stats.db") as db:
        async with db.execute("SELECT xp, level FROM user_xp WHERE user_id = ?", (user.id,)) as cursor:
            res = await cursor.fetchone()

    if not res:
        return await ctx.send(f"📊 **{user.display_name}** hasn't earned any XP yet! Start chatting to earn XP.")

    current_xp, current_level = res[0], res[1]
    xp_needed = current_level * 100

    embed = discord.Embed(
        title=f"📊 XP Profile - {user.display_name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(
        url=user.display_avatar.url
    )
    embed.add_field(
        name="⭐ Level",
        value=f"**{current_level}**",
        inline=True
    )
    embed.add_field(
        name="✨ Progress XP",
        value=f"`{current_xp} / {xp_needed} XP`",
        inline=True
    )
    await ctx.send(embed=embed)


@bot.command(name="sls", aliases=["Sls", "serverlevelstats", "ServerLevelstats"])
async def server_statusboard(ctx):
    """Displays the Top 10 users in the local server."""
    async with aiosqlite.connect("bot_stats.db") as db:
        async with db.execute(
            "SELECT user_id, level, xp FROM user_xp WHERE guild_id = ? ORDER BY level DESC, xp DESC LIMIT 10", 
            (ctx.guild.id,)
        ) as cursor:
            top_users = await cursor.fetchall()

    if not top_users:
        return await ctx.send("📉 No level stats available for this server yet!")

    embed = discord.Embed(
        title=f"🏆 Server Level Statusboard ({ctx.guild.name})", 
        color=discord.Color.gold()
    )
    description = ""

    for index, (user_id, lvl, xp) in enumerate(top_users, start=1):
        member = ctx.guild.get_member(user_id)
        name = member.display_name if member else f"User ID: {user_id}"
        description += f"**#{index}** • **{name}** — Level **{lvl}** (`{xp} XP`)\n"

    embed.description = description
    await ctx.send(embed=embed)


@bot.command(name="gls", aliases=["Gls", "globallevelstats", "GlobalLevelstats"])
async def global_statusboard(ctx):
    """Displays the Top 10 users globally across all servers."""
    async with aiosqlite.connect("bot_stats.db") as db:
        async with db.execute(
            "SELECT user_id, level, xp FROM user_xp ORDER BY level DESC, xp DESC LIMIT 10"
        ) as cursor:
            top_users = await cursor.fetchall()

    if not top_users:
        return await ctx.send("📉 No global level stats available yet!")

    embed = discord.Embed(title="🌍 Global Level Statusboard", color=discord.Color.purple())
    description = ""

    for index, (user_id, lvl, xp) in enumerate(top_users, start=1):
        user = bot.get_user(user_id)
        name = user.display_name if user else f"User ID: {user_id}"
        description += f"**#{index}** • **{name}** — Level **{lvl}** (`{xp} XP`)\n"

    embed.description = description
    await ctx.send(embed=embed)

@bot.command(name="setchannel", aliases=["Setchannel", "setdeathchannel"])
async def set_channel(ctx, channel: discord.TextChannel = None):
    """Sets the channel where death & ghost messages will be posted."""
    if not (ctx.author.guild_permissions.administrator or ctx.author.id in TRUSTED_USERS):
        return await ctx.send("❌ You need **Administrator** permissions to set the notification channel!")

    target_channel = channel or ctx.channel

    async with aiosqlite.connect("bot_stats.db") as db:
        await db.execute("""
            INSERT INTO server_config (guild_id, death_channel_id) 
            VALUES (?, ?) 
            ON CONFLICT(guild_id) DO UPDATE SET death_channel_id = excluded.death_channel_id
        """, (ctx.guild.id, target_channel.id))
        await db.commit()

    await ctx.send(f"📢 **Death Scene Notifications** set to {target_channel.mention}!")

@bot.command(name="help", aliases=["Help"])
async def help(ctx):
    embed = discord.Embed(
        title="🤖 Bot Command Menu",
        description="Here is everything I can do!",
        color=discord.Color.green()
    )
    embed.add_field(
        name="💬 Social & Leveling",
        value=f"• Say **Hi** or **Bye**\n• `{BOT_PREFIX}level`: View XP profile.\n• `{BOT_PREFIX}sls`: Server Level Statusboard.\n• `{BOT_PREFIX}gls`: Global Level Statusboard.",
        inline=False
    )
    embed.add_field(
        name="🍖 Pet System & Survival",
        value=f"• `{BOT_PREFIX}status`: Check health, hunger, and DNA conditions.\n• `{BOT_PREFIX}feed <food>`: Feed me (watch out for overfeeding and radioactive items!)\n• `{BOT_PREFIX}revive`: Break out of ghost mode 👻",
        inline=False
    )
    embed.add_field(
        name="🛠️ Utility & Server Management",
        value=f"• `{BOT_PREFIX}setchannel #channel`: Set custom death announcement channel.\n• `{BOT_PREFIX}ping`: Latency.\n• `{BOT_PREFIX}uptime`: Online length.\n• `{BOT_PREFIX}battery`: Host device status.\n• `{BOT_PREFIX}purge / {BOT_PREFIX}restart / {BOT_PREFIX}stop`: Admin commands.",
        inline=False
    )
    embed.set_footer(text="Requested by " + ctx.author.name)
    await ctx.send(embed=embed)

@bot.command(name="about", aliases=["About","Info","info","AboutTheBot","Aboutthebot","aboutthebot","aboutTheBot","aboutTheBOT","BOTINFO","BotInfo","botinfo"])
async def about(ctx):
    embed = discord.Embed(
        title="🤖 Cabbagetic Discord BOT1",
        description="A dedicated Discord bot usually for the Cabbagetic Discord servers alongside with any other Discord servers of any Discord users with various purposes to provide enjoyment, fun, responsibilities and engagement for the users. Feel free to add this APP to your Discord server(s) from its discord profile.",
        color=discord.Color.green()
    )
    embed.add_field(
        name="👥 Authors & Copyright", 
        value="Copyright (C) 2026 Esterajisi, Cabbagex55g and Cabbagetic (AKA Cabbagetic 2.0)", 
        inline=False
    )
    embed.add_field(
        name="📜 Open Source License", 
        value="This program is free software protected under the **GNU GPLv3 License**. "
              "It comes with absolutely no warranty. You are free to view, modify, "
              "and redistribute its source code under the terms of the GPLv3.", 
        inline=False
    )
    embed.add_field(
        name="📖 Source Code",
        value="[Available on GitHub ↗️](https://github.com/Cabbagetic/DiscordBOT1)",
        inline=False
    )
    await ctx.send(embed=embed)

# 4. RUN
bot.run(os.getenv('DISCORD_TOKEN'))
                
