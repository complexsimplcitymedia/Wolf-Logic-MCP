import React from 'react';
import { NavLink } from '../navigation/NavLink';

export function Footer() {
  return (
    <footer className="bg-black/80 backdrop-blur-sm border-t border-white/10 py-6">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="text-sm text-gray-400">
            © {new Date().getFullYear()} Complex Simplicity Media. All rights reserved.
          </div>
          <div className="flex space-x-6 mt-4 md:mt-0">
            <NavLink href="/privacy.html" className="text-sm">Privacy Policy</NavLink>
            <NavLink href="/terms.html" className="text-sm">Terms of Service</NavLink>
          </div>
        </div>
      </div>
    </footer>
  );
}