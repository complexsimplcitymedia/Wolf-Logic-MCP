import React, { useState } from 'react';
import { Menu, X, Info, Film, MapPin } from 'lucide-react';
import { ServiceIcons } from './navigation/ServiceIcons';
import { NavLink } from './navigation/NavLink';
import { PlanetNavigation } from './PlanetNavigation';
import { ServiceIcon } from './ServiceIcon';

export function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50">
      <nav className="bg-black/80 backdrop-blur-sm border-b border-white/10">
        <div className="container mx-auto px-4">
          <div className="flex items-center h-24">
            {/* Logo */}
            <div className="flex-shrink-0">
              <a href="https://complexsimplicityai.com" target="_blank" rel="noopener noreferrer">
                <img 
                  src="https://s3-media0.fl.yelpcdn.com/bphoto/3Zpn79OBd-1cHWEdQITM9A/o.jpg" 
                  alt="Complex Simplicity Media" 
                  className="h-16 w-auto object-contain invert"
                />
              </a>
            </div>

            {/* Navigation Links */}
            <div className="hidden md:flex items-center ml-8 space-x-8">
              <NavLink href="https://about.complexsimplicityai.com" Icon={Info} external>About</NavLink>
              <NavLink href="https://imdb.me/cadillac" Icon={Film} external>IMDB</NavLink>
              <NavLink href="https://g.co/kgs/VnXUkzj" Icon={MapPin} external>Contact</NavLink>
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
            <NavLink href="https://imdb.me/cadillac" Icon={Film} external>IMDB</NavLink>
            <NavLink href="https://g.co/kgs/VnXUkzj" Icon={MapPin} external>Contact</NavLink>
            <PlanetNavigation mobile />
          </div>
        </div>
      )}
    </header>
  );
}