# restart.py - FIXED VERSION
import discord
from discord.ext import commands
import asyncio
import json
import os
import time

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print(" Please set the TOKEN environment variable.")
    exit(1)

STATE_FILE = "data/restart_state.json"
CHECK_INTERVAL = 30

def load_state():
    try:
        if not os.path.exists(STATE_FILE):
            with open(STATE_FILE, "w") as f:
                json.dump({}, f)
            return {}
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

class RestartBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=".", self_bot=True)
        self.start_time = time.time()
        self.command_sent = False
        self.state = load_state()

    async def setup_hook(self):
        self.register_commands()

    def register_commands(self):
        @self.command(name='save')
        async def save_cmd(ctx, *, command: str):
            self.state["command"] = command
            save_state(self.state)
            await ctx.send(f" Command saved: `{command}`")

        @self.command(name='channel')
        async def save_channel(ctx, channel_id: int):
            self.state["channel_id"] = channel_id
            save_state(self.state)
            await ctx.send(f" Channel ID saved: `{channel_id}`")

        @self.command(name='status')
        async def show_status(ctx):
            state = load_state()
            msg = f"** Restart Monitor Status:**\n"
            msg += f"Uptime: {int(time.time() - self.start_time)}s\n"
            msg += f"Saved Command: `{state.get('command', 'None')}`\n"
            msg += f"Target ch_id: <@{state.get('channel_id', 'None')}>"
            await ctx.send(msg)

        @self.command(name='clear')
        async def clear_state(ctx):
            self.state = {}
            save_state(self.state)
            await ctx.send(" Cleared saved command and user ID.")

    async def on_ready(self):
        print(f" Restart Monitor online as {self.user}")
        print(f" Commands: .save <command> | .id <user_id> | .status | .clear")
        
        await asyncio.sleep(5)
        await self.execute_saved_command()
        self.loop.create_task(self.monitor_restart())

    async def execute_saved_command(self):
        if self.command_sent:
            return
        self.command_sent = True
        
        command = self.state.get("command")
        user_id = self.state.get("user_id")
        channel_id = self.state.get("channel_id")
        
        if not command:
            print(" No command saved. Use .save")
            return
        
        # Try channel first, then user
        if channel_id:
            channel = self.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(command)
                    print(f" Command sent to channel: `{command}`")
                    return
                except Exception as e:
                    print(f" Failed to send to channel: {e}")
        
        if user_id:
            try:
                target_user = await self.fetch_user(user_id)
                if target_user:
                    await target_user.send(command)
                    print(f" Command sent to DM: `{command}`")
                    return
            except discord.errors.Forbidden as e:
                print(f" Forbidden: {e}")
            except Exception as e:
                print(f" Failed to send to DM: {e}")
        
        print(" No valid target (channel or user) found")
        
    async def monitor_restart(self):
        await self.wait_until_ready()
        while True:
            await asyncio.sleep(CHECK_INTERVAL)
            current_uptime = int(time.time() - self.start_time)
            if current_uptime < 60 and not self.command_sent:
                print(" Restart detected! Re-executing command...")
                await self.execute_saved_command()

# ========== RUN WITH DELAY ==========
if __name__ == "__main__":
    bot = RestartBot()
    
    print("⏳ Waiting 30 seconds before connecting...")
    time.sleep(30)  #  CRITICAL: Wait 30 seconds before login
    
    while True:
        try:
            bot.run(TOKEN)
            break
        except discord.errors.HTTPException as e:
            if e.status == 429:
                print(" Rate limited. Waiting 60 seconds...")
                time.sleep(60)
                continue
            print(f" Error: {e}")
            break
        except Exception as e:
            print(f" Error: {e}")
            break
