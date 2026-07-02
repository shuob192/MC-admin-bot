import logging
import discord
from discord import app_commands

import agent_client
from agent_client import AgentError

logger = logging.getLogger(__name__)


def _extract_gamerule_value(raw: str) -> str:
    """'Game rule keep_inventory is currently set to: true' → 'true'"""
    return raw.split(":")[-1].strip() if ":" in raw else raw


class QueryCommands(app_commands.Group):
    """Read-only server info commands, available to everyone."""

    def __init__(self):
        super().__init__(name="mc", description="Minecraft server info")

    @app_commands.command(name="keepinventory", description="Check the current value of keep_inventory")
    async def keepinventory(self, interaction: discord.Interaction):
        logger.info("keepinventory called by %s", interaction.user)
        await interaction.response.defer()
        logger.info("deferred")
        try:
            raw = await agent_client.execute_rcon("gamerule keep_inventory")
            logger.info("rcon result: %s", raw)
            value = _extract_gamerule_value(raw)
            await interaction.followup.send(f"keep_inventory = **{value}**")
        except AgentError as e:
            logger.error("AgentError: %s", e)
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
        except Exception as e:
            logger.exception("Unexpected error in keepinventory")
            await interaction.followup.send(f"Unexpected error: {e}", ephemeral=True)

    @app_commands.command(name="gamerule", description="Check the value of any gamerule")
    @app_commands.describe(rule="Gamerule name (e.g. keep_inventory)")
    async def gamerule(self, interaction: discord.Interaction, rule: str):
        await interaction.response.defer()
        try:
            raw = await agent_client.execute_rcon(f"gamerule {rule}")
            await interaction.followup.send(f"`{rule}` → **{_extract_gamerule_value(raw)}**")
        except AgentError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)

    @app_commands.command(name="status", description="Check server status and online player count")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await agent_client.get_status()
        if data["online"]:
            await interaction.followup.send(f"Server: **Online**\n{data['detail']}")
        else:
            await interaction.followup.send(f"Server: **Offline**\n{data['detail']}")
