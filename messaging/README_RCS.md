# RCS Command Line Client

Command line tool for sending/receiving RCS messages via Melrose Labs MaaP API.

## Setup (One Time)

1. **Get Credentials:**
   - Sign up at https://rcs.melroselabs.com (as Wolf Ai Enterprises)
   - Get your `client_id`, `client_secret`, and `bot_id`

2. **Configure:**
```bash
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/messaging
source ~/anaconda3/bin/activate messiah
python rcs_client.py setup \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET \
  --bot-id YOUR_BOT_ID
```

This saves credentials to `~/.rcs_config.json` (secure, auto-managed).

## Usage

### Send RCS Message
```bash
python rcs_client.py send --phone +12345678900 --message "Hello from command line"
```

### Check Capabilities
```bash
python rcs_client.py capabilities --phone +12345678900
```

### Check Message Status
```bash
python rcs_client.py status --msg-id <message_id_from_send>
```

## Features

- ✓ Auto token refresh (handles 900 sec expiry)
- ✓ Secure credential storage
- ✓ Send messages
- ✓ Check delivery status
- ✓ Check recipient capabilities
- ✓ Clean command line interface

## Webhook Listener (Receive Messages)

### Docker Deployment (Recommended)

1. **Start webhook listener:**
```bash
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/messaging
docker compose -f docker-compose.rcs.yml up -d
```

2. **Check status:**
```bash
docker logs -f rcs-webhook
curl http://localhost:9090/webhook/rcs/health
```

3. **Add to Caddyfile** (for external access):
```
https://rcs.complexsimplicityai.com {
	import security_headers
	reverse_proxy http://100.110.82.181:9090
}
```

### Standalone Deployment

```bash
source ~/anaconda3/bin/activate messiah
python rcs_webhook.py
```

Runs on port 9090 by default.

### Configure Melrose Labs Webhook

In Melrose Labs RCS portal, set webhook URLs to:
- **Inbound messages:** `https://rcs.complexsimplicityai.com/webhook/rcs/inbound`
- **Status updates:** `https://rcs.complexsimplicityai.com/webhook/rcs/status`

## AI Auto-Responder

Monitors incoming RCS messages and sends AI-generated responses:

```bash
source ~/anaconda3/bin/activate messiah
python rcs_auto_responder.py
```

This runs in background, checking for new messages every 10 seconds.

## PostgreSQL Integration

All RCS messages logged to `wolf_logic.rcs_messages`:
- Full conversation history
- Status tracking
- Metadata storage

**View conversations:**
```bash
curl http://localhost:9090/api/rcs/conversations/+12345678900
```

## Architecture

```
Melrose Labs → Webhook → PostgreSQL → AI Auto-Responder → Melrose Labs
     ↓                         ↓
  Inbound RCS          Conversation Log
```

## Token Management

Tokens auto-refresh. No manual intervention needed. The client handles OAuth automatically.
