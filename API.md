# API Documentation

## Wolf Logic MCP Memory Server API

### Overview

Wolf Logic MCP provides a comprehensive memory management API through the Model Context Protocol. All tools return JSON responses with a consistent structure.

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description"
}
```

## Tools Reference

### store_memory

**Description**: Store a new memory entry with content, context, and optional metadata/tags.

**Input Schema**:
```json
{
  "content": "string (required)",
  "context": "string (required)",
  "metadata": "object (optional)",
  "tags": "array of strings (optional)"
}
```

**Example**:
```json
{
  "content": "User completed onboarding tutorial",
  "context": "app_usage",
  "metadata": {
    "completion_time": "2025-11-13T10:30:00Z",
    "duration_seconds": 120
  },
  "tags": ["onboarding", "milestone"]
}
```

**Response**:
```json
{
  "success": true,
  "id": "mem_1731485400_xyz789",
  "message": "Memory stored successfully"
}
```

---

### retrieve_memory

**Description**: Retrieve a specific memory by its unique ID.

**Input Schema**:
```json
{
  "id": "string (required)"
}
```

**Example**:
```json
{
  "id": "mem_1731485400_xyz789"
}
```

**Response**:
```json
{
  "success": true,
  "memory": {
    "id": "mem_1731485400_xyz789",
    "content": "User completed onboarding tutorial",
    "context": "app_usage",
    "timestamp": 1731485400000,
    "metadata": {
      "completion_time": "2025-11-13T10:30:00Z",
      "duration_seconds": 120
    },
    "tags": ["onboarding", "milestone"]
  }
}
```

---

### search_by_context

**Description**: Search for memories by context with relevance scoring.

**Input Schema**:
```json
{
  "context": "string (required)",
  "limit": "number (optional, default: 10)"
}
```

**Example**:
```json
{
  "context": "app_usage",
  "limit": 5
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "entry": {
        "id": "mem_1731485400_xyz789",
        "content": "User completed onboarding tutorial",
        "context": "app_usage",
        "timestamp": 1731485400000,
        "tags": ["onboarding", "milestone"]
      },
      "relevanceScore": 1.95
    }
  ],
  "count": 1
}
```

**Relevance Scoring**:
- Exact context match: +1.0
- Recency boost: 0-1.0 (based on age, max 30 days)
- Higher scores appear first in results

---

### search_by_tags

**Description**: Search for memories by tags with relevance scoring.

**Input Schema**:
```json
{
  "tags": "array of strings (required)",
  "limit": "number (optional, default: 10)"
}
```

**Example**:
```json
{
  "tags": ["onboarding", "milestone"],
  "limit": 10
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "entry": {
        "id": "mem_1731485400_xyz789",
        "content": "User completed onboarding tutorial",
        "context": "app_usage",
        "timestamp": 1731485400000,
        "tags": ["onboarding", "milestone"]
      },
      "relevanceScore": 1.15
    }
  ],
  "count": 1
}
```

**Relevance Scoring**:
- Tag match ratio: 0-1.0 (matching tags / search tags)
- Recency boost: 0-0.2 (based on age)
- Higher scores appear first in results

---

### list_memories

**Description**: List all stored memories, sorted by most recent.

**Input Schema**:
```json
{
  "limit": "number (optional, default: 50)"
}
```

**Example**:
```json
{
  "limit": 20
}
```

**Response**:
```json
{
  "success": true,
  "memories": [
    {
      "id": "mem_1731485400_xyz789",
      "content": "User completed onboarding tutorial",
      "context": "app_usage",
      "timestamp": 1731485400000,
      "tags": ["onboarding", "milestone"]
    }
  ],
  "count": 1
}
```

---

### delete_memory

**Description**: Delete a specific memory by its ID.

**Input Schema**:
```json
{
  "id": "string (required)"
}
```

**Example**:
```json
{
  "id": "mem_1731485400_xyz789"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "message": "Memory deleted successfully"
}
```

**Response (Not Found)**:
```json
{
  "success": false,
  "error": "Memory not found"
}
```

---

### clear_all_memories

**Description**: Clear all stored memories. Use with caution as this operation cannot be undone.

**Input Schema**:
```json
{}
```

**Example**:
```json
{}
```

**Response**:
```json
{
  "success": true,
  "message": "All memories cleared"
}
```

---

### get_memory_stats

**Description**: Get statistics about the memory storage system.

**Input Schema**:
```json
{}
```

**Example**:
```json
{}
```

**Response**:
```json
{
  "success": true,
  "stats": {
    "total": 42,
    "contexts": 8,
    "tags": 15
  }
}
```

**Stats Explanation**:
- `total`: Total number of stored memories
- `contexts`: Number of unique contexts
- `tags`: Number of unique tags

---

## Best Practices

### Memory Storage
- Use descriptive contexts that group related memories
- Add relevant tags for cross-cutting concerns
- Include metadata for additional filtering capabilities
- Keep content concise but informative

### Search Optimization
- Use context search for category-based queries
- Use tag search for cross-category queries
- Adjust limits based on your use case
- Leverage relevance scores to prioritize results

### Memory Management
- Regularly review and clean up old memories
- Use specific contexts to organize memories
- Delete individual memories rather than clearing all when possible
- Monitor stats to understand storage patterns

---

## Example Workflows

### Workflow 1: User Preference Management

```javascript
// 1. Store user preference
store_memory({
  content: "User prefers notifications at 9 AM",
  context: "user_preferences",
  tags: ["notifications", "settings"],
  metadata: { updated_at: "2025-11-13" }
})

// 2. Retrieve preferences
search_by_context({
  context: "user_preferences",
  limit: 10
})

// 3. Update preference (store new, delete old)
delete_memory({ id: "old_preference_id" })
store_memory({ 
  content: "User prefers notifications at 10 AM",
  context: "user_preferences"
})
```

### Workflow 2: Learning Progress Tracking

```javascript
// 1. Store learning milestone
store_memory({
  content: "Completed Python basics course",
  context: "learning_progress",
  tags: ["python", "course", "completed"],
  metadata: { 
    course_id: "py101",
    score: 95,
    duration_hours: 12
  }
})

// 2. Find all Python-related learning
search_by_tags({
  tags: ["python"],
  limit: 20
})

// 3. Get overall learning stats
get_memory_stats()
```

### Workflow 3: Conversation History

```javascript
// 1. Store conversation entry
store_memory({
  content: "User asked about weather in Tokyo",
  context: "conversation_history",
  tags: ["weather", "location"],
  metadata: {
    user_id: "user123",
    session_id: "session456"
  }
})

// 2. Retrieve recent conversations
list_memories({ limit: 10 })

// 3. Search by topic
search_by_tags({
  tags: ["weather"],
  limit: 5
})
```

---

## Integration Examples

### Node.js Client

```javascript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";

const client = new Client({
  name: "my-app",
  version: "1.0.0"
});

// Store a memory
const result = await client.callTool({
  name: "store_memory",
  arguments: {
    content: "Important information",
    context: "app_data",
    tags: ["important"]
  }
});

console.log(result);
```

### Android Integration Concept

```kotlin
// Pseudo-code for Android integration
class MemoryManager(private val mcpBridge: MCPBridge) {
    
    suspend fun storeMemory(
        content: String,
        context: String,
        tags: List<String>? = null
    ): String {
        val result = mcpBridge.callTool(
            "store_memory",
            mapOf(
                "content" to content,
                "context" to context,
                "tags" to tags
            )
        )
        return result.getString("id")
    }
    
    suspend fun searchByContext(
        context: String,
        limit: Int = 10
    ): List<Memory> {
        val result = mcpBridge.callTool(
            "search_by_context",
            mapOf(
                "context" to context,
                "limit" to limit
            )
        )
        return parseMemories(result)
    }
}
```

---

For more information, see the main [README](./README.md).
