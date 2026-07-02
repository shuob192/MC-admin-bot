import os
import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

OPERATOR_ROLE = os.getenv("OPERATOR_ROLE_NAME", "MC-Operator")


def is_mc_operator():
    async def predicate(interaction: discord.Interaction) -> bool:
        role = discord.utils.get(interaction.guild.roles, name=OPERATOR_ROLE)
        if role is None or role not in interaction.user.roles:
            raise app_commands.CheckFailure(
                f"This command requires the **{OPERATOR_ROLE}** role."
            )
        return True
    return app_commands.check(predicate)
