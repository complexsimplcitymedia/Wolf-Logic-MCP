import React from 'react';
import { Navigation } from './Navigation';
import { Footer } from './Footer';
import { SEOHead } from '../seo/SEOHead';
import { SpaceBackground } from '../effects/SpaceBackground';
import { StarField } from '../effects/StarField';
import { useSEO } from '../../hooks/useSEO';

interface LayoutProps {
  children: React.ReactNode;
  path?: string;
  title?: string;
  description?: string;
  imageUrl?: string;
  noindex?: boolean;
}

export function Layout({ 
  children, 
  path,
  title,
  description,
  imageUrl,
  noindex
}: LayoutProps) {
  const seo = useSEO({ path, title, description, imageUrl, noindex });

  return (
    <>
      <SEOHead {...seo} />
      <div className="min-h-screen bg-black text-white relative">
        <SpaceBackground />
        <StarField />
        <Navigation />
        <main className="relative z-10">
          {children}
        </main>
        <Footer />
      </div>
    </>
  );
}