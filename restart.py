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

# ========== CONFIGURATION ==========
STATE_FILE = "restart_state.json"
CHECK_INTERVAL = 30  # seconds between checks

# ========== STATE MANAGEMENT ==========
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

# ========== BOT CLASS ==========
class RestartBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=".", self_bot=True)  # Prefix is now "."
        self.start_time = time.time()
        self.command_sent = False
        self.state = load_state()

    async def setup_hook(self):
        await self.register_commands()

    def register_commands(self):
        @self.command(name='save')
        async def save_cmd(ctx, *, command: str):
            """Save a command to re-execute after restart. .save .ab 123 1.8 beef"""
            self.state["command"] = command
            save_state(self.state)
            await ctx.send(f" Command saved: `{command}`")

        @self.command(name='id')
        async def save_id(ctx, user_id: int):
            """Save the target user ID. .id 123456789"""
            self.state["user_id"] = user_id
            save_state(self.state)
            await ctx.send(f" User ID saved: `{user_id}`")

        @self.command(name='status')
        async def show_status(ctx):
            """Show current saved state."""
            state = load_state()
            msg = f"** Restart Monitor Status:**\n"
            msg += f"Uptime: {int(time.time() - self.start_time)}s\n"
            msg += f"Saved Command: `{state.get('command', 'None')}`\n"
            msg += f"Target User: <@{state.get('user_id', 'None')}>"
            await ctx.send(msg)

        @self.command(name='clear')
        async def clear_state(ctx):
            """Clear saved command and user ID."""
            self.state = {}
            save_state(self.state)
            await ctx.send(" Cleared saved command and user ID.")

    async def on_ready(self):
        print(f" Restart Monitor online as {self.user}")
        print(f" Commands: .save <command> | .id <user_id> | .status | .clear")
        
        # Execute saved command on startup if not sent yet
        await self.execute_saved_command()
        
        # Start monitoring loop
        self.bot.loop.create_task(self.monitor_restart())

    async def execute_saved_command(self):
        """Execute the saved command once on startup."""
        if self.command_sent:
            return
        
        self.command_sent = True
        
        command = self.state.get("command")
        user_id = self.state.get("user_id")
        
        if not command or not user_id:
            print(" No command or user ID saved. Use .save and .id")
            return
        
        try:
            target_user = await self.fetch_user(user_id)
            if target_user:
                await target_user.send(command)
                print(f" Command executed: `{command}`")
            else:
                print(" Could not find target user.")
        except Exception as e:
            print(f" Failed to send command: {e}")

    async def monitor_restart(self):
        """Monitor for restarts and re-execute if needed."""
        await self.wait_until_ready()
        while True:
            await asyncio.sleep(CHECK_INTERVAL)
            
            current_uptime = int(time.time() - self.start_time)
            
            if current_uptime < 60 and not self.command_sent:
                print(" Restart detected Re-executing command...")
                await self.execute_saved_command()

# ========== RUN ==========
if __name__ == "__main__":
    bot = RestartBot()
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Error: {e}")
