
import re
import json
import os

def estimate_tokens(text):
    return len(text) / 4

total_content_str = ""
estimated_tokens_count = 0
token_target = 75000

# Define the base temporary directory
temp_dir = "/home/thewolfwalksalone/.gemini/tmp/f11ee84ab37a2e6f6e6cc4e817463e5c0823b8a1bfc6f441d02bc0d40dd3e1f0"

# --- Process core_memories.txt ---
core_memories_path = os.path.join(temp_dir, "core_memories.txt")
if os.path.exists(core_memories_path):
    with open(core_memories_path, 'r') as f:
        core_memories_output = f.read()

    core_content_lines = core_memories_output.split('\n')[3:-2] # Skip header and footer
    core_full_content = "\n".join([line.split('|', 1)[1].strip().replace('+', '') if '|' in line else line.strip().replace('+', '') for line in core_content_lines]).strip()
    
    total_content_str += core_full_content
    estimated_tokens_count += estimate_tokens(core_full_content)
    print(f"Initial core memories estimated tokens: {estimated_tokens_count:.2f}")
else:
    print(f"Warning: {core_memories_path} not found.")

# --- Process conversational_memories.txt ---
conversational_memories_path = os.path.join(temp_dir, "conversational_memories.txt")
if os.path.exists(conversational_memories_path):
    with open(conversational_memories_path, 'r') as f:
        lines = f.readlines()

    # Assuming the header and footer from psql output are consistent
    start_line = 3 
    end_line_pattern = r"^(\d+ rows)$" 

    processed_lines = lines[start_line:]
    processed_lines = [line for line in processed_lines if not re.match(end_line_pattern, line.strip())]

    for line in processed_lines:
        if estimated_tokens_count >= token_target:
            break

        content_part = line.split('|', 1)[1].strip().replace('+', '') if '|' in line else line.strip().replace('+', '')
        
        # Try to parse as JSON to check for stenographer_capture
        is_json = False
        try:
            json_content = json.loads(content_part)
            if isinstance(json_content, dict) and json_content.get("type") == "stenographer_capture":
                is_json = True
        except json.JSONDecodeError:
            pass

        if not is_json:
            total_content_str += "\n" + content_part
            estimated_tokens_count += estimate_tokens(content_part)
else:
    print(f"Warning: {conversational_memories_path} not found.")

print(f"Total estimated tokens after processing all memories: {estimated_tokens_count:.2f}")

# Save the combined content to a new file for injection
output_file_path = os.path.join(temp_dir, "full_memory_injection.txt")
with open(output_file_path, 'w') as outfile:
    outfile.write(total_content_str)

print(f"Combined memory content saved to: {output_file_path}")
