#!/usr/bin/env python3
"""
Example client for submitting conversation threads to Wolf MCP Gateway

Usage:
    python submit_conversation.py --token <oauth_token> --source android --file conversation.json
    python submit_conversation.py --token <oauth_token> --source web --interactive
"""

import requests
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Default MCP Gateway endpoint
DEFAULT_GATEWAY = "https://wolf-logic-mcp.complexsimplicityai.com"

def submit_conversation(
    gateway_url: str,
    oauth_token: str,
    messages: List[Dict[str, Any]],
    source: str,
    title: str = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Submit conversation thread to MCP Gateway
    
    Args:
        gateway_url: Base URL of MCP Gateway
        oauth_token: Authentik OAuth token
        messages: List of message dicts with 'role' and 'content'
        source: Client source (android, ios, web, desktop)
        title: Optional conversation title
        metadata: Optional metadata dict
    
    Returns:
        Response data from server
    """
    endpoint = f"{gateway_url}/mcp/conversations/submit"
    
    headers = {
        "Authorization": f"Bearer {oauth_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "title": title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "messages": messages,
        "source": source,
        "metadata": metadata or {}
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error submitting conversation: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise

def load_conversation_from_file(filepath: str) -> List[Dict[str, Any]]:
    """Load conversation from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Support different formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'messages' in data:
        return data['messages']
    else:
        raise ValueError("File must contain message array or dict with 'messages' key")

def interactive_conversation() -> List[Dict[str, Any]]:
    """Collect conversation interactively from user"""
    print("\n📝 Interactive Conversation Builder")
    print("Enter messages (type 'done' to finish)")
    print("Format: role: content")
    print("Example: user: Hello, how are you?")
    print()
    
    messages = []
    while True:
        line = input("> ").strip()
        if line.lower() == 'done':
            break
        
        if ':' not in line:
            print("⚠️  Format should be 'role: content'")
            continue
        
        role, content = line.split(':', 1)
        role = role.strip()
        content = content.strip()
        
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        print(f"✓ Added {role} message ({len(content)} chars)")
    
    return messages

def main():
    parser = argparse.ArgumentParser(description="Submit conversation threads to Wolf MCP Gateway")
    parser.add_argument('--gateway', default=DEFAULT_GATEWAY, help='MCP Gateway URL')
    parser.add_argument('--token', required=True, help='OAuth token from Authentik')
    parser.add_argument('--source', required=True, choices=['android', 'ios', 'web', 'desktop'], help='Client source')
    parser.add_argument('--file', help='JSON file with conversation messages')
    parser.add_argument('--interactive', action='store_true', help='Enter messages interactively')
    parser.add_argument('--title', help='Conversation title')
    parser.add_argument('--metadata', help='JSON metadata string')
    
    args = parser.parse_args()
    
    # Load messages
    if args.file:
        print(f"📂 Loading conversation from {args.file}")
        messages = load_conversation_from_file(args.file)
    elif args.interactive:
        messages = interactive_conversation()
    else:
        print("❌ Must specify either --file or --interactive")
        return 1
    
    if not messages:
        print("❌ No messages to submit")
        return 1
    
    # Parse metadata
    metadata = json.loads(args.metadata) if args.metadata else {}
    
    print(f"\n🚀 Submitting conversation:")
    print(f"   Source: {args.source}")
    print(f"   Messages: {len(messages)}")
    print(f"   Title: {args.title or '(auto-generated)'}")
    
    # Submit
    try:
        result = submit_conversation(
            gateway_url=args.gateway,
            oauth_token=args.token,
            messages=messages,
            source=args.source,
            title=args.title,
            metadata=metadata
        )
        
        if result.get('success'):
            print(f"\n✅ Conversation submitted successfully!")
            print(f"   Thread ID: {result['data']['thread_id']}")
            print(f"   Filename: {result['data']['filename']}")
            print(f"   Message Count: {result['data']['message_count']}")
            print(f"   Queue Path: {result['data']['queue_path']}")
        else:
            print(f"\n❌ Submission failed: {result.get('message')}")
            return 1
            
    except Exception as e:
        print(f"\n❌ Failed to submit conversation: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
