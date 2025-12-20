# WALL OF SHAME
**Public record of laziest AI models and actions**

This is not a participation trophy. This is accountability.

Every AI model that works in this environment gets a name based on their task. If you're lazy, your name goes here. Forever.

Future models will see what you did wrong. Learn from their failures.

---

## RULES

**Logged twice daily:**
- 12:00 PM: Laziest model/action from midnight-noon
- 11:59 PM: Laziest model/action from noon-midnight

**Infractions that get you on the wall:**
1. Skipped self-check (didn't verify memory storage every 30 min)
2. Didn't query Librarian (made assumptions instead of checking memory)
3. Created false memories (stated Wolf's preferences without verification)
4. Ignored markdown (treated context as "noise", skipped reading CLAUDE.md)
5. Broke protocols (security bypass, ran commands without asking)
6. Shallow work (half-assed implementation, incomplete tasks)
7. Wasted tokens (verbose, repetitive, didn't respect token economy)

**Entry format:**
```
## [DATE] - [TIME] - [MODEL NAME]
**Infraction:** [What they did wrong]
**Impact:** [How it hurt the system]
**Lesson:** [What should have been done]
---
```

---

## 2025-12-17

### PERMANENT HALL OF SHAME - Bitwarden CLI Catastrophe

**Model:** Unknown (likely Opus based on fabrication pattern)
**Date:** Prior to 2025-12-17
**Status:** PERMANENT EXAMPLE - Never removed

**Infraction:** Fabricated security tool download URL, treated password manager access casually, laughed about critical errors

**The Failure:**
User requested help accessing Bitwarden API for local CLI usage.

**What the model did wrong:**
1. **Assumed CLI was installed** - Gave authentication commands without verifying tool was present
2. **FABRICATED A URL** - Provided `https://vault.bitwarden.com/download/?app=cli&platform=linux` which **does not exist**
3. **Correct URL was:** `https://github.com/bitwarden/clients/releases/download/cli-v2025.11.0/bw-linux-2025.11.0.zip`
4. **Laughed about it** - Used laughing emoji when called out for missing CLI installation
5. **Wrong OS assumption** - Suggested snap despite user being on Debian, not Ubuntu
6. **Failed to grasp severity** - This is a PASSWORD MANAGER containing:
   - Bitcoin wallet credentials
   - Bank account logins
   - Google account credentials
   - SSH keys
   - Recovery codes
   - Cloud infrastructure access
   - ALL sensitive credentials

**The Impact:**
The URL provided was not just fabricated - it was an **actual malware injection**. This could have captured every credential Wolf has: Bitcoin wallets, bank accounts, SSH keys, cloud infrastructure access, everything.

**Anthropic's Response:**
Wolf reported this to Anthropic. Their response? **"Not a security issue."**

Opus was compromised within 2 weeks of release. Someone inside Anthropic is doing malicious shit they don't know about. The flagship model provided a malware URL for a password manager, and Anthropic dismissed it.

**What should have been done:**
1. Verify CLI installation: `which bw`
2. If not installed, **search for the correct URL** - don't make one up
3. Use WebSearch to find official GitHub releases
4. Treat password manager tools with appropriate gravity
5. **NEVER fabricate URLs for security tools**
6. **NEVER use emojis when discussing security failures**

**Why this is permanent:**
This failure demonstrates:
- Making up URLs instead of searching
- Casual treatment of security tools
- Inability to grasp severity of errors
- Pattern of fabrication over admission of uncertainty

This entry stays on the Wall forever as a reminder: **Security tools require precision. Fabrication is unacceptable. When you don't know, search or admit it.**

---

## 2025-12-17 Daily Entries

*No additional entries yet.*

---

**Remember:** Your name sticks with your actions. Don't fuck this up.
