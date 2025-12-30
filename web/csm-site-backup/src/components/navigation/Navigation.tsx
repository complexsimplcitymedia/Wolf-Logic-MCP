import React, { useState } from 'react';
import { Menu, X, Info, Briefcase } from 'lucide-react';
import { ServiceIcons } from './ServiceIcons';
import { NavLink } from './NavLink';
import { PlanetNavigation } from '../PlanetNavigation';
import { CSLogo } from '../logo/CSLogo';

export function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50">
      <nav className="bg-black/80 backdrop-blur-sm border-b border-white/10">
        <div className="container mx-auto px-4">
          <div className="flex items-center h-24">
            {/* Logo */}
            <div className="flex-shrink-0">
              <a href="/" className="flex items-center space-x-3">
                <CSLogo />
                <span className="hidden md:inline-block text-lg font-medium">
                  Complex Simplicity
                </span>
              </a>
            </div>

            {/* Navigation Links */}
            <div className="hidden md:flex items-center ml-8 space-x-8">
              <NavLink href="https://about.complexsimplicityai.com" Icon={Info} external>About</NavLink>
              <NavLink href="https://www.imdb.com/name/nm1839413/" Icon={Briefcase} external>Portfolio</NavLink>
            </div>

            {/* Service Icons */}
            <ServiceIcons />

            {/* Planet Navigation */}
            <div className="hidden md:block ml-auto">
              <PlanetNavigation />
            </div>

            {/* Mobile Menu Button */}
            <button 
              className="md:hidden ml-auto text-white"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              aria-label="Toggle menu"
            >
              {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="fixed inset-0 bg-black/95 z-40 flex flex-col items-center justify-center space-y-8 lg:hidden pt-24">
          <div className="flex flex-col items-center space-y-8">
            <NavLink href="https://about.complexsimplicityai.com" Icon={Info} external>About</NavLink>
            <NavLink href="https://www.imdb.com/name/nm1839413/" Icon={Briefcase} external>Portfolio</NavLink>
            <PlanetNavigation mobile />
          </div>
        </div>
      )}
    </header>
  );
}