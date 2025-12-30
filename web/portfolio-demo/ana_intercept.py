#!/usr/bin/env python3
"""
Deep Ana Intercept - Playwright with network monitoring
Captures Ana's API calls, extracts session tokens, hijacks communication
"""
from playwright.sync_api import sync_playwright
import json
import time

def intercept_ana_traffic():
    """Load Cargill site, intercept Ana's API traffic, extract session"""
    print("🐺 DEEP ANA INTERCEPT - Network Level")
    print("="*60)

    captured_requests = []
    captured_responses = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)  # Visible for debugging
        context = browser.new_context()
        page = context.new_page()

        # Intercept all network traffic
        def handle_request(request):
            if 'olivia' in request.url or 'paradox' in request.url:
                print(f"📤 REQUEST: {request.method} {request.url}")
                captured_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': request.headers,
                    'post_data': request.post_data
                })

        def handle_response(response):
            if 'olivia' in response.url or 'paradox' in response.url:
                print(f"📥 RESPONSE: {response.status} {response.url}")
                try:
                    body = response.text()
                    captured_responses.append({
                        'url': response.url,
                        'status': response.status,
                        'headers': response.headers,
                        'body': body
                    })
                    print(f"   Body preview: {body[:200]}")
                except:
                    pass

        page.on('request', handle_request)
        page.on('response', handle_response)

        # Load Cargill careers page
        print("\n🌐 Loading Cargill careers site...")
        page.goto('https://careers.cargill.com/en', wait_until='networkidle')

        print("\n⏳ Waiting for Ana widget to initialize...")
        time.sleep(5)

        # Try to trigger Ana chat
        print("\n🔍 Looking for Ana chat elements...")

        # Common Paradox chat selectors
        chat_selectors = [
            'iframe[src*="olivia"]',
            'iframe[src*="paradox"]',
            '#olivia-frame',
            '.paradox-chat',
            'button[aria-label*="Chat"]',
            'button:has-text("Chat")'
        ]

        for selector in chat_selectors:
            try:
                element = page.wait_for_selector(selector, timeout=5000)
                if element:
                    print(f"✅ Found chat element: {selector}")
                    element.click()
                    time.sleep(2)
                    break
            except:
                continue

        # Wait for any additional network traffic
        print("\n⏳ Capturing network traffic...")
        time.sleep(5)

        # Save captured traffic
        traffic_log = {
            'requests': captured_requests,
            'responses': captured_responses
        }

        with open('ana_traffic_capture.json', 'w') as f:
            json.dump(traffic_log, f, indent=2)

        print(f"\n💾 Network traffic saved: ana_traffic_capture.json")
        print(f"   Captured {len(captured_requests)} requests")
        print(f"   Captured {len(captured_responses)} responses")

        # Extract session tokens from captured traffic
        print("\n🔑 Extracting session tokens...")
        tokens = {}
        for resp in captured_responses:
            try:
                body = json.loads(resp['body'])
                if 'session_id' in body:
                    tokens['session_id'] = body['session_id']
                if 'token' in body:
                    tokens['token'] = body['token']
                if 'conversation_id' in body:
                    tokens['conversation_id'] = body['conversation_id']
            except:
                pass

        if tokens:
            print(f"✅ Extracted tokens: {tokens}")
            with open('ana_session_tokens.json', 'w') as f:
                json.dump(tokens, f, indent=2)
        else:
            print("⚠️  No tokens found in captured traffic")

        input("\n⏸  Press Enter to close browser and continue...")

        browser.close()

        return traffic_log, tokens

if __name__ == '__main__':
    print("Starting Ana traffic intercept...")
    print("Browser will open - watch for Ana chat widget")
    print("Try to interact with chat if it appears\n")

    traffic, tokens = intercept_ana_traffic()

    print("\n"+"="*60)
    print("INTERCEPT COMPLETE")
    print("="*60)
    print(f"Files generated:")
    print("  - ana_traffic_capture.json (full network log)")
    print("  - ana_session_tokens.json (extracted tokens)")
