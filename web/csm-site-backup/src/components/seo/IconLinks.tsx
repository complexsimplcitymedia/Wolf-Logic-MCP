import React from 'react';
import { Helmet } from 'react-helmet-async';

export function IconLinks() {
  return (
    <Helmet>
      {/* Favicon */}
      <link rel="icon" type="image/x-icon" href="/favicon.ico" />
      
      {/* Apple Touch Icons */}
      <link rel="apple-touch-icon" sizes="180x180" href="/icons/icon-192x192.png" />
      
      {/* Standard Icons */}
      <link rel="icon" type="image/png" sizes="32x32" href="/icons/icon-32x32.png" />
      <link rel="icon" type="image/png" sizes="16x16" href="/icons/icon-16x16.png" />
      
      {/* Web Manifest */}
      <link rel="manifest" href="/manifest.json" />
      
      {/* Theme Color */}
      <meta name="theme-color" content="#000000" />
    </Helmet>
  );
}