import discord
from discord import app_commands

import agent_client
from agent_client import AgentError
from checks import is_mc_operator


class AdminCommands(app_commands.Group):
    """Admin commands, restricted to MC-Operator role."""

    def __init__(self):
        super().__init__(name="mcadmin", description="Minecraft server admin (MC-Operator only)")

    @app_commands.command(name="gamerule", description="Change a gamerule")
    @app_commands.describe(rule="Gamerule name", value="Value to set (true/false or integer)")
    @is_mc_operator()
    async def gamerule(self, interaction: discord.Interaction, rule: str, value: str):
        await interaction.response.defer()
        try:
            result = await agent_client.execute_rcon(f"gamerule {rule} {value}")
            await interaction.followup.send(f"`gamerule {rule} {value}` → {result}")
        except AgentError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)

    @app_commands.command(name="op", description="Grant OP to a player")
    @app_commands.describe(player="Player name")
    @is_mc_operator()
    async def op(self, interaction: discord.Interaction, player: str):
        await interaction.response.defer()
        try:
            result = await agent_client.execute_rcon(f"op {player}")
            await interaction.followup.send(result)
        except AgentError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)

    @app_commands.command(name="deop", description="Revoke OP from a player")
    @app_commands.describe(player="Player name")
    @is_mc_operator()
    async def deop(self, interaction: discord.Interaction, player: str):
        await interaction.response.defer()
        try:
            result = await agent_client.execute_rcon(f"deop {player}")
            await interaction.followup.send(result)
        except AgentError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)

    @app_commands.command(name="whitelist_add", description="Add a player to the whitelist")
    @app_commands.describe(player="Player name")
    @is_mc_operator()
    async def whitelist_add(self, interaction: discord.Interaction, player: str):
        await interaction.response.defer()
        try:
            result = await agent_client.execute_rcon(f"whitelist add {player}")
            await interaction.followup.send(result)
        except AgentError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)

    @app_commands.command(name="whitelist_remove", description="Remove a player from the whitelist")
    @app_commands.describe(player="Player name")
    @is_mc_operator()
    async def whitelist_remove(self, interaction: discord.Interaction, player: str):
        await interaction.response.defer()
        try:
            result = await agent_client.execute_rcon(f"whitelist remove {player}")
            await interaction.followup.send(result)
        except AgentError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)

    @app_commands.command(name="rcon", description="Execute a raw RCON command")
    @app_commands.describe(command="Command to run (no leading / needed)")
    @is_mc_operator()
    async def rcon(self, interaction: discord.Interaction, command: str):
        await interaction.response.defer()
        try:
            result = await agent_client.execute_rcon(command)
            await interaction.followup.send(f"```\n{result or '(no response)'}\n```")
        except AgentError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
