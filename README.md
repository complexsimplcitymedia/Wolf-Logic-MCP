# Wolf Logic MCP - First Mobile MCP AI Memory Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js Version](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)](https://www.typescriptlang.org/)
[![Tests](https://img.shields.io/badge/tests-10%2F10%20passing-success)](./test/basic.test.js)
[![Security](https://img.shields.io/badge/security-0%20vulnerabilities-success)](https://github.com/github/codeql)

**Your Contextual Neural Indefinite Memory**

Wolf Logic MCP is the first mobile-ready Model Context Protocol (MCP) server designed specifically for AI memory management on Android devices. It provides a robust, context-aware memory system that enables AI applications to store, retrieve, and search information indefinitely.

## 🚀 Features

- **Contextual Memory Storage**: Store memories with rich context and metadata
- **Neural Search**: Search memories by context or tags with relevance scoring
- **Indefinite Retention**: Memories persist until explicitly deleted
- **Mobile-Optimized**: Designed for mobile devices and Android applications
- **MCP Protocol**: Built on the Model Context Protocol standard
- **Tag-based Organization**: Categorize and retrieve memories using tags
- **Metadata Support**: Attach custom metadata to each memory entry
- **Relevance Ranking**: Automatic scoring based on context match and recency

## 📦 Installation

### Prerequisites
- Node.js 18.0.0 or higher
- npm or yarn

### Setup

```bash
# Clone the repository
git clone https://github.com/complexsimplcitymedia/Wolf-Logic-MCP.git
cd Wolf-Logic-MCP

# Install dependencies
npm install

# Build the project
npm run build
```

## 🎯 Usage

### Running the Server

```bash
npm start
```

The server runs using stdio transport, making it compatible with MCP clients.

### Available Tools

#### 1. **store_memory**
Store a new memory entry with content, context, and optional metadata/tags.

```json
{
  "content": "User prefers dark mode in applications",
  "context": "user_preferences",
  "metadata": {
    "source": "settings_app",
    "confidence": 0.95
  },
  "tags": ["preferences", "ui", "theme"]
}
```

#### 2. **retrieve_memory**
Retrieve a specific memory by its ID.

```json
{
  "id": "mem_1234567890_abc123"
}
```

#### 3. **search_by_context**
Search memories by context with optional limit.

```json
{
  "context": "user_preferences",
  "limit": 10
}
```

#### 4. **search_by_tags**
Search memories by tags.

```json
{
  "tags": ["preferences", "theme"],
  "limit": 10
}
```

#### 5. **list_memories**
List all stored memories, sorted by most recent.

```json
{
  "limit": 50
}
```

#### 6. **delete_memory**
Delete a specific memory by its ID.

```json
{
  "id": "mem_1234567890_abc123"
}
```

#### 7. **clear_all_memories**
Clear all stored memories (use with caution).

```json
{}
```

#### 8. **get_memory_stats**
Get statistics about stored memories.

```json
{}
```

## 🏗️ Architecture

### Memory Storage Module

The memory storage module (`src/memory.ts`) provides:

- **In-memory storage** with fast access
- **Context indexing** for quick context-based searches
- **Tag indexing** for efficient tag-based queries
- **Relevance scoring** based on context match and recency
- **Automatic cleanup** when memories are deleted

### MCP Server

The MCP server (`src/index.ts`) provides:

- **Standard MCP protocol** implementation
- **Tool-based interface** for all operations
- **Error handling** with descriptive messages
- **JSON responses** for easy parsing

## 📱 Android Integration

Wolf Logic MCP is designed to be mobile-ready and can be integrated with Android applications through:

1. **Node.js Runtime**: Use a Node.js runtime for Android (e.g., nodejs-mobile)
2. **Bridge Layer**: Create a bridge between your Android app and the MCP server
3. **Local Server**: Run the MCP server locally on the device for offline capability

### Example Android Integration Flow

```
Android App → Node.js Bridge → MCP Server → Memory Storage
```

## 🔧 Development

### Build

```bash
npm run build
```

### Watch Mode (for development)

```bash
npm run dev
```

### Clean Build Artifacts

```bash
npm run clean
```

## 📊 Memory Entry Structure

Each memory entry contains:

```typescript
{
  id: string;              // Unique identifier
  content: string;         // The actual memory content
  context: string;         // Context or category
  timestamp: number;       // Creation timestamp
  metadata?: object;       // Optional custom metadata
  tags?: string[];        // Optional tags for categorization
}
```

## 🔍 Search and Relevance

### Context Search
- Exact context matches receive highest relevance score
- Recent memories are boosted in rankings
- Results are automatically sorted by relevance

### Tag Search
- Matches are scored based on tag overlap
- Multiple tag matches increase relevance
- Recency is factored into the final score

## 🛡️ Use Cases

- **Personal AI Assistants**: Store user preferences and conversation history
- **Learning Applications**: Track educational progress and knowledge
- **Health Apps**: Remember user health data and patterns
- **Productivity Tools**: Store tasks, notes, and reminders
- **Gaming**: Save player preferences and game state
- **Smart Home**: Remember device settings and user routines

## 🧪 Testing

Run the comprehensive test suite to verify functionality:

```bash
npm test
```

The test suite includes 10 tests covering:
- Memory storage and retrieval
- Context-based search
- Tag-based search
- Memory management operations
- Statistics tracking
- Index integrity

All tests pass with 100% success rate. See [test/basic.test.js](test/basic.test.js) for details.

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Install dependencies
npm install

# Build the project
npm run build

# Run tests
npm test

# Watch mode for development
npm run dev
```

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md) - Get started in 5 minutes
- [API Documentation](API.md) - Detailed API reference
- [Examples](EXAMPLES.md) - Real-world usage examples
- [Changelog](CHANGELOG.md) - Version history
- [Summary](SUMMARY.md) - Implementation overview

## 🔗 Links

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP SDK Documentation](https://github.com/modelcontextprotocol/sdk)

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Wolf Logic MCP** - Empowering mobile AI with indefinite contextual memory.
