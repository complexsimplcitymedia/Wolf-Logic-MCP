import React from 'react';
import { NavLink } from '../navigation/NavLink';
import { AINavigation } from '../navigation/AINavigation';
import { CarConfiguratorNav } from '../navigation/CarConfiguratorNav';
import { MobileMenu } from './MobileMenu';

export function Navigation() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-sm border-b border-white/10">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <NavLink href="/" className="text-xl font-bold">
              Complex Simplicity Media
            </NavLink>
          </div>

          <div className="hidden lg:flex items-center space-x-4">
            <NavLink href="/portfolio.html">Portfolio</NavLink>
            <NavLink href="/services.html">Services</NavLink>
            <NavLink href="/contact.html">Contact</NavLink>
            <AINavigation />
            <CarConfiguratorNav />
          </div>

          <MobileMenu />
        </div>
      </div>
    </nav>
  );
}