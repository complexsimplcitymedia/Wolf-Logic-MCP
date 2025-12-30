import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { SEOProvider } from './components/seo/SEOProvider';
import App from './App';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <SEOProvider>
      <App />
    </SEOProvider>
  </StrictMode>
);