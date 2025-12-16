import React from 'react';
import { createRoot } from 'react-dom/client';
import { ServicesPage } from '../components/pages/ServicesPage';
import '../index.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ServicesPage />
  </React.StrictMode>
);