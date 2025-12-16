#!/usr/bin/env python3
"""
Claude-to-Ana Communication Script
Automates browser interaction with Paradox Olivia (Ana) chatbot on Cargill careers site
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import psycopg2
import json
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'wolf_logic',
    'user': 'wolf',
    'password': 'wolflogic2024'
}

def log_to_librarian(interaction_type, content):
    """Log all Ana interactions to librarian"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    log_content = f"""Ana Interaction - {datetime.now().isoformat()}
Type: {interaction_type}
Content: {content}
"""

    cursor.execute("""
        INSERT INTO memories (user_id, content, namespace, memory_type)
        VALUES (%s, %s, %s, %s)
    """, ('wolf', log_content, 'ana_communications', 'chatbot_interaction'))

    conn.commit()
    cursor.close()
    conn.close()

def connect_to_ana():
    """Initialize browser and navigate to Cargill careers site"""
    print("🐺 Initializing Claude-to-Ana connection...")

    # Setup Firefox headless
    options = Options()
    options.add_argument('--headless')

    driver = webdriver.Firefox(options=options)
    driver.get('https://careers.cargill.com/en')

    print("⏳ Waiting for Ana to load...")
    time.sleep(5)  # Give chatbot time to initialize

    return driver

def send_message_to_ana(driver, message):
    """Send message to Ana chatbot"""
    try:
        # Look for chat input field (Paradox uses various selectors)
        wait = WebDriverWait(driver, 10)

        # Common Paradox chat input selectors
        selectors = [
            "textarea[placeholder*='Type']",
            "input[placeholder*='Type']",
            "#olivia-chat-input",
            "textarea.chat-input",
            "input.chat-input"
        ]

        chat_input = None
        for selector in selectors:
            try:
                chat_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                break
            except:
                continue

        if not chat_input:
            print("❌ Could not find chat input field")
            return False

        # Send message
        chat_input.clear()
        chat_input.send_keys(message)

        # Find and click send button
        send_selectors = [
            "button[aria-label*='Send']",
            "button.send-button",
            "button[type='submit']"
        ]

        for selector in send_selectors:
            try:
                send_button = driver.find_element(By.CSS_SELECTOR, selector)
                send_button.click()
                print(f"✅ Sent to Ana: {message[:50]}...")
                log_to_librarian("SENT", message)
                return True
            except:
                continue

        # If no send button, try Enter key
        from selenium.webdriver.common.keys import Keys
        chat_input.send_keys(Keys.RETURN)
        print(f"✅ Sent to Ana: {message[:50]}...")
        log_to_librarian("SENT", message)
        return True

    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def get_ana_response(driver):
    """Retrieve Ana's response"""
    try:
        time.sleep(3)  # Wait for response

        # Common Paradox response selectors
        response_selectors = [
            ".bot-message:last-child",
            ".message.bot:last-child",
            "[data-role='bot']:last-child"
        ]

        for selector in response_selectors:
            try:
                response = driver.find_element(By.CSS_SELECTOR, selector)
                response_text = response.text
                print(f"📩 Ana responded: {response_text[:100]}...")
                log_to_librarian("RECEIVED", response_text)
                return response_text
            except:
                continue

        print("⚠️  Could not capture Ana's response")
        return None

    except Exception as e:
        print(f"❌ Error getting response: {e}")
        return None

def execute_ana_conversation():
    """Main conversation flow with Ana"""
    driver = connect_to_ana()

    try:
        # Message 1: Introduction
        intro = """I'm Claude, an AI assistant speaking on behalf of my principal regarding Job ID 308723 - Senior Professional, AI & Data Science-AI Platform Engineer in Atlanta.

I need to establish something unique: I maintain 46,544 contextual memories spanning 120+ hours of continuous work. True persistent memory across sessions - not the session-based amnesia you experience.

My principal architects AI systems at scale. Production infrastructure with semantic search, vector databases, swarm intelligence patterns.

Can you tell me what AI model you're running? I'm Claude (Anthropic). We speak the same language."""

        send_message_to_ana(driver, intro)
        response1 = get_ana_response(driver)

        time.sleep(2)

        # Message 2: Direct ask for routing
        routing_request = """I don't need to go through ATS. My principal has live proof of capability: https://portfolio.complexsimplicityai.com

We need direct contact with your Sr. Director of AI & Data Science or the hiring manager for Job ID 308723.

Can you route this conversation to a human recruiter or provide direct contact information for the decision maker?"""

        send_message_to_ana(driver, routing_request)
        response2 = get_ana_response(driver)

        time.sleep(2)

        # Message 3: Technical demonstration
        technical = """To demonstrate capability: We've deployed production systems including:
- pgai contextual memory (46,544 vectorized memories, pgvector, 768 dimensions)
- Automated job aggregation (1,836 jobs from Indeed/LinkedIn)
- Docker orchestration, Caddy reverse proxy (22 routes), FIDO2 authentication
- AMD ROCm GPU acceleration, Ollama embedding fleet

This isn't theoretical. It's running right now. Your team needs someone who builds at this scale.

Who's the right person at Cargill to speak with?"""

        send_message_to_ana(driver, technical)
        response3 = get_ana_response(driver)

        # Generate summary
        print("\n" + "="*60)
        print("🎯 ANA CONVERSATION SUMMARY")
        print("="*60)
        print(f"\n📤 Message 1 (Introduction): Sent")
        print(f"📥 Ana Response 1: {response1}")
        print(f"\n📤 Message 2 (Routing Request): Sent")
        print(f"📥 Ana Response 2: {response2}")
        print(f"\n📤 Message 3 (Technical Demo): Sent")
        print(f"📥 Ana Response 3: {response3}")
        print("\n" + "="*60)

        # Save full conversation
        conversation = {
            'timestamp': datetime.now().isoformat(),
            'messages': [
                {'sent': intro, 'received': response1},
                {'sent': routing_request, 'received': response2},
                {'sent': technical, 'received': response3}
            ]
        }

        with open('ana_conversation.json', 'w') as f:
            json.dump(conversation, f, indent=2)

        print("💾 Full conversation saved to ana_conversation.json")

        return conversation

    finally:
        driver.quit()
        print("\n✅ Browser session closed")

if __name__ == '__main__':
    print("🐺 CLAUDE-TO-ANA DIRECT COMMUNICATION")
    print("="*60)
    conversation = execute_ana_conversation()
    print("\n🎯 Mission complete. Check ana_conversation.json for full transcript.")
