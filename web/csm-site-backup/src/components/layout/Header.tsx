import React, { useState, useEffect } from 'react';
import { Logo } from '../shared/Logo';
import { Navigation } from './Navigation';
import { MobileMenu } from './MobileMenu';

export function Header() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 0);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-colors duration-300 
                     ${isScrolled ? 'bg-black/80 backdrop-blur-sm' : 'bg-transparent'}`}>
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-24">
          <Logo />
          <Navigation />
          <MobileMenu />
        </div>
      </div>
    </header>
  );
}