# Quick Start Guide

Get started with Wolf Logic MCP Memory Server in 5 minutes!

## Installation

```bash
# Clone the repository
git clone https://github.com/complexsimplcitymedia/Wolf-Logic-MCP.git
cd Wolf-Logic-MCP

# Install dependencies
npm install

# Build the project
npm run build
```

## Running Tests

```bash
npm test
```

## Using the Server

### Option 1: Run Directly

```bash
npm start
```

The server runs on stdio transport and waits for MCP protocol messages.

### Option 2: Configure with an MCP Client

Create or edit your MCP client configuration file (e.g., `~/.mcp/config.json`):

```json
{
  "mcpServers": {
    "wolf-logic-mcp": {
      "command": "node",
      "args": ["/absolute/path/to/Wolf-Logic-MCP/dist/index.js"]
    }
  }
}
```

## Basic Usage Examples

Once connected to an MCP client, you can use the following tools:

### Store a Memory

```json
{
  "name": "store_memory",
  "arguments": {
    "content": "User prefers dark mode",
    "context": "user_preferences",
    "tags": ["ui", "theme"]
  }
}
```

### Search by Context

```json
{
  "name": "search_by_context",
  "arguments": {
    "context": "user_preferences",
    "limit": 10
  }
}
```

### Get Statistics

```json
{
  "name": "get_memory_stats",
  "arguments": {}
}
```

## Next Steps

- Read the [full API documentation](API.md)
- Check out [usage examples](EXAMPLES.md)
- See the [complete README](README.md)

## Troubleshooting

### Server won't start
- Ensure Node.js 18+ is installed: `node --version`
- Check that dependencies are installed: `npm install`
- Verify the build succeeded: `npm run build`

### MCP client can't connect
- Verify the absolute path to `dist/index.js` in your config
- Check that the server binary is executable: `chmod +x dist/index.js`
- Look for error messages in the client logs

### Memory not persisting
- Note: The current version uses in-memory storage
- Memories are lost when the server restarts
- For persistent storage, consider implementing a database backend

## Getting Help

- Open an issue on [GitHub](https://github.com/complexsimplcitymedia/Wolf-Logic-MCP/issues)
- Read the documentation in this repository
- Check the [MCP SDK documentation](https://github.com/modelcontextprotocol/sdk)

Happy coding! 🚀
