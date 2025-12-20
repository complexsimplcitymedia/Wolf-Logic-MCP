import React, { useState, useEffect } from 'react';
import './WolfLogicGrid.css';

const API_BASE = 'http://100.110.82.181:3030';

interface ButtonSlot {
  name: string | null;
  id?: string;
  category?: string;
  isRunning?: boolean;
}

interface ApiResponse {
  ok: boolean;
  output?: string;
  name?: string;
  error?: string;
}

const WolfLogicGrid: React.FC = () => {
  const [slots, setSlots] = useState<ButtonSlot[]>(Array(32).fill({ name: null }));
  const [runningSlots, setRunningSlots] = useState<Set<number>>(new Set());
  const [lastOutput, setLastOutput] = useState<string>('');
  const [showModelPicker, setShowModelPicker] = useState<boolean>(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('mistral');

  useEffect(() => {
    fetchButtonStates();
    fetchOllamaModels();
  }, []);

  const fetchButtonStates = async () => {
    try {
      const response = await fetch(`${API_BASE}/scripts/state`);
      const data = await response.json();
      if (data.slots) {
        setSlots(data.slots);
      }
    } catch (error) {
      console.error('Failed to fetch button states:', error);
      setLastOutput('❌ Backend connection failed. Is the server running on port 8084?');
    }
  };

  const fetchOllamaModels = async () => {
    try {
      const response = await fetch(`${API_BASE}/scripts/models`);
      const data = await response.json();
      if (data.models && data.models.length > 0) {
        setAvailableModels(data.models);
      }
    } catch (error) {
      console.error('Failed to fetch Ollama models:', error);
      setAvailableModels([
        'mistral:latest', 'llama3:latest', 'codellama:latest',
        'phi3:latest', 'qwen2.5:latest', 'deepseek-coder:latest'
      ]);
    }
  };

  const runScript = async (slot: number, params?: any) => {
    if (runningSlots.has(slot)) return;

    // Slot 0 is Init Ollama - show model picker
    if (slot === 0 && !params) {
      setShowModelPicker(true);
      return;
    }

    // Slot 1 is Start Mistral - use selected model
    if (slot === 1 && !params && selectedModel) {
      params = { model: selectedModel };
    }

    setRunningSlots(prev => new Set([...prev, slot]));
    setLastOutput(`⚡ Running ${slots[slot]?.name || 'Script'}...`);

    try {
      const response = await fetch(`${API_BASE}/scripts/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot, params })
      });

      const data: ApiResponse = await response.json();

      if (data.ok) {
        setLastOutput(`✅ ${data.name}: ${data.output || 'Success'}`);
      } else {
        setLastOutput(`❌ Error: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      setLastOutput(`❌ Network Error: Could not connect to backend at ${API_BASE}`);
    } finally {
      setRunningSlots(prev => {
        const newSet = new Set(prev);
        newSet.delete(slot);
        return newSet;
      });
      // Refresh button states
      fetchButtonStates();
    }
  };

  const handleModelSelect = (model: string) => {
    setSelectedModel(model);
    setShowModelPicker(false);
    setLastOutput(`✅ Selected model: ${model}`);
    runScript(0, { model });
  };

  const getCategoryColor = (category?: string): string => {
    const colors: { [key: string]: string } = {
      system: '#ff6b6b',
      services: '#4ecdc4',
      memory: '#45b7d1',
      processing: '#96ceb4',
      interaction: '#ffeaa7',
      testing: '#dfe6e9',
      monitoring: '#a29bfe',
      agents: '#fd79a8',
      database: '#00b894'
    };
    return colors[category || ''] || '#636e72';
  };

  const renderButton = (index: number) => {
    const slot = slots[index] || { name: null };
    const isRunning = runningSlots.has(index);
    const hasScript = slot.name !== null && slot.name !== undefined;

    if (!hasScript) {
      return (
        <div key={index} className="button-placeholder">
          <span className="button-number">{index + 1}</span>
        </div>
      );
    }

    return (
      <button
        key={index}
        className={`wolf-button has-script ${isRunning ? 'running' : ''}`}
        onClick={() => runScript(index)}
        disabled={isRunning}
        style={{ borderColor: getCategoryColor(slot.category) }}
      >
        <span className="button-number">{index + 1}</span>
        <span className="button-label">
          {isRunning ? '⚡ Running...' : slot.name}
        </span>
        <span className="button-category" style={{ color: getCategoryColor(slot.category) }}>
          {slot.category}
        </span>
      </button>
    );
  };

  return (
    <div className="wolf-logic-container">
      <div className="control-panel">
        <h2>🧠 Complex Logic Control Surface</h2>
        <div className="status-bar">
          <span>Active Scripts: {slots.filter(s => s.name).length}/32</span>
          <span>Backend: {API_BASE}</span>
          <span>Model: <strong>{selectedModel}</strong></span>
        </div>
      </div>

      {/* Virtual LCD Output Panel */}
      <div className="output-panel lcd-output">
        <div className="lcd-frame">
          <div className="lcd-header-bar">VIRTUAL LCD OUTPUT</div>
          <pre className="lcd-text">{lastOutput || '🐺 Ready for commands...'}</pre>
        </div>
      </div>

      <div className="button-grid">
        {Array.from({ length: 32 }, (_, i) => renderButton(i))}
      </div>

      {/* Model Picker Modal */}
      {showModelPicker && (
        <div className="modal-overlay" onClick={() => setShowModelPicker(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Select Ollama Model</h3>
            <div className="model-list">
              {availableModels.map((model) => (
                <button
                  key={model}
                  className="model-button"
                  onClick={() => handleModelSelect(model)}
                >
                  {model}
                </button>
              ))}
            </div>
            <button className="close-button" onClick={() => setShowModelPicker(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default WolfLogicGrid;
