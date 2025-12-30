# RCS Quick Start Guide

Complete RCS messaging infrastructure for Wolf Ai Enterprises.

## What You Got

1. **Command Line Client** - Send RCS from terminal
2. **Webhook Listener** - Receive RCS messages
3. **AI Auto-Responder** - AI answers your messages automatically
4. **PostgreSQL Integration** - Full conversation history
5. **Docker Ready** - Production deployment

## Setup (5 Minutes)

### Step 1: Get Melrose Labs Credentials

1. Sign up: https://rcs.melroselabs.com
   - Organization: **Wolf Ai Enterprises**
   - Get: `client_id`, `client_secret`, `bot_id`

### Step 2: Configure RCS Client

```bash
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/messaging
source ~/anaconda3/bin/activate messiah

python rcs_client.py setup \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET \
  --bot-id YOUR_BOT_ID
```

### Step 3: Test Sending

```bash
python rcs_client.py send \
  --phone +12345678900 \
  --message "First RCS from Wolf Ai Enterprises"
```

### Step 4: Start Webhook Listener

```bash
docker compose -f docker-compose.rcs.yml up -d
```

### Step 5: Add to Caddyfile

Add this block to `/etc/caddy/Caddyfile`:

```
https://rcs.complexsimplicityai.com {
	import custom_wildcard_tls
	import security_headers
	reverse_proxy http://100.110.82.181:9090
}
```

Then reload Caddy:
```bash
sudo systemctl reload caddy
```

### Step 6: Configure Melrose Labs Webhooks

In RCS portal, set:
- **Inbound:** `https://rcs.complexsimplicityai.com/webhook/rcs/inbound`
- **Status:** `https://rcs.complexsimplicityai.com/webhook/rcs/status`

## Usage

### Send Message
```bash
python rcs_client.py send --phone +1234567890 --message "Hello"
```

### Check Message Status
```bash
python rcs_client.py status --msg-id <message_id>
```

### View Conversation
```bash
curl http://localhost:9090/api/rcs/conversations/+1234567890
```

### Start AI Auto-Responder
```bash
python rcs_auto_responder.py
```

## What's Next

Once tested:
1. Deploy to production (already Docker-ready)
2. Integrate with your AI models for smart responses
3. Add to patent documentation
4. Scale to multiple bots

## Files

- `rcs_client.py` - Command line client
- `rcs_webhook.py` - Webhook listener (receives messages)
- `rcs_auto_responder.py` - AI auto-responder
- `docker-compose.rcs.yml` - Docker deployment
- `Dockerfile.rcs` - Container definition

## Database

All messages stored in `wolf_logic.rcs_messages`:
```sql
SELECT * FROM rcs_messages ORDER BY created_at DESC LIMIT 10;
```

## Architecture

```
You (CLI) ──────────────┐
                        ├──> Melrose Labs RCS ──> Mobile Devices
Melrose Labs RCS ───────┘
        │
        ├──> Webhook (rcs.complexsimplicityai.com)
        │         │
        │         └──> PostgreSQL (conversation log)
        │                   │
        │                   └──> AI Auto-Responder
        │                             │
        │                             └──> Sends reply via RCS
        └─────────────────────────────────────────────────────┘
```

You now have full bidirectional RCS messaging from command line with AI integration.
