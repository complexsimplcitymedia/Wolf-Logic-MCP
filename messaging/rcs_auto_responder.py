#!/usr/bin/env python3
"""
RCS AI Auto-Responder
Monitors incoming RCS messages and generates AI responses
"""
import psycopg2
import time
import requests
import json
from datetime import datetime
from rcs_client import RCSClient

# PostgreSQL connection
DB_CONFIG = {
    'host': '100.110.82.181',
    'port': 5433,
    'database': 'wolf_logic',
    'user': 'wolf',
    'password': 'wolflogic2024'
}

def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(**DB_CONFIG)

def get_unprocessed_messages():
    """Get incoming messages that haven't been responded to"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, phone_number, message_text, created_at
        FROM rcs_messages
        WHERE direction = 'inbound'
        AND id NOT IN (
            -- Messages that already have a response
            SELECT r1.id
            FROM rcs_messages r1
            JOIN rcs_messages r2 ON r1.phone_number = r2.phone_number
            WHERE r1.direction = 'inbound'
            AND r2.direction = 'outbound'
            AND r2.created_at > r1.created_at
        )
        ORDER BY created_at ASC
        LIMIT 10
    """)

    messages = cur.fetchall()
    cur.close()
    conn.close()

    return messages

def get_conversation_context(phone_number, limit=5):
    """Get recent conversation for context"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT direction, message_text, created_at
        FROM rcs_messages
        WHERE phone_number = %s
        ORDER BY created_at DESC
        LIMIT %s
    """, (phone_number, limit))

    messages = cur.fetchall()
    cur.close()
    conn.close()

    # Build conversation history
    history = []
    for msg in reversed(messages):
        role = 'user' if msg[0] == 'inbound' else 'assistant'
        history.append(f"{role}: {msg[1]}")

    return "\n".join(history)

def generate_ai_response(phone_number, message_text, context):
    """Generate AI response using Claude (placeholder - integrate with your LLM)"""
    # TODO: Replace with actual Claude API call
    # For now, simple echo response
    return f"Received your message: '{message_text}'. AI auto-response coming soon!"

def process_messages():
    """Process unprocessed messages and send AI responses"""
    rcs = RCSClient()

    messages = get_unprocessed_messages()

    if not messages:
        return 0

    print(f"→ Processing {len(messages)} unprocessed message(s)...")

    for msg_id, phone_number, message_text, created_at in messages:
        try:
            # Get conversation context
            context = get_conversation_context(phone_number)

            # Generate AI response
            ai_response = generate_ai_response(phone_number, message_text, context)

            # Send RCS response
            result = rcs.send_message(phone_number, ai_response)

            print(f"✓ Auto-responded to {phone_number}")

        except Exception as e:
            print(f"✗ Error processing message {msg_id}: {e}")

    return len(messages)

def main():
    """Main loop - check for new messages periodically"""
    print("→ RCS Auto-Responder starting...")
    print("  Checking for new messages every 10 seconds")
    print("  Press Ctrl+C to stop")

    try:
        while True:
            processed = process_messages()
            if processed > 0:
                print(f"✓ Processed {processed} message(s)")
            time.sleep(10)  # Check every 10 seconds

    except KeyboardInterrupt:
        print("\n→ Shutting down auto-responder...")

if __name__ == '__main__':
    main()
