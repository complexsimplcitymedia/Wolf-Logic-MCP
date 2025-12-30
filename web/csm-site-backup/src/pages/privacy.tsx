import React from 'react';
import { createRoot } from 'react-dom/client';
import { PrivacyPage } from '../components/pages/PrivacyPage';
import '../index.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <PrivacyPage />
  </React.StrictMode>
);