#!/usr/bin/env node

/**
 * Wolf Logic MCP - First Mobile MCP AI Memory Server
 * Provides contextual neural indefinite memory for AI applications
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { MemoryStorage } from "./memory.js";

// Initialize memory storage
const memoryStorage = new MemoryStorage();

// Define available tools
const TOOLS: Tool[] = [
  {
    name: "store_memory",
    description: "Store a new memory entry with content, context, and optional metadata/tags",
    inputSchema: {
      type: "object",
      properties: {
        content: {
          type: "string",
          description: "The content to store in memory",
        },
        context: {
          type: "string",
          description: "The context or category for this memory",
        },
        metadata: {
          type: "object",
          description: "Optional metadata as key-value pairs",
        },
        tags: {
          type: "array",
          items: { type: "string" },
          description: "Optional tags for categorization",
        },
      },
      required: ["content", "context"],
    },
  },
  {
    name: "retrieve_memory",
    description: "Retrieve a specific memory by its ID",
    inputSchema: {
      type: "object",
      properties: {
        id: {
          type: "string",
          description: "The unique identifier of the memory to retrieve",
        },
      },
      required: ["id"],
    },
  },
  {
    name: "search_by_context",
    description: "Search memories by context",
    inputSchema: {
      type: "object",
      properties: {
        context: {
          type: "string",
          description: "The context to search for",
        },
        limit: {
          type: "number",
          description: "Maximum number of results to return (default: 10)",
          default: 10,
        },
      },
      required: ["context"],
    },
  },
  {
    name: "search_by_tags",
    description: "Search memories by tags",
    inputSchema: {
      type: "object",
      properties: {
        tags: {
          type: "array",
          items: { type: "string" },
          description: "Array of tags to search for",
        },
        limit: {
          type: "number",
          description: "Maximum number of results to return (default: 10)",
          default: 10,
        },
      },
      required: ["tags"],
    },
  },
  {
    name: "list_memories",
    description: "List all stored memories, sorted by most recent",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum number of memories to return (default: 50)",
          default: 50,
        },
      },
    },
  },
  {
    name: "delete_memory",
    description: "Delete a specific memory by its ID",
    inputSchema: {
      type: "object",
      properties: {
        id: {
          type: "string",
          description: "The unique identifier of the memory to delete",
        },
      },
      required: ["id"],
    },
  },
  {
    name: "clear_all_memories",
    description: "Clear all stored memories (use with caution)",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "get_memory_stats",
    description: "Get statistics about stored memories",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
];

// Create MCP server
const server = new Server(
  {
    name: "wolf-logic-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Handle tool listing
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS,
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "store_memory": {
        const { content, context, metadata, tags } = args as {
          content: string;
          context: string;
          metadata?: Record<string, any>;
          tags?: string[];
        };
        const id = await memoryStorage.store(content, context, metadata, tags);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ success: true, id, message: "Memory stored successfully" }, null, 2),
            },
          ],
        };
      }

      case "retrieve_memory": {
        const { id } = args as { id: string };
        const memory = await memoryStorage.retrieve(id);
        if (!memory) {
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({ success: false, error: "Memory not found" }, null, 2),
              },
            ],
          };
        }
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ success: true, memory }, null, 2),
            },
          ],
        };
      }

      case "search_by_context": {
        const { context, limit = 10 } = args as { context: string; limit?: number };
        const results = await memoryStorage.searchByContext(context, limit);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ success: true, results, count: results.length }, null, 2),
            },
          ],
        };
      }

      case "search_by_tags": {
        const { tags, limit = 10 } = args as { tags: string[]; limit?: number };
        const results = await memoryStorage.searchByTags(tags, limit);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ success: true, results, count: results.length }, null, 2),
            },
          ],
        };
      }

      case "list_memories": {
        const { limit = 50 } = args as { limit?: number };
        const memories = await memoryStorage.listAll(limit);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ success: true, memories, count: memories.length }, null, 2),
            },
          ],
        };
      }

      case "delete_memory": {
        const { id } = args as { id: string };
        const deleted = await memoryStorage.delete(id);
        if (!deleted) {
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({ success: false, error: "Memory not found" }, null, 2),
              },
            ],
          };
        }
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ success: true, message: "Memory deleted successfully" }, null, 2),
            },
          ],
        };
      }

      case "clear_all_memories": {
        await memoryStorage.clear();
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ success: true, message: "All memories cleared" }, null, 2),
            },
          ],
        };
      }

      case "get_memory_stats": {
        const stats = memoryStorage.getStats();
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ success: true, stats }, null, 2),
            },
          ],
        };
      }

      default:
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ success: false, error: `Unknown tool: ${name}` }, null, 2),
            },
          ],
          isError: true,
        };
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            success: false,
            error: error instanceof Error ? error.message : String(error),
          }, null, 2),
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Wolf Logic MCP Memory Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
