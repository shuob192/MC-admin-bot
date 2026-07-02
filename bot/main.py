import os
import re
import sys
import logging

import discord
from discord import app_commands
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))

import agent_client
from agent_client import AgentError
from commands.query import QueryCommands
from commands.admin import AdminCommands

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DISCORD_TOKEN        = os.getenv("DISCORD_TOKEN", "")
MINECRAFT_CHANNEL_ID = int(os.getenv("MINECRAFT_CHANNEL_ID", "0"))

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set")

_KEEPINVENTORY_RE = re.compile(r"keep[\s_-]?inventory", re.IGNORECASE)


class MinecraftBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.add_command(QueryCommands())
        self.tree.add_command(AdminCommands())
        await self.tree.sync()
        logging.info("Slash commands synced")

    async def on_interaction(self, interaction: discord.Interaction):
        await self.tree.process_application_commands(interaction)

    async def on_ready(self):
        logging.info("Logged in as %s (id=%d)", self.user, self.user.id)

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ):
        msg = str(error) if isinstance(error, app_commands.CheckFailure) else f"Error: {error}"
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception:
            logging.exception("Failed to send error response")
        if not isinstance(error, app_commands.CheckFailure):
            logging.exception("Unhandled app command error", exc_info=error)

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if MINECRAFT_CHANNEL_ID and message.channel.id != MINECRAFT_CHANNEL_ID:
            return

        if _KEEPINVENTORY_RE.search(message.content):
            try:
                raw = await agent_client.execute_rcon("gamerule keep_inventory")
                value = raw.split(":")[-1].strip() if ":" in raw else raw
                await message.reply(f"keep_inventory = **{value}**")
            except AgentError as e:
                await message.reply(f"Error: {e}")


bot = MinecraftBot()
bot.run(DISCORD_TOKEN)
