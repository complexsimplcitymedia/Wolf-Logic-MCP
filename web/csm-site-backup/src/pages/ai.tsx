import React from 'react';
import { createRoot } from 'react-dom/client';
import { AIPage } from '../components/pages/AIPage';
import '../index.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AIPage />
  </React.StrictMode>
);