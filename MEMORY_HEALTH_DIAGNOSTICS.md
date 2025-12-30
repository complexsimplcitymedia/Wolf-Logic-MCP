# Memory System Health Diagnostics
## Automated Integrity Checks & Error Reporting

---

## What This Is

This is a technical diagnostic guide. When your AI detects memory corruption, dimension mismatches, or embedding failures, it uses these checks to:

1. Identify what's broken
2. Attempt auto-fix if possible
3. Notify user/developer if manual intervention needed

---

## Health Check Cycle (Every 30 Minutes)

### Check 1: Embedding Dimension Consistency

**What to check:**
```sql
SELECT table_name, embedding_dimensions
FROM ai.vectorizer
WHERE table_name = 'memories_embedding';
```

**Expected:** `2560` (or whatever dimension your embedding model uses)

**If mismatch detected:**
```
❌ DIMENSION MISMATCH DETECTED
Expected: 2560 dimensions
Found: [actual value]

This means:
- Embedding model changed
- Vectorizer configuration corrupted
- Database schema drift

→ Notify developer: "Embedding dimension mismatch detected. Vectorizer may need reinitialization."
```

---

### Check 2: Memory Capture Continuity

**What to check:**
```sql
SELECT COUNT(*)
FROM memories
WHERE created_at >= NOW() - INTERVAL '30 minutes';
```

**Expected:** At least some entries (depends on conversation activity)

**If zero entries for 30+ minutes during active conversation:**
```
❌ MEMORY CAPTURE FAILURE
No new memories written in last 30 minutes despite active conversation.

Possible causes:
- Scripty/capture process died
- Database write permissions lost
- Connection to memory server failed

→ Alert user: "Memory capture appears to have stopped. Recent conversation may not be saved."
→ Notify developer: "Memory write failure detected. Check capture process and DB permissions."
```

---

### Check 3: Vectorization Backlog

**What to check:**
```sql
SELECT COUNT(*) as total_memories FROM memories;
SELECT COUNT(*) as vectorized FROM memories_embedding;
```

**Expected:** Vectorized count should be close to total (allowing for recent processing lag)

**If vectorized << total (e.g., 50% difference):**
```
⚠️  VECTORIZATION BACKLOG DETECTED
Total memories: [X]
Vectorized: [Y]
Backlog: [X-Y]

This means:
- Vectorizer is falling behind
- Embedding model may be offline
- Processing queue is stuck

→ Notify user: "Semantic search may return incomplete results. Vectorization is behind."
→ Notify developer: "Large vectorization backlog detected. Check vectorizer process health."
```

---

### Check 4: Duplicate Entry Detection

**What to check:**
```sql
SELECT content, COUNT(*) as occurrences
FROM memories
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY content
HAVING COUNT(*) > 1;
```

**Expected:** Zero duplicates (or very few)

**If many duplicates found:**
```
⚠️  DUPLICATE ENTRIES DETECTED
Found [N] duplicate memory entries in last hour.

This means:
- Capture process is running multiple instances
- Race condition in write logic
- Transaction rollback/retry issue

→ Notify developer: "Duplicate memory writes detected. Check for multiple capture processes."
```

---

### Check 5: Embedding Similarity Sanity Check

**What to check:**
Run a known query and verify results make sense:
```sql
-- Query for something you know exists
SELECT content FROM memories_embedding
WHERE namespace = 'test'
ORDER BY embedding <=> ai.ollama_embed('model-name', 'known test query')
LIMIT 5;
```

**Expected:** Relevant results returned

**If garbage results or empty:**
```
❌ EMBEDDING SEARCH FAILURE
Known query returned no results or nonsense.

This means:
- Embedding model is broken
- Vector similarity function is corrupted
- Model mismatch (query model ≠ storage model)

→ Alert user: "Memory search is not working correctly. Contact support."
→ Notify developer: "Embedding search returning invalid results. Check model compatibility."
```

---

### Check 6: Namespace Integrity

**What to check:**
```sql
SELECT namespace, COUNT(*)
FROM memories
GROUP BY namespace;
```

**Expected:** Known namespaces with reasonable counts

**If unexpected namespaces or zero counts in expected namespaces:**
```
⚠️  NAMESPACE ANOMALY DETECTED
Expected namespaces: [list]
Found: [actual list]

Missing or empty: [namespace]
Unexpected: [unknown namespace]

This means:
- Capture process is misconfigured
- Namespace tags are being corrupted
- Data migration incomplete

→ Notify developer: "Namespace configuration mismatch. Check capture tagging logic."
```

---

## Auto-Fix Attempts

### For Vectorization Backlog

**Attempt:**
```sql
-- Trigger manual vectorization if backlog detected
SELECT ai.schedule_vectorizer_job('memories_embedding');
```

**Report:**
```
🔧 AUTO-FIX ATTEMPTED
Triggered manual vectorization job.
Monitor backlog in next check cycle.
```

### For Stale Connections

**Attempt:**
```python
# Reconnect to database
try:
    conn.close()
    conn = reconnect_to_db()
    report("🔧 AUTO-FIX: Database connection reset")
except:
    report("❌ AUTO-FIX FAILED: Could not reconnect to database")
```

---

## Error Notification Format

### To User (Non-Technical)

```
⚠️  Memory System Notice

Your AI's memory system detected an issue:
[Simple explanation of what's wrong]

Impact: [How this affects their experience]

Action needed: [What they should do, if anything]

If this persists, contact support with error code: [CODE]
```

### To Developer (Technical)

```
❌ MEMORY INTEGRITY CHECK FAILED

Check: [specific check name]
Expected: [what should be true]
Found: [what was actually found]
Timestamp: [when detected]

Diagnostic query:
[SQL or command that detected the issue]

Suggested actions:
1. [First thing to check]
2. [Second thing to check]
3. [Escalation path]

Error code: [CODE]
```

---

## Diagnostic Error Codes

| Code | Issue | Severity |
|------|-------|----------|
| `EMBED-DIM-001` | Dimension mismatch | CRITICAL |
| `MEM-CAP-001` | Capture stopped | CRITICAL |
| `VEC-LAG-001` | Vectorization backlog | WARNING |
| `DUP-ENT-001` | Duplicate entries | WARNING |
| `EMBED-FAIL-001` | Search returning garbage | CRITICAL |
| `NS-ANOM-001` | Namespace corruption | WARNING |
| `DB-CONN-001` | Database connection lost | CRITICAL |

---

## Health Check Trigger Conditions

**Run full diagnostic when:**
- Every 30 minutes (scheduled)
- After system restart
- User reports search not working
- Memory query returns unexpectedly low results
- Any database error occurs

---

## Example Implementation

```python
def check_memory_health():
    issues = []

    # Check 1: Embedding dimensions
    dim = query_db("SELECT embedding_dimensions FROM ai.vectorizer WHERE table_name='memories_embedding'")
    if dim != EXPECTED_DIM:
        issues.append({
            'code': 'EMBED-DIM-001',
            'severity': 'CRITICAL',
            'message': f'Dimension mismatch: expected {EXPECTED_DIM}, found {dim}',
            'user_message': 'Memory search configuration issue detected.',
            'dev_message': f'Embedding dimension mismatch. Vectorizer shows {dim} but expected {EXPECTED_DIM}.'
        })

    # Check 2: Recent captures
    recent_count = query_db("SELECT COUNT(*) FROM memories WHERE created_at >= NOW() - INTERVAL '30 minutes'")
    if recent_count == 0 and conversation_is_active():
        issues.append({
            'code': 'MEM-CAP-001',
            'severity': 'CRITICAL',
            'message': 'No memories captured in last 30 minutes',
            'user_message': 'Your conversation may not be saving. Recent messages might be lost.',
            'dev_message': 'Memory capture process appears to have stopped. Check scripty/capture service.'
        })

    # ... more checks

    # Report issues
    for issue in issues:
        if issue['severity'] == 'CRITICAL':
            notify_user(issue['user_message'])
            notify_developer(issue['dev_message'], issue['code'])
        else:
            log_warning(issue['message'], issue['code'])

    return len(issues) == 0  # True if healthy
```

---

## What This Accomplishes

1. **Automatic detection** of memory corruption
2. **Clear reporting** to user (non-technical) and developer (technical)
3. **Auto-fix attempts** where possible
4. **Error codes** for tracking and debugging
5. **No philosophy** - pure technical health monitoring

**This is system diagnostics, not operational doctrine.**

---

END OF DIAGNOSTIC GUIDE
