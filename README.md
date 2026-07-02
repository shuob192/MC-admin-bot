# mc-admin-bot

Discord bot for managing a Minecraft Java Edition server via RCON, with a FastAPI agent and role-based operator permissions.

## Architecture

```
Discord Bot 
    │
    │  HTTP (Tailscale)
    ▼
FastAPI Agent 
    │
    │  RCON (localhost)
    ▼
Minecraft Server 
```

The agent runs on the same machine as the Minecraft server and communicates via RCON locally. The Discord bot runs on a separate machine and reaches the agent over HTTP — via local IP if both machines are on the same LAN, or via Tailscale if they are on different networks.

## Prerequisites

- Minecraft Java Edition server with RCON enabled
- Python 3.8+ on the server machine, Python 3.10+ recommended on the bot machine
- A Discord application and bot token

## Networking

The Discord bot communicates with the FastAPI agent over HTTP. How to connect them depends on your setup:

| Setup | How to connect |
|---|---|
| Both machines on the same LAN | Set `AGENT_URL` to the agent machine's local IP (e.g. `http://192.168.1.10:8000`) |
| Machines on different networks | Use [Tailscale](https://tailscale.com/) and set `AGENT_URL` to the agent's Tailscale IP |

If you are running everything at home on the same router, **Tailscale is not required**.

## Setup

### 1. Minecraft server

`server.properties` is located in the root of your Minecraft server directory. Open it and set the following values:

```properties
enable-rcon=true
rcon.port=25575
rcon.password=your_rcon_password
```

> **Note:** `server.properties` is generated on first launch. If the file does not exist, start the server once to create it.

Then restart the server for the changes to take effect. You can verify RCON is working by connecting with any RCON client (e.g. `mcrcon`):

```bash
mcrcon -H localhost -P 25575 -p your_rcon_password "list"
```

### 2. Discord bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications) and create a new application
2. Under **Bot**, generate a token
3. Under **Privileged Gateway Intents**, enable **Message Content Intent**
4. Under **OAuth2 → URL Generator**, select scopes `bot` + `applications.commands` and invite the bot to your server
5. Create a `minecraft-sv` text channel and copy its ID
6. Create an `MC-Operator` role and assign it to server admins

### 3. Agent (server machine)

```bash
cd ~/MC_server_logbot
python3 -m venv .venv && source .venv/bin/activate
pip install -r agent/requirements.txt

cp agent/.env.example agent/.env
# Fill in RCON_PASSWORD and AGENT_API_KEY
nano agent/.env
```

Generate a random API key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Bot (any machine)

```bash
pip install -r bot/requirements.txt

cp bot/.env.example bot/.env
# Fill in DISCORD_TOKEN, AGENT_URL, AGENT_API_KEY, MINECRAFT_CHANNEL_ID
nano bot/.env
```

## Running

Start in this order:

```bash
# 1. Minecraft server
tmux new-session -s minecraft
java -Xmx4G -jar server.jar nogui

# 2. Agent (server machine)
tmux new-session -s mc-agent
source .venv/bin/activate
uvicorn main:app --app-dir agent --host 0.0.0.0 --port 8000

# 3. Bot
source .venv/bin/activate
cd bot && python main.py
```

## Commands

### Available to everyone

| Command | Description |
|---|---|
| `/mc keepinventory` | Check the current value of `keepinventory` |
| `/mc gamerule <rule>` | Check the value of any gamerule |
| `/mc status` | Check server status and online player count |

Typing "keep inventory" in the channel also triggers an automatic reply.

### MC-Operator only

| Command | Description |
|---|---|
| `/mcadmin gamerule <rule> <value>` | Change a gamerule |
| `/mcadmin op <player>` | Grant OP to a player |
| `/mcadmin deop <player>` | Revoke OP from a player |
| `/mcadmin whitelist_add <player>` | Add a player to the whitelist |
| `/mcadmin whitelist_remove <player>` | Remove a player from the whitelist |
| `/mcadmin rcon <command>` | Execute a raw RCON command |

## Testing

```bash
pip install -r tests/requirements.txt
pytest -v
```

Tests use a mock RCON server and do not require a running Minecraft server.
