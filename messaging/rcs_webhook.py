#!/usr/bin/env python3
"""
RCS Webhook Listener - Receives incoming RCS messages
Logs to PostgreSQL and triggers AI auto-responder
"""
from flask import Flask, request, jsonify
import psycopg2
import json
from datetime import datetime
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def init_database():
    """Initialize RCS messages table if not exists"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Create RCS messages table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rcs_messages (
            id SERIAL PRIMARY KEY,
            message_id TEXT UNIQUE,
            direction TEXT NOT NULL,  -- 'inbound' or 'outbound'
            phone_number TEXT NOT NULL,
            message_text TEXT,
            status TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_rcs_phone ON rcs_messages(phone_number);
        CREATE INDEX IF NOT EXISTS idx_rcs_created ON rcs_messages(created_at DESC);
    """)

    conn.commit()
    cur.close()
    conn.close()
    logger.info("✓ Database initialized")

def log_message(message_id, direction, phone_number, message_text, status, metadata):
    """Log RCS message to PostgreSQL"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO rcs_messages (message_id, direction, phone_number, message_text, status, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (message_id)
        DO UPDATE SET
            status = EXCLUDED.status,
            metadata = EXCLUDED.metadata,
            updated_at = NOW()
        RETURNING id;
    """, (message_id, direction, phone_number, message_text, status, json.dumps(metadata)))

    msg_db_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    logger.info(f"✓ Message logged to database (ID: {msg_db_id})")
    return msg_db_id

def get_conversation_history(phone_number, limit=10):
    """Get recent conversation with a phone number"""
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

    return [
        {'direction': msg[0], 'text': msg[1], 'timestamp': msg[2].isoformat()}
        for msg in reversed(messages)
    ]

@app.route('/webhook/rcs/inbound', methods=['POST'])
def rcs_inbound():
    """Handle incoming RCS messages"""
    try:
        data = request.json
        logger.info(f"→ Received webhook: {json.dumps(data, indent=2)}")

        # Extract message details
        message_id = data.get('messageId')
        sender = data.get('senderAddress', data.get('userContact'))
        message_text = data.get('RCSMessage', {}).get('textMessage', '')

        # Log to database
        log_message(
            message_id=message_id,
            direction='inbound',
            phone_number=sender,
            message_text=message_text,
            status='received',
            metadata=data
        )

        logger.info(f"✓ Inbound message from {sender}: {message_text}")

        # TODO: Trigger AI auto-responder here
        # For now, just acknowledge receipt

        return jsonify({
            'status': 'success',
            'message': 'Message received and logged'
        }), 200

    except Exception as e:
        logger.error(f"✗ Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/webhook/rcs/status', methods=['POST'])
def rcs_status():
    """Handle RCS message status updates"""
    try:
        data = request.json
        logger.info(f"→ Status update: {json.dumps(data, indent=2)}")

        message_id = data.get('messageId')
        status = data.get('status')

        # Update message status in database
        log_message(
            message_id=message_id,
            direction='outbound',  # Status updates are for sent messages
            phone_number='',  # Will be updated if available
            message_text='',
            status=status,
            metadata=data
        )

        logger.info(f"✓ Status update for {message_id}: {status}")

        return jsonify({
            'status': 'success',
            'message': 'Status update received'
        }), 200

    except Exception as e:
        logger.error(f"✗ Error processing status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/webhook/rcs/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'RCS Webhook Listener',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/rcs/conversations/<phone_number>', methods=['GET'])
def get_conversation(phone_number):
    """Get conversation history with a phone number"""
    try:
        # Add + if not present
        if not phone_number.startswith('+'):
            phone_number = f'+{phone_number}'

        limit = request.args.get('limit', 10, type=int)
        messages = get_conversation_history(phone_number, limit)

        return jsonify({
            'phone_number': phone_number,
            'messages': messages,
            'count': len(messages)
        }), 200

    except Exception as e:
        logger.error(f"✗ Error fetching conversation: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    logger.info("→ Initializing RCS Webhook Listener...")
    init_database()

    # Run on port 9090 (configurable)
    port = int(os.environ.get('RCS_WEBHOOK_PORT', 9090))
    host = os.environ.get('RCS_WEBHOOK_HOST', '0.0.0.0')

    logger.info(f"✓ Starting webhook listener on {host}:{port}")
    logger.info(f"  Webhook URLs:")
    logger.info(f"    Inbound: http://{host}:{port}/webhook/rcs/inbound")
    logger.info(f"    Status:  http://{host}:{port}/webhook/rcs/status")
    logger.info(f"    Health:  http://{host}:{port}/webhook/rcs/health")

    app.run(host=host, port=port, debug=False)
