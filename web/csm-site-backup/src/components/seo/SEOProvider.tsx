import React from 'react';
import { HelmetProvider } from 'react-helmet-async';
import { IconLinks } from './IconLinks';

interface SEOProviderProps {
  children: React.ReactNode;
}

export function SEOProvider({ children }: SEOProviderProps) {
  return (
    <HelmetProvider>
      <IconLinks />
      {children}
    </HelmetProvider>
  );
}