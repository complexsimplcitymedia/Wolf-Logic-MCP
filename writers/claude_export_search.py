#!/usr/bin/env python3
"""
Claude Export Search - Surgical extraction from Anthropic data export
Searches through Claude conversation exports for specific terms.

Usage: python claude_export_search.py <export_path> <search_term>
       python claude_export_search.py /path/to/conversations.json "manic"

ROCm-ready for future GPU acceleration if needed.
"""

import sys
import os
import json
from datetime import datetime
from typing import Generator, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# Check for ROCm/PyTorch availability (optional, for future acceleration)
try:
    import torch
    ROCM_AVAILABLE = torch.cuda.is_available() or hasattr(torch.version, 'hip')
    if ROCM_AVAILABLE:
        print(f"[ROCm] GPU acceleration available: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'HIP'}")
except ImportError:
    ROCM_AVAILABLE = False


def load_export(filepath: str) -> Dict[str, Any]:
    """Load the Claude export JSON file"""
    print(f"[LOAD] Reading {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def extract_conversations(data: Dict[str, Any]) -> List[Dict]:
    """Extract conversations from various Claude export formats"""
    conversations = []

    # Handle different export structures
    if isinstance(data, list):
        # Direct list of conversations
        conversations = data
    elif isinstance(data, dict):
        # Check common keys
        if 'conversations' in data:
            conversations = data['conversations']
        elif 'chats' in data:
            conversations = data['chats']
        elif 'data' in data:
            if isinstance(data['data'], list):
                conversations = data['data']
            elif isinstance(data['data'], dict) and 'conversations' in data['data']:
                conversations = data['data']['conversations']
        else:
            # Maybe the dict itself is keyed by conversation IDs
            for key, value in data.items():
                if isinstance(value, dict) and ('messages' in value or 'chat_messages' in value):
                    value['conversation_id'] = key
                    conversations.append(value)

    print(f"[EXTRACT] Found {len(conversations)} conversations")
    return conversations


def get_messages(conversation: Dict) -> List[Dict]:
    """Extract messages from a conversation object"""
    # Try common message field names
    for key in ['messages', 'chat_messages', 'content', 'turns']:
        if key in conversation and isinstance(conversation[key], list):
            return conversation[key]
    return []


def get_message_content(message: Dict) -> str:
    """Extract text content from a message object"""
    # Handle various message formats
    if isinstance(message, str):
        return message

    if isinstance(message, dict):
        # Direct content field
        for key in ['content', 'text', 'message', 'body']:
            if key in message:
                content = message[key]
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # Content blocks (Claude API format)
                    texts = []
                    for block in content:
                        if isinstance(block, str):
                            texts.append(block)
                        elif isinstance(block, dict) and 'text' in block:
                            texts.append(block['text'])
                    return ' '.join(texts)

    return str(message)


def get_message_role(message: Dict) -> str:
    """Extract role from a message object"""
    if isinstance(message, dict):
        for key in ['role', 'sender', 'author', 'type']:
            if key in message:
                role = message[key]
                if isinstance(role, str):
                    return role.lower()
                elif isinstance(role, dict) and 'role' in role:
                    return role['role'].lower()
    return 'unknown'


def search_conversation(conv: Dict, search_term: str, case_insensitive: bool = True) -> List[Dict]:
    """Search a single conversation for the term"""
    matches = []
    conv_id = conv.get('uuid') or conv.get('id') or conv.get('conversation_id') or 'unknown'
    conv_name = conv.get('name') or conv.get('title') or 'Untitled'
    conv_created = conv.get('created_at') or conv.get('created') or conv.get('timestamp') or 'unknown'

    messages = get_messages(conv)

    pattern = re.compile(re.escape(search_term), re.IGNORECASE if case_insensitive else 0)

    for i, msg in enumerate(messages):
        role = get_message_role(msg)
        content = get_message_content(msg)

        # Only search assistant messages for this use case
        if role in ['assistant', 'claude', 'ai', 'bot']:
            if pattern.search(content):
                # Get surrounding context (50 chars before/after)
                match_positions = [(m.start(), m.end()) for m in pattern.finditer(content)]

                for start, end in match_positions:
                    context_start = max(0, start - 100)
                    context_end = min(len(content), end + 100)
                    context = content[context_start:context_end]

                    matches.append({
                        'conversation_id': conv_id,
                        'conversation_name': conv_name,
                        'conversation_created': conv_created,
                        'message_index': i,
                        'role': role,
                        'match_context': f"...{context}...",
                        'full_content_length': len(content)
                    })

    return matches


def search_export(filepath: str, search_term: str, max_workers: int = 8) -> List[Dict]:
    """Main search function - parallel search across all conversations"""
    print("=" * 60)
    print("CLAUDE EXPORT SEARCH")
    print("=" * 60)
    print(f"File: {filepath}")
    print(f"Search term: '{search_term}'")
    print(f"Workers: {max_workers}")
    print("=" * 60)

    # Load and parse
    data = load_export(filepath)
    conversations = extract_conversations(data)

    if not conversations:
        print("[ERROR] No conversations found in export")
        return []

    # Parallel search
    all_matches = []
    print(f"\n[SEARCH] Scanning {len(conversations)} conversations...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(search_conversation, conv, search_term): i
            for i, conv in enumerate(conversations)
        }

        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 50 == 0:
                print(f"  Processed {completed}/{len(conversations)} conversations...")

            try:
                matches = future.result()
                all_matches.extend(matches)
            except Exception as e:
                conv_idx = futures[future]
                print(f"  [ERROR] Conversation {conv_idx}: {e}")

    print(f"\n[COMPLETE] Found {len(all_matches)} matches")
    return all_matches


def main():
    if len(sys.argv) < 3:
        print("Usage: python claude_export_search.py <export_path> <search_term>")
        print("Example: python claude_export_search.py conversations.json manic")
        sys.exit(1)

    filepath = sys.argv[1]
    search_term = sys.argv[2]

    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    matches = search_export(filepath, search_term)

    # Output results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    if not matches:
        print(f"No matches found for '{search_term}'")
    else:
        # Group by conversation
        by_conv = {}
        for m in matches:
            cid = m['conversation_id']
            if cid not in by_conv:
                by_conv[cid] = {
                    'name': m['conversation_name'],
                    'created': m['conversation_created'],
                    'matches': []
                }
            by_conv[cid]['matches'].append(m)

        print(f"\nFound '{search_term}' in {len(by_conv)} conversations:\n")

        for i, (conv_id, info) in enumerate(by_conv.items(), 1):
            print(f"\n[{i}] Conversation: {info['name']}")
            print(f"    ID: {conv_id}")
            print(f"    Created: {info['created']}")
            print(f"    Matches: {len(info['matches'])}")

            for j, match in enumerate(info['matches'], 1):
                print(f"\n    Match {j}:")
                print(f"    Context: {match['match_context']}")

    # Save results to JSON
    output_file = f"search_results_{search_term}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'search_term': search_term,
            'source_file': filepath,
            'total_matches': len(matches),
            'conversations_with_matches': len(by_conv) if matches else 0,
            'matches': matches
        }, f, indent=2, default=str)

    print(f"\n[SAVED] Results written to {output_file}")


if __name__ == "__main__":
    main()
