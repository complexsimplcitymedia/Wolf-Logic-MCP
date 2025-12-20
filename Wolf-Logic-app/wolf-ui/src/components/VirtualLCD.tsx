import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navigation from './Navigation';
import SetupWizard from './SetupWizard';
import './VirtualLCD.css';

interface GPUData {
  source: string;
  load: number;
  temperature: number;
  vram_used: number;
  vram_total: number;
  power_draw: number;
  fan_speed?: number;
}

interface SystemData {
  cpu: { percent: number; cores: number };
  memory: { total_gb: number; used_gb: number; percent: number };
  disk: { total_gb: number; used_gb: number; percent: number };
}

interface ServiceData {
  [key: string]: { port: number; status: string };
}

interface LCDData {
  gpu: GPUData;
  system: SystemData;
  services: ServiceData;
}

// Fallback static data if API fails
const fallbackData: LCDData = {
  gpu: {
    source: 'amd',
    load: 0,
    temperature: 0,
    vram_used: 0,
    vram_total: 16384,
    power_draw: 0,
    fan_speed: 0
  },
  system: {
    cpu: { percent: 0, cores: 16 },
    memory: { total_gb: 64, used_gb: 0, percent: 0 },
    disk: { total_gb: 2000, used_gb: 0, percent: 0 }
  },
  services: {
    'neo4j': { port: 7474, status: 'offline' },
    'qdrant': { port: 6333, status: 'offline' },
    'llm': { port: 11434, status: 'offline' },
    'mem0': { port: 8080, status: 'offline' }
  }
};

const VirtualLCD: React.FC = () => {
  const [data, setData] = useState<LCDData>(fallbackData);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [booting, setBooting] = useState<boolean>(() => {
    return !sessionStorage.getItem('wolf-booted');
  });
  const [showWizard, setShowWizard] = useState<boolean>(() => {
    return !localStorage.getItem('wolf-node-initialized');
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/lcd-data');
        const result = await response.json();
        if (result.success) {
          setData(result.data);
          setLastUpdate(new Date());
        }
      } catch (err) {
        // Keep showing last data or fallback
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => status === 'online' ? '#00ff00' : '#ff4444';
  const getLoadColor = (load: number) => load > 80 ? '#ff4444' : load > 50 ? '#ffaa00' : '#00ff00';

  const handleSetupComplete = () => {
    localStorage.setItem('wolf-node-initialized', 'true');
    setShowWizard(false);
  };

  // Boot animation - plays once per session
  if (booting) {
    return (
      <div className="boot-screen">
        <video
          className="boot-video"
          autoPlay
          playsInline
          onEnded={() => {
            sessionStorage.setItem('wolf-booted', 'true');
            setBooting(false);
          }}
        >
          <source src="/csai-boot.mp4" type="video/mp4" />
        </video>
      </div>
    );
  }

  // Setup Wizard - shown if infrastructure not yet initialized
  if (showWizard) {
    return <SetupWizard onComplete={handleSetupComplete} />;
  }

  return (
    <>
    <div className="virtual-lcd">
      <div className="lcd-header">
        <span className="header-title">SYSTEM MONITOR</span>
        <span className="timestamp">{lastUpdate.toLocaleTimeString()}</span>
      </div>

      <div className="lcd-grid">
        {/* GPU Section */}
        <div className="lcd-section gpu-section">
          <div className="section-title">GPU [{data.gpu.source.toUpperCase()}]</div>
          <div className="metric-row">
            <span className="metric-label">LOAD:</span>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${data.gpu.load}%`, backgroundColor: getLoadColor(data.gpu.load) }}></div>
            </div>
            <span className="metric-value" style={{ color: getLoadColor(data.gpu.load) }}>{data.gpu.load}%</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">TEMP:</span>
            <span className="metric-value" style={{ color: data.gpu.temperature > 80 ? '#ff4444' : '#00ff00' }}>{data.gpu.temperature}°C</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">VRAM:</span>
            <span className="metric-value">{data.gpu.vram_used}MB / {data.gpu.vram_total}MB</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">POWER:</span>
            <span className="metric-value">{data.gpu.power_draw}W</span>
          </div>
          {data.gpu.fan_speed && (
            <div className="metric-row">
              <span className="metric-label">FAN:</span>
              <span className="metric-value">{data.gpu.fan_speed} RPM</span>
            </div>
          )}
        </div>

        {/* System Section */}
        <div className="lcd-section system-section">
          <div className="section-title">SYSTEM</div>
          <div className="metric-row">
            <span className="metric-label">CPU:</span>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${data.system.cpu.percent}%`, backgroundColor: getLoadColor(data.system.cpu.percent) }}></div>
            </div>
            <span className="metric-value">{data.system.cpu.percent.toFixed(1)}%</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">RAM:</span>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${data.system.memory.percent}%`, backgroundColor: getLoadColor(data.system.memory.percent) }}></div>
            </div>
            <span className="metric-value">{data.system.memory.used_gb}GB/{data.system.memory.total_gb}GB</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">DISK:</span>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${data.system.disk.percent}%`, backgroundColor: getLoadColor(data.system.disk.percent) }}></div>
            </div>
            <span className="metric-value">{data.system.disk.percent.toFixed(1)}%</span>
          </div>
        </div>

        {/* Services Section */}
        <div className="lcd-section services-section">
          <div className="section-title">SERVICES</div>
          <div className="services-grid">
            {Object.entries(data.services).map(([name, info]) => (
              <div key={name} className="service-item">
                <span className="service-indicator" style={{ backgroundColor: getStatusColor(info.status) }}></span>
                <span className="service-name">{name.toUpperCase()}</span>
                <span className="service-port">:{info.port}</span>
              </div>
            ))}
            <div className="service-item">
              <span className="service-indicator" style={{ backgroundColor: '#ff4444' }}></span>
              <span className="service-name">MARIADB</span>
              <span className="service-port">:3306</span>
            </div>
          </div>
        </div>
      </div>

    </div>

    {/* Control Buttons - Outside LCD */}
    <div className="lcd-button-panel">
      {/* Header row */}
      <div className="button-header-row">
        <Link to="/" className="lcd-button"><div className="button-top">DASHBOARD</div></Link>
        <Link to="/control" className="lcd-button"><div className="button-top">CONTROL</div></Link>
        <Link to="/memory" className="lcd-button"><div className="button-top">MEMORY</div></Link>
        <Link to="/graph" className="lcd-button"><div className="button-top">GRAPH</div></Link>
        <Link to="/settings" className="lcd-button"><div className="button-top">SETTINGS</div></Link>
      </div>

      {/* Square button grid */}
      <div className="button-square-grid">
        <button className="button-square">1</button>
        <button className="button-square">2</button>
        <button className="button-square">3</button>
        <button className="button-square">4</button>
        <button className="button-square">5</button>

        <button className="button-square">6</button>
        <button className="button-square">7</button>
        <button className="button-square">8</button>
        <button className="button-square">9</button>
        <button className="button-square">10</button>

        <button className="button-square">11</button>
        <button className="button-square">12</button>
        <button className="button-square">13</button>
        <button className="button-square">14</button>
        <button className="button-square">15</button>

        <button className="button-square">16</button>
        <button className="button-square">17</button>
        <button className="button-square">18</button>
        <button className="button-square">19</button>
        <button className="button-square">20</button>

        <button className="button-square">21</button>
        <button className="button-square">22</button>
        <button className="button-square">23</button>
        <button className="button-square">24</button>
        <button className="button-square">25</button>
      </div>

      <div className="panel-tagline">Because the Wolf Never Forgets</div>
    </div>
    </>
  );
};

export default VirtualLCD;
