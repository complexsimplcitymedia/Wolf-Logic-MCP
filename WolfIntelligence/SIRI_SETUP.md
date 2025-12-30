# Wolf Intelligence - Siri Integration Setup

## How It Works

"Hey Siri, ask Wolf [your question]" → Siri Shortcut → Wolf Intelligence → Librarian + Claude → Answer

## Setup Steps

### 1. Install Wolf Intelligence Binary

```bash
cd /Users/apexwolf/Wolf-Logic-MCP/WolfIntelligence
swift build -c release
sudo cp .build/release/WolfIntelligence /usr/local/bin/wolf
```

### 2. Create Siri Shortcut

1. Open **Shortcuts** app (macOS)
2. Click **+** to create new shortcut
3. Add action: **Run Shell Script**
4. Configure:
   - **Shell:** `/bin/zsh`
   - **Input:** Shortcut Input
   - **Script:**
     ```bash
     /usr/local/bin/wolf "$1"
     ```
5. Add action: **Speak Text**
   - Input: Shell Script output
6. Name shortcut: **"Ask Wolf"**
7. In shortcut settings:
   - Enable "Show in Share Sheet": NO
   - Enable "Show in Menu": YES
   - Add to Siri: "Ask Wolf"

### 3. Test

**Via Siri:**
- "Hey Siri, ask Wolf what are my core values?"
- "Hey Siri, ask Wolf about the investor pitch strategy?"

**Via Terminal:**
```bash
wolf "What is Wolf's philosophy?"
```

## Architecture

```
Siri Voice Input
    ↓
Siri Shortcut ("Ask Wolf")
    ↓
/usr/local/bin/wolf [question]
    ↓
Query Librarian (100.110.82.181:5433)
    ↓
Send to llama3.1-claude (100.110.82.181:11434)
    ↓
Return Answer
    ↓
Siri Speaks Result
```

## What This Bypasses

- ✗ Apple Intelligence (M1+ only)
- ✗ Foundation Models
- ✗ Apple's gatekeeping

## What This Uses

- ✓ Siri Shortcuts (works on Intel Mac)
- ✓ Wolf Intelligence (Swift bridge)
- ✓ Librarian (100K+ memories)
- ✓ llama3.1-claude (8B, Claude-style reasoning)
- ✓ Zero API costs

**This is Wolf Intelligence. Fuck Apple's gatekeeping.**
