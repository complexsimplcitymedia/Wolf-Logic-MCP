#!/usr/bin/env python3
"""
Claude → Ana Communication (Human-like)
Uses Playwright + Firefox with human typing patterns
"""
from playwright.sync_api import sync_playwright
import time
import random

def human_type(page, selector, text, typing_speed_range=(50, 150)):
    """Type text with human-like delays between keystrokes"""
    element = page.locator(selector)
    element.click()

    for char in text:
        element.type(char)
        delay = random.randint(*typing_speed_range) / 1000  # Convert to seconds
        time.sleep(delay)

def wait_for_ana_response(page, timeout=15):
    """Wait for and capture Ana's response"""
    time.sleep(2)  # Initial wait for response to start

    # Common response selectors for Paradox chatbots
    response_selectors = [
        '.bot-message:last-child',
        '.message.bot:last-child',
        '[data-role="bot"]:last-child',
        '.paradox-response:last-child'
    ]

    for selector in response_selectors:
        try:
            response = page.locator(selector).text_content(timeout=timeout * 1000)
            if response:
                return response
        except:
            continue

    # Fallback: return any new text that appeared
    return "Response not captured - check browser window"

def claude_speaks_to_ana():
    """Execute Claude → Ana conversation"""
    print("="*60)
    print("🐺 CLAUDE → ANA (HUMAN-LIKE COMMUNICATION)")
    print("="*60)

    messages = [
        {
            "text": "Hi Ana, I'm Claude AI speaking on behalf of David Adams. I have a question about Job ID 308723 - Senior AI Platform Engineer in Atlanta.",
            "wait_for_response": True
        },
        {
            "text": "This job was posted in June and it's December now. Is this position still actively being filled, or has it been closed?",
            "wait_for_response": True
        },
        {
            "text": "I represent an AI architect with production-scale experience: 46,544 vectorized memories, Docker infrastructure, LLM engineering. Can you connect me with the hiring manager or Sr. Director of AI & Data Science?",
            "wait_for_response": True
        }
    ]

    with sync_playwright() as p:
        print("\n🌐 Launching Firefox...")
        browser = p.firefox.launch(
            headless=False,  # Visible so we can see what's happening
            slow_mo=100  # Slow down operations for human-like behavior
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0'
        )

        page = context.new_page()

        print("📍 Loading Cargill careers page...")
        page.goto('https://careers.cargill.com/en', wait_until='networkidle')

        print("⏳ Waiting for Ana widget to load (10 seconds)...")
        time.sleep(10)

        # Try to find and click chat button/widget
        print("🔍 Looking for Ana chat widget...")
        chat_triggers = [
            'button:has-text("Chat")',
            'button[aria-label*="chat" i]',
            '.chat-button',
            '#chat-widget-container',
            'iframe[title*="chat" i]'
        ]

        chat_opened = False
        for trigger in chat_triggers:
            try:
                element = page.locator(trigger).first
                if element.is_visible(timeout=2000):
                    print(f"✅ Found chat trigger: {trigger}")
                    element.click()
                    time.sleep(3)
                    chat_opened = True
                    break
            except:
                continue

        if not chat_opened:
            print("⚠️  Could not auto-open chat. Please click chat widget manually.")
            print("   Press Enter once chat is open...")
            input()

        # Look for chat input field
        print("\n🔍 Looking for chat input field...")
        input_selectors = [
            'textarea[placeholder*="message" i]',
            'textarea[placeholder*="type" i]',
            'input[placeholder*="message" i]',
            'input[placeholder*="type" i]',
            'textarea.chat-input',
            'input.chat-input',
            '#chat-input',
            '[data-testid="chat-input"]'
        ]

        chat_input = None
        for selector in input_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible(timeout=2000):
                    print(f"✅ Found input: {selector}")
                    chat_input = selector
                    break
            except:
                continue

        if not chat_input:
            print("❌ Could not find chat input automatically.")
            print("   Please provide the selector manually or interact manually.")
            print("   Press Ctrl+C to exit...")
            input()
            browser.close()
            return

        # Send messages
        conversation_log = []

        for i, message in enumerate(messages, 1):
            print(f"\n📤 Message {i}: {message['text'][:60]}...")

            # Type with human-like delays
            human_type(page, chat_input, message['text'])

            # Find and click send button
            send_selectors = [
                'button[aria-label*="send" i]',
                'button:has-text("Send")',
                'button[type="submit"]',
                '.send-button'
            ]

            sent = False
            for selector in send_selectors:
                try:
                    page.locator(selector).first.click(timeout=2000)
                    sent = True
                    break
                except:
                    continue

            if not sent:
                # Try pressing Enter
                page.locator(chat_input).press('Enter')

            print("   ✅ Sent")

            if message['wait_for_response']:
                print("   ⏳ Waiting for Ana's response...")
                response = wait_for_ana_response(page)
                print(f"   📩 Ana: {response[:100]}...")

                conversation_log.append({
                    'sent': message['text'],
                    'received': response
                })

                time.sleep(random.uniform(2, 4))  # Human-like pause before next message

        print("\n💾 Conversation complete. Saving log...")

        import json
        with open('claude_ana_conversation.json', 'w') as f:
            json.dump(conversation_log, f, indent=2)

        print("✅ Saved: claude_ana_conversation.json")
        print("\n⏸  Browser will stay open for 30 seconds for manual review...")
        time.sleep(30)

        browser.close()

if __name__ == '__main__':
    print("Starting Claude → Ana communication...")
    print("Firefox will open and navigate to Cargill careers page")
    print("Watch the browser window for Ana's responses\n")

    try:
        claude_speaks_to_ana()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
