import React from 'react';
import { Navigation } from './Navigation';
import { VideoBackground } from './VideoBackground';
import { StarField } from './StarField';
import { SocialLinks } from './SocialLinks';
import { Footer } from './footer/Footer';

interface LayoutProps {
  children: React.ReactNode;
  showBackground?: boolean;
}

export function Layout({ children, showBackground = true }: LayoutProps) {
  return (
    <main className="relative min-h-screen bg-black text-white">
      <StarField />
      <Navigation />
      
      {/* Main content with padding for header */}
      <div className="pt-24"> {/* Add padding-top to account for fixed header */}
        {showBackground && (
          <div className="relative">
            <VideoBackground />
            <div className="relative space-gradient">
              {children}
            </div>
          </div>
        )}
        {!showBackground && children}
      </div>

      <SocialLinks />
      <Footer />
    </main>
  );
}