import React, { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { NavLink } from '../navigation/NavLink';
import { AINavigation } from '../navigation/AINavigation';
import { CarConfiguratorNav } from '../navigation/CarConfiguratorNav';

export function MobileMenu() {
  const [isOpen, setIsOpen] = useState(false);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
    document.body.style.overflow = !isOpen ? 'hidden' : 'auto';
  };

  return (
    <div className="lg:hidden">
      <button
        onClick={toggleMenu}
        className="p-2 text-white focus:outline-none"
        aria-label={isOpen ? 'Close menu' : 'Open menu'}
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black/95 z-50">
          <div className="container mx-auto px-4 py-8">
            <div className="flex justify-end mb-8">
              <button
                onClick={toggleMenu}
                className="p-2 text-white"
                aria-label="Close menu"
              >
                <X size={24} />
              </button>
            </div>

            <nav className="flex flex-col items-center space-y-6">
              <NavLink href="/" onClick={toggleMenu}>Home</NavLink>
              <NavLink href="/portfolio.html" onClick={toggleMenu}>Portfolio</NavLink>
              <NavLink href="/services.html" onClick={toggleMenu}>Services</NavLink>
              <NavLink href="/contact.html" onClick={toggleMenu}>Contact</NavLink>
              <div className="flex flex-col items-center space-y-4 mt-4">
                <AINavigation />
                <CarConfiguratorNav />
              </div>
            </nav>

            <div className="mt-8 pt-8 border-t border-white/10">
              <div className="flex flex-col items-center space-y-4">
                <NavLink href="/privacy.html" onClick={toggleMenu}>Privacy Policy</NavLink>
                <NavLink href="/terms.html" onClick={toggleMenu}>Terms of Service</NavLink>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}