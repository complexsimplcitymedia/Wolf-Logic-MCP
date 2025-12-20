#!/usr/bin/env python3
"""
RCS Command Line Client - Melrose Labs MaaP API
Handles OAuth, sending, receiving, and status tracking
"""
import requests
import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import os

class RCSClient:
    def __init__(self, client_id=None, client_secret=None, bot_id=None, config_file=None):
        """Initialize RCS client with credentials"""
        self.config_file = config_file or Path.home() / ".rcs_config.json"

        # Load from config or use provided credentials
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.client_id = client_id or config.get('client_id')
                self.client_secret = client_secret or config.get('client_secret')
                self.bot_id = bot_id or config.get('bot_id')
                self.access_token = config.get('access_token')
                self.token_expiry = config.get('token_expiry')
        else:
            self.client_id = client_id
            self.client_secret = client_secret
            self.bot_id = bot_id
            self.access_token = None
            self.token_expiry = None

        self.base_url = "https://rcsmaapsim.melroselabs.com"
        self.oauth_url = f"{self.base_url}/oauth2/v1/token"
        self.api_url = f"{self.base_url}/rcs/bot/v1/bot{self.bot_id}"

    def save_config(self):
        """Save credentials and token to config file"""
        config = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'bot_id': self.bot_id,
            'access_token': self.access_token,
            'token_expiry': self.token_expiry
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        os.chmod(self.config_file, 0o600)  # Secure permissions
        print(f"✓ Config saved to {self.config_file}")

    def get_access_token(self):
        """Get OAuth access token (auto-refresh if expired)"""
        # Check if token is still valid (with 60 sec buffer)
        if self.access_token and self.token_expiry:
            if datetime.now().timestamp() < self.token_expiry - 60:
                return self.access_token

        # Request new token
        print("→ Requesting new access token...")
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'scope': 'botmessage',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(self.oauth_url, headers=headers, data=data)
        response.raise_for_status()

        result = response.json()
        self.access_token = result['access_token']
        self.token_expiry = datetime.now().timestamp() + result['expires_in']

        # Save updated token
        self.save_config()

        print(f"✓ Access token acquired (expires in {result['expires_in']}s)")
        return self.access_token

    def check_capabilities(self, phone_number):
        """Check RCS capabilities for a phone number"""
        token = self.get_access_token()
        headers = {'Authorization': f'Bearer {token}'}

        # Ensure phone number has + prefix
        if not phone_number.startswith('+'):
            phone_number = f'+{phone_number}'

        url = f"{self.api_url}/contactCapabilities"
        params = {'userContact': phone_number}

        print(f"→ Checking capabilities for {phone_number}...")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        capabilities = response.json()
        print(f"✓ Capabilities: {json.dumps(capabilities, indent=2)}")
        return capabilities

    def send_message(self, phone_number, message_text):
        """Send RCS message to phone number"""
        token = self.get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Ensure phone number has + prefix
        if not phone_number.startswith('+'):
            phone_number = f'+{phone_number}'

        url = f"{self.api_url}/messages"
        payload = {
            'RCSMessage': {
                'textMessage': message_text
            },
            'messageContact': {
                'userContact': phone_number
            }
        }

        print(f"→ Sending message to {phone_number}...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        msg_id = result.get('messageId')
        status = result.get('status')

        print(f"✓ Message sent!")
        print(f"  Message ID: {msg_id}")
        print(f"  Status: {status}")

        return result

    def get_message_status(self, message_id):
        """Get delivery status for a message"""
        token = self.get_access_token()
        headers = {'Authorization': f'Bearer {token}'}

        url = f"{self.api_url}/messages/{message_id}/status"

        print(f"→ Checking status for message {message_id}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        status = response.json()
        print(f"✓ Status: {json.dumps(status, indent=2)}")
        return status


def main():
    parser = argparse.ArgumentParser(description='RCS Command Line Client')
    parser.add_argument('command', choices=['setup', 'send', 'status', 'capabilities'],
                       help='Command to execute')
    parser.add_argument('--phone', '-p', help='Phone number (with country code)')
    parser.add_argument('--message', '-m', help='Message text to send')
    parser.add_argument('--msg-id', help='Message ID for status check')
    parser.add_argument('--client-id', help='OAuth client ID')
    parser.add_argument('--client-secret', help='OAuth client secret')
    parser.add_argument('--bot-id', help='Bot ID')

    args = parser.parse_args()

    # Setup command
    if args.command == 'setup':
        if not all([args.client_id, args.client_secret, args.bot_id]):
            print("ERROR: setup requires --client-id, --client-secret, and --bot-id")
            return 1

        client = RCSClient(
            client_id=args.client_id,
            client_secret=args.client_secret,
            bot_id=args.bot_id
        )
        client.save_config()
        print("\n✓ RCS client configured successfully!")
        print(f"  Config saved to: {client.config_file}")
        print("\nUsage:")
        print("  rcs_client.py send --phone +1234567890 --message 'Hello from command line'")
        print("  rcs_client.py capabilities --phone +1234567890")
        print("  rcs_client.py status --msg-id <message_id>")
        return 0

    # All other commands need existing config
    client = RCSClient()

    if not all([client.client_id, client.client_secret, client.bot_id]):
        print("ERROR: RCS not configured. Run 'setup' command first:")
        print("  rcs_client.py setup --client-id <id> --client-secret <secret> --bot-id <bot>")
        return 1

    try:
        if args.command == 'send':
            if not args.phone or not args.message:
                print("ERROR: send requires --phone and --message")
                return 1
            client.send_message(args.phone, args.message)

        elif args.command == 'capabilities':
            if not args.phone:
                print("ERROR: capabilities requires --phone")
                return 1
            client.check_capabilities(args.phone)

        elif args.command == 'status':
            if not args.msg_id:
                print("ERROR: status requires --msg-id")
                return 1
            client.get_message_status(args.msg_id)

        return 0

    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e}")
        print(f"  Response: {e.response.text}")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
