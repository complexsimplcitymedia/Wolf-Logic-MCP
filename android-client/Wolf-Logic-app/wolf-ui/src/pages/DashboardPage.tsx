import React, { useState, useEffect } from 'react';
import './DashboardPage.css';

const DashboardPage: React.FC = () => {
  const [timestamp, setTimestamp] = useState<string>('');
  const [chartFiles, setChartFiles] = useState({
    timeline: '',
    agent: '',
    namespaces: '',
    hourly: ''
  });

  useEffect(() => {
    // Get latest chart timestamp (today's date format)
    const now = new Date();
    const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');

    // Use the latest known timestamp from today
    const latestTs = '20251210_102343';
    setTimestamp('2025-12-10 10:23:43');

    setChartFiles({
      timeline: `/charts/timeline_${latestTs}.png`,
      agent: `/charts/agent_totals_${latestTs}.png`,
      namespaces: `/charts/namespaces_${latestTs}.png`,
      hourly: `/charts/hourly_${latestTs}.png`
    });
  }, []);

  const refreshCharts = () => {
    // Force refresh by adding cache buster
    const cacheBuster = Date.now();
    const latestTs = '20251210_102343';
    setChartFiles({
      timeline: `/charts/timeline_${latestTs}.png?v=${cacheBuster}`,
      agent: `/charts/agent_totals_${latestTs}.png?v=${cacheBuster}`,
      namespaces: `/charts/namespaces_${latestTs}.png?v=${cacheBuster}`,
      hourly: `/charts/hourly_${latestTs}.png?v=${cacheBuster}`
    });
  };

  return (
    <div className="dashboard-page">
      <h1>Wolf AI Performance Dashboard</h1>
      <div className="timestamp">
        Generated: {timestamp}
        <button onClick={refreshCharts} className="refresh-btn">Refresh</button>
      </div>

      <div className="chart-grid">
        <div className="chart-card">
          <div className="chart-title">Activity Timeline</div>
          <img src={chartFiles.timeline} alt="Timeline" />
        </div>
        <div className="chart-card">
          <div className="chart-title">Agent Performance</div>
          <img src={chartFiles.agent} alt="Agent Totals" />
        </div>
        <div className="chart-card">
          <div className="chart-title">Namespace Distribution</div>
          <img src={chartFiles.namespaces} alt="Namespaces" />
        </div>
        <div className="chart-card">
          <div className="chart-title">Hourly Activity</div>
          <img src={chartFiles.hourly} alt="Hourly" />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
