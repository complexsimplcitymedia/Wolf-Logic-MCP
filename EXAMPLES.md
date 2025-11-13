# Examples

This directory contains example integrations and use cases for Wolf Logic MCP.

## Example 1: Basic Memory Storage

```javascript
// Example of storing and retrieving memories

// Store a user preference
const storeResult = await callTool({
  name: "store_memory",
  arguments: {
    content: "User prefers dark mode",
    context: "ui_preferences",
    tags: ["theme", "ui"],
    metadata: {
      app_version: "1.0.0",
      platform: "android"
    }
  }
});

console.log("Stored memory ID:", storeResult.id);

// Retrieve the memory
const retrieveResult = await callTool({
  name: "retrieve_memory",
  arguments: {
    id: storeResult.id
  }
});

console.log("Retrieved memory:", retrieveResult.memory);
```

## Example 2: Context-based Search

```javascript
// Store multiple memories in the same context
await callTool({
  name: "store_memory",
  arguments: {
    content: "User completed tutorial step 1",
    context: "tutorial_progress",
    tags: ["tutorial", "progress"]
  }
});

await callTool({
  name: "store_memory",
  arguments: {
    content: "User completed tutorial step 2",
    context: "tutorial_progress",
    tags: ["tutorial", "progress"]
  }
});

// Search all tutorial progress
const searchResult = await callTool({
  name: "search_by_context",
  arguments: {
    context: "tutorial_progress",
    limit: 10
  }
});

console.log("Found", searchResult.count, "tutorial memories");
searchResult.results.forEach(result => {
  console.log("- ", result.entry.content, "(score:", result.relevanceScore, ")");
});
```

## Example 3: Tag-based Organization

```javascript
// Store memories with multiple tags
await callTool({
  name: "store_memory",
  arguments: {
    content: "User likes action games",
    context: "user_interests",
    tags: ["gaming", "preferences", "action"]
  }
});

await callTool({
  name: "store_memory",
  arguments: {
    content: "User plays FPS games regularly",
    context: "gaming_habits",
    tags: ["gaming", "fps", "action"]
  }
});

// Find all gaming-related memories
const gamingMemories = await callTool({
  name: "search_by_tags",
  arguments: {
    tags: ["gaming", "action"],
    limit: 10
  }
});

console.log("Gaming memories:", gamingMemories.results.length);
```

## Example 4: Memory Management

```javascript
// Get current statistics
const stats = await callTool({
  name: "get_memory_stats",
  arguments: {}
});

console.log("Memory Statistics:");
console.log("- Total memories:", stats.stats.total);
console.log("- Unique contexts:", stats.stats.contexts);
console.log("- Unique tags:", stats.stats.tags);

// List recent memories
const recent = await callTool({
  name: "list_memories",
  arguments: { limit: 5 }
});

console.log("\nRecent memories:");
recent.memories.forEach(mem => {
  console.log("-", mem.content, "(" + new Date(mem.timestamp).toISOString() + ")");
});

// Delete a specific memory
if (recent.memories.length > 0) {
  await callTool({
    name: "delete_memory",
    arguments: {
      id: recent.memories[0].id
    }
  });
  console.log("\nDeleted oldest memory");
}
```

## Example 5: Conversation History

```javascript
// Store conversation turns
async function storeConversation(userMessage, aiResponse, sessionId) {
  await callTool({
    name: "store_memory",
    arguments: {
      content: `User: ${userMessage}\nAI: ${aiResponse}`,
      context: "conversation_history",
      tags: ["conversation", sessionId],
      metadata: {
        session_id: sessionId,
        timestamp: new Date().toISOString()
      }
    }
  });
}

// Store a conversation
await storeConversation(
  "What's the weather like?",
  "I can help you check the weather. Where are you located?",
  "session_123"
);

// Retrieve conversation history for a session
const history = await callTool({
  name: "search_by_tags",
  arguments: {
    tags: ["session_123"],
    limit: 20
  }
});

console.log("Conversation history:");
history.results.forEach(result => {
  console.log(result.entry.content);
  console.log("---");
});
```

## Example 6: Learning Progress Tracker

```javascript
// Track learning milestones
async function trackLearning(course, lesson, score, completionTime) {
  await callTool({
    name: "store_memory",
    arguments: {
      content: `Completed ${lesson} in ${course} with score ${score}%`,
      context: "learning_progress",
      tags: ["learning", course, "completed"],
      metadata: {
        course: course,
        lesson: lesson,
        score: score,
        completion_time: completionTime,
        date: new Date().toISOString()
      }
    }
  });
}

// Record some learning
await trackLearning("Python Basics", "Variables and Types", 95, 45);
await trackLearning("Python Basics", "Control Flow", 88, 60);
await trackLearning("Python Basics", "Functions", 92, 75);

// Get all Python learning progress
const pythonProgress = await callTool({
  name: "search_by_tags",
  arguments: {
    tags: ["Python Basics"],
    limit: 20
  }
});

console.log("Python Learning Progress:");
pythonProgress.results.forEach(result => {
  const meta = result.entry.metadata;
  console.log(`- ${meta.lesson}: ${meta.score}% (${meta.completion_time} min)`);
});
```

## Example 7: User Preferences System

```javascript
// Manage user preferences
class PreferenceManager {
  async setPreference(key, value, category) {
    // Delete old preference if exists
    const existing = await callTool({
      name: "search_by_tags",
      arguments: {
        tags: [category, key]
      }
    });
    
    if (existing.results.length > 0) {
      await callTool({
        name: "delete_memory",
        arguments: {
          id: existing.results[0].entry.id
        }
      });
    }
    
    // Store new preference
    return await callTool({
      name: "store_memory",
      arguments: {
        content: `${key}: ${value}`,
        context: "user_preferences",
        tags: ["preference", category, key],
        metadata: {
          key: key,
          value: value,
          category: category,
          updated: new Date().toISOString()
        }
      }
    });
  }
  
  async getPreference(key) {
    const result = await callTool({
      name: "search_by_tags",
      arguments: {
        tags: ["preference", key],
        limit: 1
      }
    });
    
    if (result.results.length > 0) {
      return result.results[0].entry.metadata.value;
    }
    return null;
  }
  
  async getAllPreferences(category) {
    const result = await callTool({
      name: "search_by_tags",
      arguments: {
        tags: ["preference", category],
        limit: 100
      }
    });
    
    const prefs = {};
    result.results.forEach(r => {
      const meta = r.entry.metadata;
      prefs[meta.key] = meta.value;
    });
    
    return prefs;
  }
}

// Usage
const prefManager = new PreferenceManager();
await prefManager.setPreference("theme", "dark", "ui");
await prefManager.setPreference("language", "en", "ui");
await prefManager.setPreference("notifications", true, "system");

const theme = await prefManager.getPreference("theme");
console.log("Current theme:", theme);

const uiPrefs = await prefManager.getAllPreferences("ui");
console.log("UI Preferences:", uiPrefs);
```

## Example 8: Health & Wellness Tracker

```javascript
// Track health metrics over time
async function logHealthMetric(metric, value, unit) {
  await callTool({
    name: "store_memory",
    arguments: {
      content: `${metric}: ${value} ${unit}`,
      context: "health_metrics",
      tags: ["health", metric],
      metadata: {
        metric: metric,
        value: value,
        unit: unit,
        timestamp: new Date().toISOString()
      }
    }
  });
}

// Log some health data
await logHealthMetric("steps", 8500, "steps");
await logHealthMetric("water", 2.5, "liters");
await logHealthMetric("sleep", 7.5, "hours");

// Get recent steps data
const stepsData = await callTool({
  name: "search_by_tags",
  arguments: {
    tags: ["steps"],
    limit: 7  // Last 7 days
  }
});

console.log("Steps history:");
stepsData.results.forEach(result => {
  const meta = result.entry.metadata;
  const date = new Date(meta.timestamp).toLocaleDateString();
  console.log(`${date}: ${meta.value} ${meta.unit}`);
});
```

## Android Integration Example

```kotlin
// Kotlin Android example
class MemoryService(private val mcpClient: MCPClient) {
    
    suspend fun storeMemory(
        content: String,
        context: String,
        tags: List<String> = emptyList(),
        metadata: Map<String, Any> = emptyMap()
    ): String {
        val result = mcpClient.callTool(
            "store_memory",
            mapOf(
                "content" to content,
                "context" to context,
                "tags" to tags,
                "metadata" to metadata
            )
        )
        return result.getString("id")
    }
    
    suspend fun searchByContext(
        context: String,
        limit: Int = 10
    ): List<Memory> {
        val result = mcpClient.callTool(
            "search_by_context",
            mapOf(
                "context" to context,
                "limit" to limit
            )
        )
        return parseMemories(result.getJSONArray("results"))
    }
    
    suspend fun getStats(): MemoryStats {
        val result = mcpClient.callTool("get_memory_stats", emptyMap())
        val stats = result.getJSONObject("stats")
        return MemoryStats(
            total = stats.getInt("total"),
            contexts = stats.getInt("contexts"),
            tags = stats.getInt("tags")
        )
    }
}

// Usage in Android Activity/Fragment
class MainActivity : AppCompatActivity() {
    private lateinit var memoryService: MemoryService
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        lifecycleScope.launch {
            // Store user action
            memoryService.storeMemory(
                content = "User opened settings",
                context = "user_activity",
                tags = listOf("activity", "settings")
            )
            
            // Get recent activities
            val activities = memoryService.searchByContext("user_activity", 10)
            activities.forEach { memory ->
                Log.d("Memory", memory.content)
            }
        }
    }
}
```

## Testing Examples

For testing the server, you can use a simple test script:

```javascript
// test-memory-server.js
import { spawn } from 'child_process';

// Start the server
const server = spawn('node', ['dist/index.js']);

// Send MCP request
const request = {
  jsonrpc: "2.0",
  id: 1,
  method: "tools/call",
  params: {
    name: "store_memory",
    arguments: {
      content: "Test memory",
      context: "test",
      tags: ["test"]
    }
  }
};

server.stdin.write(JSON.stringify(request) + '\n');

server.stdout.on('data', (data) => {
  console.log('Response:', data.toString());
});

setTimeout(() => {
  server.kill();
}, 1000);
```
