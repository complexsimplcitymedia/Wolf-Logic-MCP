# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-13

### Added
- Initial release of Wolf Logic MCP Memory Server
- Core memory storage module with context and tag indexing
- 8 comprehensive MCP tools for memory management:
  - `store_memory` - Store new memories with context, tags, and metadata
  - `retrieve_memory` - Retrieve specific memories by ID
  - `search_by_context` - Search memories by context with relevance scoring
  - `search_by_tags` - Search memories by tags with relevance scoring
  - `list_memories` - List all memories sorted by recency
  - `delete_memory` - Delete specific memories
  - `clear_all_memories` - Clear all stored memories
  - `get_memory_stats` - Get memory storage statistics
- Relevance scoring algorithm based on context match and recency
- TypeScript implementation with full type safety
- MCP SDK integration with stdio transport
- Mobile-ready architecture for Android integration
- Comprehensive documentation:
  - README with features and usage
  - API documentation with detailed examples
  - Integration examples for Node.js and Android
  - MCP client configuration example
- MIT License
- Build tooling with TypeScript compiler
- .gitignore configuration for Node.js/TypeScript projects

### Features
- Indefinite memory retention (memories persist until explicitly deleted)
- Context-based organization and search
- Tag-based categorization and search
- Custom metadata support for flexible data storage
- Automatic indexing for fast retrieval
- Recency-based relevance boosting
- Statistics tracking for contexts, tags, and total memories

[1.0.0]: https://github.com/complexsimplcitymedia/Wolf-Logic-MCP/releases/tag/v1.0.0
