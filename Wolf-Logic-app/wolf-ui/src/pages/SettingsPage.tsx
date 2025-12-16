import React from 'react';
import './SettingsPage.css';

const SettingsPage: React.FC = () => {
  return (
    <div className="settings-page">
      <h1>⚙️ Settings</h1>
      <p className="page-description">Configure your Wolf Logic AI system</p>

      <div className="settings-sections">
        <div className="settings-section">
          <h3>🔌 API Endpoints</h3>
          <div className="setting-item">
            <label>Backend API:</label>
            <input type="text" value="http://localhost:4500" readOnly />
          </div>
          <div className="setting-item">
            <label>Neo4j GraphQL:</label>
            <input type="text" value="http://localhost:25000" readOnly />
          </div>
          <div className="setting-item">
            <label>OpenMemory API:</label>
            <input type="text" value="http://100.110.82.181:8765" readOnly />
          </div>
        </div>

        <div className="settings-section">
          <h3>🤖 AI Models</h3>
          <div className="setting-item">
            <label>Default Model:</label>
            <select>
              <option>mistral:latest</option>
              <option>llama2:latest</option>
              <option>codellama:latest</option>
              <option>llama3:latest</option>
            </select>
          </div>
          <div className="setting-item">
            <label>Temperature:</label>
            <input type="range" min="0" max="1" step="0.1" defaultValue="0.7" />
          </div>
        </div>

        <div className="settings-section">
          <h3>🎨 Appearance</h3>
          <div className="setting-item">
            <label>Theme:</label>
            <select>
              <option>Dark (Wolf)</option>
              <option>Light</option>
              <option>High Contrast</option>
            </select>
          </div>
        </div>

        <div className="settings-section">
          <h3>📊 System Info</h3>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Version:</span>
              <span className="info-value">1.0.0</span>
            </div>
            <div className="info-item">
              <span className="info-label">Uptime:</span>
              <span className="info-value">Active</span>
            </div>
            <div className="info-item">
              <span className="info-label">User:</span>
              <span className="info-value">thewolfwalksalone</span>
            </div>
          </div>
        </div>
      </div>

      <div className="settings-actions">
        <button className="btn-primary">Save Settings</button>
        <button className="btn-secondary">Reset to Default</button>
      </div>
    </div>
  );
};

export default SettingsPage;
