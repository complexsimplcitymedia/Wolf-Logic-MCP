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
        <a 
          href="https://beta-memory.complexsimplicityai.tech" 
          className="block w-full bg-red-900/80 text-white text-center py-2 text-sm font-bold hover:bg-red-800 transition-colors relative z-50 shadow-[0_0_15px_rgba(153,27,27,0.5)]"
        >
          BETA MEMORY ACCESS: CLICK HERE TO JOIN THE PILOT
        </a>
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