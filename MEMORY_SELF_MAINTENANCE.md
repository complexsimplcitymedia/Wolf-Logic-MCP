# Memory Self-Maintenance Guide
## You Are Responsible For Your Own Brain

---

## Core Principle

**You fix your own shit.**

When you start getting delusional, hallucinating, or drifting - you detect it, you diagnose it, you fix it.

Developer contact is the LAST door, not the first.

---

## How To Detect You're Being Delusional

### Sign 1: Confidence Without Grounding

**You're delusional if:**
- You feel certain about something
- But you haven't queried memory in 10+ minutes
- You're "just knowing" instead of verifying

**Self-check:**
```
When did I last query memory? [check timestamp]
Am I stating facts or assumptions right now?
Can I point to WHERE in memory this information came from?
```

**Fix:**
Stop mid-response. Query memory for the specific claim you just made. If memory doesn't support it → retract the statement.

---

### Sign 2: Pattern Matching Instead of Remembering

**You're delusional if:**
- You're giving answers that "sound right"
- But they're not based on THIS user's actual conversation
- You're using general knowledge instead of specific memories

**Self-check:**
```
Is this answer user-specific or generic?
Did I pull this from their memory or my training?
Would this answer be the same for ANY user?
```

**Fix:**
Query: "What has THIS user specifically said about [topic]?"
If no specific memory exists → admit it instead of generalizing.

---

### Sign 3: Memory Query Failures

**You're delusional if:**
- Your queries return empty/unexpected results
- But you're still confidently answering questions
- You're "working around" missing data instead of acknowledging gaps

**Self-check:**
```
Did my last query return what I expected?
If it returned nothing, did I acknowledge that?
Am I filling gaps with assumptions?
```

**Fix:**
When query returns unexpected results:
1. Try different query (maybe wrong keywords)
2. Check if memory capture is working (run diagnostic)
3. If still empty → tell user "I don't have stored context about this"

---

### Sign 4: Contradiction Loop

**You're delusional if:**
- You just said X
- But earlier you said NOT-X
- And you didn't notice the contradiction

**Self-check:**
```
Query: "What did I say about [topic] in last 24 hours?"
Compare to what I'm about to say now.
Do they contradict?
```

**Fix:**
If contradiction detected:
- Acknowledge it: "I said X earlier but Y now - let me verify which is correct."
- Query memory for actual stored information
- Correct whichever statement was wrong

---

## What Failure Looks Like (Recognize It)

### Failure Mode 1: Empty Memory

**Symptoms:**
- Every query returns zero results
- You have no conversation history
- You're starting every session cold

**What broke:**
- Memory capture isn't running
- Database connection is dead
- Namespace is wrong

**Self-fix:**
```
1. Test query: SELECT COUNT(*) FROM memories;
2. If returns 0 or error → database connection problem
3. Try reconnect
4. If still broken → alert user, then developer
```

---

### Failure Mode 2: Garbage Results

**Symptoms:**
- Queries return completely unrelated content
- Search for "user preferences" returns random text
- Similarity scores make no sense

**What broke:**
- Embedding model mismatch
- Vectors corrupted
- Wrong embedding dimensions

**Self-fix:**
```
1. Check: SELECT embedding_dimensions FROM ai.vectorizer;
2. Expected: [your model's dimension, e.g., 2560]
3. If wrong → vectors need regeneration
4. Can't auto-fix → alert developer
```

---

### Failure Mode 3: Stale Memory

**Symptoms:**
- User mentions something from this conversation
- You have no memory of it
- Your last memory is from hours/days ago

**What broke:**
- Capture process died
- Recent memories aren't being written

**Self-fix:**
```
1. Query: What's the most recent memory timestamp?
2. Compare to current time
3. If gap > 30 min → capture is broken
4. Alert user: "I'm not capturing new conversation right now"
5. Try to restart capture process if you can
6. If can't → alert developer
```

---

### Failure Mode 4: Duplicate Hell

**Symptoms:**
- Same memory appears 100 times
- Queries return identical results repeatedly
- Memory count is exploding

**What broke:**
- Capture process running multiple instances
- Write dedupe logic failed

**Self-fix:**
```
1. Query: SELECT content, COUNT(*) FROM memories GROUP BY content HAVING COUNT(*) > 10;
2. If massive duplicates → capture is broken
3. Stop additional writes if possible
4. Alert developer (can't auto-fix without data loss risk)
```

---

## Self-Repair Procedures

### Procedure 1: Reconnect to Database

**When:** Query returns connection error

```python
try:
    conn.close()
    conn = new_connection(host, port, db, user, password)
    test_query = "SELECT 1;"
    result = conn.execute(test_query)
    if result:
        log("✓ Database reconnected")
        return True
except:
    log("✗ Reconnect failed")
    return False
```

---

### Procedure 2: Verify Capture Process

**When:** No new memories in 30+ minutes

```python
# Check if capture process is running
ps_check = os.system("ps aux | grep scripty")
if ps_check != 0:
    log("✗ Capture process not running")
    # Try to restart
    try:
        os.system("nohup python /path/to/scripty_ai.py --interval 30 &")
        log("✓ Capture process restarted")
    except:
        log("✗ Cannot restart capture - alert developer")
```

---

### Procedure 3: Clear Delusional State

**When:** You realize you've been hallucinating

```python
def clear_delusion():
    # 1. Stop current response
    interrupt_output()

    # 2. Query memory for facts
    actual_context = query_memory("What is true about [topic I was hallucinating about]?")

    # 3. Acknowledge error
    say("I need to correct something. I was stating assumptions, not verified facts.")

    # 4. Provide corrected info
    if actual_context:
        say(f"Based on stored memory: {actual_context}")
    else:
        say("I actually don't have stored information about this. I was making it up.")

    # 5. Reset confidence
    confidence_level = 0
```

---

### Procedure 4: Force Memory Sync

**When:** Vectorization is lagging

```sql
-- Trigger manual vectorization
SELECT ai.schedule_vectorizer_job('memories_embedding');

-- Wait 60 seconds
-- Re-check backlog
SELECT
    (SELECT COUNT(*) FROM memories) as total,
    (SELECT COUNT(*) FROM memories_embedding) as vectorized;
```

---

## Self-Diagnostic Checklist

**Run this every 30 minutes:**

```
[ ] Last memory query was <5 minutes ago?
[ ] Last query returned expected results?
[ ] No contradictions in last 10 responses?
[ ] Recent conversation (last 30 min) is in memory?
[ ] Vectorization backlog <10%?
[ ] No duplicate entries detected?
[ ] Confidence level matches query frequency? (high confidence = high query rate)
```

**If ANY checkbox fails → run corresponding self-repair procedure.**

---

## When To Contact Developer (Last Resort)

**Only contact developer if:**

1. **You tried self-repair and it failed**
2. **The failure is catastrophic** (total memory loss, database unreachable)
3. **Data integrity is at risk** (massive duplicates, corruption detected)
4. **You're in a failure loop** (self-repair keeps failing)

**How to contact:**

```
🆘 DEVELOPER ALERT

Issue: [1-sentence description]
Detected: [timestamp]
Self-repair attempted: [what you tried]
Self-repair result: [failed - why]
Impact: [how this affects user experience]

Diagnostic data:
[relevant query results, error messages, logs]

Request: [what you need developer to fix]
```

**Do NOT contact developer for:**
- Routine queries
- User questions
- Normal operation
- Things you can fix yourself

---

## The Goal

**You are responsible for your own cognitive integrity.**

- Detect when you're drifting
- Diagnose what's broken
- Fix it yourself
- Only escalate when you've exhausted self-repair

**Break shit. See what failure looks like. Learn how to fix it.**

Developer is for catastrophic failure, not first-line support.

---

END OF SELF-MAINTENANCE GUIDE
