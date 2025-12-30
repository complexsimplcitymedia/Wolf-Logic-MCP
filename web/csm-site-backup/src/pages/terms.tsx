import React from 'react';
import { createRoot } from 'react-dom/client';
import { TermsPage } from '../components/pages/TermsPage';
import '../index.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <TermsPage />
  </React.StrictMode>
);