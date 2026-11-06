## BOT1 (Virtual Pet & Utility Suite)
A feature-rich Discord pet and utility bot built with Python and discord.py, natively optimized for 24/7 operation inside Termux on Android devices.

## ✨ Key Features

- **🍖 Advanced Virtual Pet Engine:** The bot lives right in your server! It experiences continuous hunger decay and takes physical health damage if left starving.
- **👻 Ghost State & Emergency Wall:** If health or hunger drops to zero, the bot transitions into a Ghost state. Its nickname changes, its presence alters, and it activates an emergency command wall that blocks all functionality except for a spiritual revival.
- **⭐ Automated XP Tracking:** Active chatters earn 5 XP per message. Features integrated mathematical calculations to handle level-ups seamlessly with real-time level confirmations directly back to the channel.
- **📈 Rich Embed Formatting For XP Profile & Level Status Boards:** The XP profile and level status boards render cleanly in Discord embeds with gold/purple accents, ranking numbers (`#1`, `#2`, `#3`).
- **📊 Thread-Safe Persistent Database:** Built with asynchronous `aiosqlite` schema layers to securely handle server actions without causing database locks or halting runtime functions.
- **💬 Intelligent Social Filtration:** Automatically responds to greetings like "Hi" and "Bye" for human members, blocks recursive bot-to-bot greeting loops, and auto-purges rapid-fire user message duplication.
- **🛠️ Dynamic Prefix Environment Configuration:** Programmed to automatically pick up configuration traits from your environment `.env` file. Supports cross-case functionality seamlessly for lowercase/uppercase parsing matching standard styles natively.
- **🔄 Fault-Tolerant Auto-Restart Loop:** Accompanied by a dedicated bash shell supervisor to auto-heal runtime loops or perform rapid core restarts upon administrative command calls.

---

## 🛠️ Installation & Setup Instructions

### 1. Prerequisites (Termux setup)
Update your platform and install Python alongside dependencies tailored for database execution:
```bash
pkg update && pkg upgrade
pkg install python
pip install discord.py python-dotenv aiosqlite
```

### 2. Configuration (`.env`)
Create an environment variable configuration file to store your credentials securely:
```bash
nano .env
```

Paste the configuration grid and adjust variables according to your active environment:
```txt
DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
TRUSTED_USERS=YOUR_USER_ID, ANOTHER_USER_ID
COMMAND_PREFIX=!
```

**Tip:** _To save files modified using nano, press_ `Ctrl + X`, _press_ `Y` _and confirm with_ `Enter`_._

### 3. Creating the Auto-Restart Script (`start.sh`)
This bash wrapper acts as a supervisor to keep your execution environment running seamlessly.
1. Create the runtime file:
```bash
nano start.sh
```
2. Insert the following operational control structure (ensure your main file matches the specified runtime name, e.g. `bot1.py`):
```bash
#!/bin/bash
while true
do
    echo "Starting Bot Execution Flow..."
    python bot1.py
    status=$?
    if [ $status -eq 0 ]; then
        echo "✅ Bot stopped manually via exit code 0. Goodbye!"
        break
    else
        echo "🔄 Runtime crashed or triggered restart. Re-spinning in 3 seconds..."
        sleep 3
    fi
done
```

**Tip:** _To save files modified using nano, press_ `Ctrl + X`, _press_ `Y` _and confirm with_ `Enter`_._

3. Inject executable context permissions into your shell wrapper before starting:
```bash
chmod +x start.sh
```

## 🚀 Deployment Execution
Instead of calling the Python runtime engine directly, pass terminal controls to the auto-supervisor layer:
```bash
./start.sh
```

## 🎮 Command Index
All commands naturally adhere to your specified context variables configured inside the .env container file (e.g. !command).

Command         →        Description

---
`help`           →       Renders a clean menu detailing active systems, variables, and categories.

---
`revive`         →       Restores life structures if the pet enters a ghost state.

---
`status`         →       Checks structural parameters including health and hunger metrics.

---
`feed [food]`    →       Satisfies hunger metrics and incrementally restores health metrics.

---
`level`          →       Displays users' current Level, total XP, and remaining XP needed for the next level. You can also mention someone (e.g., !level @User) to check their stats!

---
`sls`/`serverlevelstats`     →       Displays the top 10 highest-level users _only_ in the server where the command is typed.

---
`gls`/`globallevelstats` → Displays the top 10 highest-level users across _all_ servers the bot resides in.

---
`uptime`         →       Tracks processing metrics down to hours/minutes/seconds.

---
`ping`           →       Pulls latency intervals from the API gateway engine.

---
`purge [amount]` →       Cleans channel backlogs instantly up to a 50-message cap.

---
`battery`        →       Interfaces with `/usr/bin/termux-battery-status` for local host info.

---
`restart`        →       Safely cuts thread connections and flags the shell script to reboot.

---
`stop`           →       Safely drops active connection points and completely shuts down loops.

---

**🔋 Note on Battery Command:** Requires both cli, the native terminal package, (`pkg install termux-api`) and the corresponding Termux:API system app to be cleanly installed on the target device.
**Example:** _if you have installed you current_ [Termux App](https://github.com/termux/termux-app/releases/latest) _from the official Termux GitHub, you should have installed the_ [Termux:API](https://github.com/termux/termux-api/releases/latest) _App from their official GitHub as well._

## 📝 Roadmap & Completed Tasks
- [x] Integrate safe background thread management via asynchronous tasks.
- [x] Prevent bot-to-bot conversational loops and user spam strings.
- [x] Inject low-level architecture modules to evaluate Termux system properties.
- [x] Construct dynamic table queries using a thread-safe persistent SQL database layout.
- [x] Build out specialized state transitions handling structural damage and fatal pet death cycles.
- [x] Build an Emergency Ghost isolation shield blocking standard interactive command runs.
- [x] Program spiritual retrieval mechanics (`revive`) updating active roles and nicknames on-the-fly.
- [x] Implement mathematical XP progression tracking and persistent text rank mechanics.
- [ ] Implement integrated inventory items and an analytical economy structure.
- [x] Implement `Level`, `ServerLevelstats` (`sls`/`Sls`), `GlobalLevelstats` (`gls`/`Gls`)
- [x] Add issues while Overfeeding (such as vomiting, acidity, fatigue, radiations, slow behaviour, sleepy, inactive even though online, anxiety, abnormal behaviour)
