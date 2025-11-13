/**
 * Memory Storage Module
 * Handles contextual neural indefinite memory storage and retrieval
 */

export interface MemoryEntry {
  id: string;
  content: string;
  context: string;
  timestamp: number;
  metadata?: Record<string, any>;
  tags?: string[];
}

export interface MemorySearchResult {
  entry: MemoryEntry;
  relevanceScore: number;
}

export class MemoryStorage {
  private memories: Map<string, MemoryEntry>;
  private contextIndex: Map<string, Set<string>>;
  private tagIndex: Map<string, Set<string>>;

  constructor() {
    this.memories = new Map();
    this.contextIndex = new Map();
    this.tagIndex = new Map();
  }

  /**
   * Store a new memory entry
   */
  async store(content: string, context: string, metadata?: Record<string, any>, tags?: string[]): Promise<string> {
    const id = this.generateId();
    const entry: MemoryEntry = {
      id,
      content,
      context,
      timestamp: Date.now(),
      metadata,
      tags,
    };

    this.memories.set(id, entry);
    this.indexEntry(entry);

    return id;
  }

  /**
   * Retrieve a memory by ID
   */
  async retrieve(id: string): Promise<MemoryEntry | null> {
    return this.memories.get(id) || null;
  }

  /**
   * Search memories by context
   */
  async searchByContext(context: string, limit: number = 10): Promise<MemorySearchResult[]> {
    const memoryIds = this.contextIndex.get(context) || new Set();
    const results: MemorySearchResult[] = [];

    for (const id of memoryIds) {
      const entry = this.memories.get(id);
      if (entry) {
        results.push({
          entry,
          relevanceScore: this.calculateRelevance(entry, context),
        });
      }
    }

    return results
      .sort((a, b) => b.relevanceScore - a.relevanceScore)
      .slice(0, limit);
  }

  /**
   * Search memories by tags
   */
  async searchByTags(tags: string[], limit: number = 10): Promise<MemorySearchResult[]> {
    const memoryIds = new Set<string>();

    for (const tag of tags) {
      const ids = this.tagIndex.get(tag);
      if (ids) {
        ids.forEach(id => memoryIds.add(id));
      }
    }

    const results: MemorySearchResult[] = [];
    for (const id of memoryIds) {
      const entry = this.memories.get(id);
      if (entry) {
        results.push({
          entry,
          relevanceScore: this.calculateTagRelevance(entry, tags),
        });
      }
    }

    return results
      .sort((a, b) => b.relevanceScore - a.relevanceScore)
      .slice(0, limit);
  }

  /**
   * Get all memories (for listing)
   */
  async listAll(limit: number = 50): Promise<MemoryEntry[]> {
    const entries = Array.from(this.memories.values());
    return entries
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit);
  }

  /**
   * Delete a memory entry
   */
  async delete(id: string): Promise<boolean> {
    const entry = this.memories.get(id);
    if (!entry) {
      return false;
    }

    this.memories.delete(id);
    this.removeFromIndex(entry);
    return true;
  }

  /**
   * Clear all memories
   */
  async clear(): Promise<void> {
    this.memories.clear();
    this.contextIndex.clear();
    this.tagIndex.clear();
  }

  /**
   * Get memory statistics
   */
  getStats(): { total: number; contexts: number; tags: number } {
    return {
      total: this.memories.size,
      contexts: this.contextIndex.size,
      tags: this.tagIndex.size,
    };
  }

  private generateId(): string {
    return `mem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private indexEntry(entry: MemoryEntry): void {
    // Index by context
    if (!this.contextIndex.has(entry.context)) {
      this.contextIndex.set(entry.context, new Set());
    }
    this.contextIndex.get(entry.context)!.add(entry.id);

    // Index by tags
    if (entry.tags) {
      for (const tag of entry.tags) {
        if (!this.tagIndex.has(tag)) {
          this.tagIndex.set(tag, new Set());
        }
        this.tagIndex.get(tag)!.add(entry.id);
      }
    }
  }

  private removeFromIndex(entry: MemoryEntry): void {
    // Remove from context index
    const contextSet = this.contextIndex.get(entry.context);
    if (contextSet) {
      contextSet.delete(entry.id);
      if (contextSet.size === 0) {
        this.contextIndex.delete(entry.context);
      }
    }

    // Remove from tag index
    if (entry.tags) {
      for (const tag of entry.tags) {
        const tagSet = this.tagIndex.get(tag);
        if (tagSet) {
          tagSet.delete(entry.id);
          if (tagSet.size === 0) {
            this.tagIndex.delete(tag);
          }
        }
      }
    }
  }

  private calculateRelevance(entry: MemoryEntry, context: string): number {
    let score = 0;

    // Exact context match
    if (entry.context === context) {
      score += 1.0;
    }

    // Recency boost (newer memories get higher scores)
    const age = Date.now() - entry.timestamp;
    const dayInMs = 24 * 60 * 60 * 1000;
    score += Math.max(0, 1 - (age / (30 * dayInMs)));

    return score;
  }

  private calculateTagRelevance(entry: MemoryEntry, searchTags: string[]): number {
    if (!entry.tags || entry.tags.length === 0) {
      return 0;
    }

    const matchingTags = entry.tags.filter(tag => searchTags.includes(tag));
    const score = matchingTags.length / searchTags.length;

    // Recency boost
    const age = Date.now() - entry.timestamp;
    const dayInMs = 24 * 60 * 60 * 1000;
    const recencyScore = Math.max(0, 1 - (age / (30 * dayInMs)));

    return score + (recencyScore * 0.2);
  }
}
