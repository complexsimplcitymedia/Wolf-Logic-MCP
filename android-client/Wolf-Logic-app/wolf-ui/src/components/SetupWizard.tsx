import React, { useState, useEffect } from 'react';
import './SetupWizard.css';

interface SetupWizardProps {
  onComplete: () => void;
}

const SetupWizard: React.FC<SetupWizardProps> = ({ onComplete }) => {
  const [step, setStep] = useState<number>(1);
  const [status, setStatus] = useState<string>('WAITING_FOR_USER');
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `> ${new Date().toLocaleTimeString()}: ${msg}`]);
  };

  const [selectedModel, setSelectedModel] = useState<string>('claude');

  const startSetup = async () => {
    setStep(3); // Move to terminal log screen
    setStatus('RUNNING');
    addLog(`Initializing Sovereign Node with ${selectedModel.toUpperCase()}...`);
    
    try {
      const installCmd = selectedModel === 'claude' ? 'npm install -g @anthropic-ai/sdk' : 
                         selectedModel === 'gemini' ? 'pip install -q -U google-generativeai' : 
                         'npm install -g openai';
      
      addLog(`COMMAND: ${installCmd}`);
      
      const response = await fetch('/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          script_id: 'bootstrap', 
          args: ['--model', selectedModel, '--install-cmd', installCmd] 
        })
      });
      const result = await response.json();
      
      if (result.success) {
        addLog('Infrastructure bootstrap sequence initiated.');
        addLog('Updating core environment...');
        addLog('Initializing Memory Core (PostgreSQL 17)...');
        addLog('Downloading Cognitive Engine (Nomic 768)...');
        
        // Poll for completion (simplified for beta)
        let completed = false;
        while (!completed) {
          const statusRes = await fetch('/api/status/bootstrap');
          const statusData = await statusRes.json();
          if (statusData.status === 'completed') {
            completed = true;
          } else {
            await new Promise(r => setTimeout(r, 2000));
          }
        }
        
        addLog('WOLF INTELLIGENCE NODE ACTIVE.');
        setStatus('COMPLETED');
      } else {
        addLog('ERROR: Could not initiate bootstrap sequence.');
        setStatus('FAILED');
      }
    } catch (err) {
      addLog('BRIDGE_FAILURE: Connection to backend lost.');
      setStatus('FAILED');
    }
  };

  return (
    <div className="setup-wizard">
      <div className="wizard-container">
        <div className="wizard-header">
          <span className="blink">WOLF_SETUP_WIZARD_v1.0</span>
        </div>

        {step === 1 && (
          <div className="wizard-screen agreement">
            <h2>SOVEREIGNTY DISCLOSURE</h2>
            <p>
              You are about to transform this device into a <strong>Wolf Intelligence Node</strong>.
              This process will install a local PostgreSQL 17 database and the Nomic Cognitive Engine (768-dim).
            </p>
            <div className="permission-box">
              <label>
                <input type="checkbox" defaultChecked /> Grant Permission to Deploy Database
              </label>
              <label>
                <input type="checkbox" defaultChecked /> Grant Permission to Download Nomic 768
              </label>
            </div>
            <button className="wizard-btn pulse" onClick={() => setStep(2)}>NEXT: SELECT INTELLIGENCE</button>
          </div>
        )}

        {step === 2 && (
          <div className="wizard-screen selection">
            <h2>SELECT PRIMARY INTELLIGENCE</h2>
            <div className="model-options">
              <div 
                className={`model-card ${selectedModel === 'claude' ? 'selected' : ''}`}
                onClick={() => setSelectedModel('claude')}
              >
                <h3>CLAUDE</h3>
                <p>Anthropic's reasoning engine.</p>
              </div>
              <div 
                className={`model-card ${selectedModel === 'gemini' ? 'selected' : ''}`}
                onClick={() => setSelectedModel('gemini')}
              >
                <h3>GEMINI</h3>
                <p>Google's multimodal powerhouse.</p>
              </div>
              <div 
                className={`model-card ${selectedModel === 'codex' ? 'selected' : ''}`}
                onClick={() => setSelectedModel('codex')}
              >
                <h3>CODEX</h3>
                <p>OpenAI's code specialist.</p>
              </div>
            </div>
            <button className="wizard-btn pulse" onClick={startSetup}>INITIALIZE NODE</button>
          </div>
        )}

        {step === 3 && (
          <div className="wizard-screen terminal">
            <div className="terminal-logs">
              {logs.map((log, i) => (
                <div key={i} className="log-line">{log}</div>
              ))}
              {status === 'RUNNING' && <div className="cursor">_</div>}
            </div>
            {status === 'COMPLETED' && (
              <button className="wizard-btn success" onClick={onComplete}>ENTER SYSTEM</button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SetupWizard;
