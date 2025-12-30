import React from 'react';
import { createRoot } from 'react-dom/client';
import { PortfolioPage } from '../components/pages/PortfolioPage';
import '../index.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <PortfolioPage />
  </React.StrictMode>
);