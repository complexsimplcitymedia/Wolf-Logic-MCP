import React, { useState, useEffect } from 'react';
import './MemoryPanel.css';

interface Memory {
  id: string;
  content: string;
  category?: string;
  cluster?: number;
  timestamp?: string;
  user_id?: string;
}

interface MemoryStats {
  total: number;
  categorized: number;
  uncategorized: number;
  categories: { [key: string]: number };
}

const MemoryPanel: React.FC = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [recentUpdates, setRecentUpdates] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    fetchMemories();
    fetchStats();
    const interval = setInterval(() => {
      fetchMemories();
      fetchStats();
    }, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMemories = async () => {
    try {
      const response = await fetch('/api/memories/recent?limit=50');
      const data = await response.json();
      if (data.memories) {
        setMemories(data.memories);
        // Track recent updates (last 10)
        setRecentUpdates(data.memories.slice(0, 10));
      }
    } catch (error) {
      console.error('Failed to fetch memories:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/memories/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const filteredMemories = filter === 'all'
    ? memories
    : memories.filter(m => m.category === filter);

  return (
    <div className="memory-panel">
      <div className="memory-header">
        <h2>🧠 Memory System</h2>
        {stats && (
          <div className="memory-stats">
            <span className="stat">Total: {stats.total}</span>
            <span className="stat categorized">Categorized: {stats.categorized}</span>
            <span className="stat uncategorized">Uncategorized: {stats.uncategorized}</span>
          </div>
        )}
      </div>

      <div className="category-filter">
        <button
          className={filter === 'all' ? 'active' : ''}
          onClick={() => setFilter('all')}
        >
          All
        </button>
        {stats?.categories && Object.keys(stats.categories).map(cat => (
          <button
            key={cat}
            className={filter === cat ? 'active' : ''}
            onClick={() => setFilter(cat)}
          >
            {cat} ({stats.categories[cat]})
          </button>
        ))}
      </div>

      <div className="memory-sections">
        <div className="recent-updates">
          <h3>⚡ Recent Updates</h3>
          <div className="update-list">
            {recentUpdates.map((mem, idx) => (
              <div key={mem.id || idx} className="update-item">
                <span className="update-time">{new Date().toLocaleTimeString()}</span>
                <span className="update-category">{mem.category || 'uncategorized'}</span>
                <span className="update-content">{mem.content.substring(0, 60)}...</span>
              </div>
            ))}
          </div>
        </div>

        <div className="memory-list">
          <h3>📚 Memory Database ({filteredMemories.length})</h3>
          {loading ? (
            <div className="loading">Loading memories...</div>
          ) : (
            <div className="memory-grid">
              {filteredMemories.map((mem, idx) => (
                <div key={mem.id || idx} className="memory-card">
                  <div className="memory-meta">
                    <span className="memory-category">{mem.category || 'none'}</span>
                    {mem.cluster !== undefined && (
                      <span className="memory-cluster">Cluster {mem.cluster}</span>
                    )}
                  </div>
                  <div className="memory-content">{mem.content}</div>
                  {mem.user_id && <div className="memory-user">User: {mem.user_id}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MemoryPanel;
