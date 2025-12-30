import React from 'react';
import { createRoot } from 'react-dom/client';
import { BiographyPage } from '../components/pages/BiographyPage';
import '../index.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BiographyPage />
  </React.StrictMode>
);