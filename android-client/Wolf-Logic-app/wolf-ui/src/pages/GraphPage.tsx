import React from 'react';
import './GraphPage.css';

const GraphPage: React.FC = () => {
  return (
    <div className="graph-page">
      <h1>🕸️ Graph Database</h1>
      <p className="page-description">Neo4j Graph Database Visualization</p>

      <div className="graph-info">
        <div className="info-card">
          <h3>GraphQL API</h3>
          <p>Access the GraphQL API at:</p>
          <a href="http://localhost:25000" target="_blank" rel="noopener noreferrer" className="api-link">
            http://localhost:25000
          </a>
        </div>

        <div className="info-card">
          <h3>Neo4j Browser</h3>
          <p>Access Neo4j Browser at:</p>
          <a href="http://localhost:8474" target="_blank" rel="noopener noreferrer" className="api-link">
            http://localhost:8474
          </a>
        </div>
      </div>

      <div className="coming-soon">
        <h2>Coming Soon</h2>
        <p>Interactive graph visualization will be added here</p>
      </div>
    </div>
  );
};

export default GraphPage;
