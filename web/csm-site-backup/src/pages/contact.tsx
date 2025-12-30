import React from 'react';
import { createRoot } from 'react-dom/client';
import { ContactPage } from '../components/pages/ContactPage';
import '../index.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ContactPage />
  </React.StrictMode>
);