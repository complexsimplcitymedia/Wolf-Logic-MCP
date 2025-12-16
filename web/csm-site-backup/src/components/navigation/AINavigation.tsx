import React from 'react';
import { Bot } from 'lucide-react';
import { NavLink } from './NavLink';

export function AINavigation() {
  return (
    <NavLink
      href="https://llama.complexsimplicityai.com"
      Icon={Bot}
      external
      className="bg-gradient-to-r from-purple-500/20 to-blue-500/20 px-4 py-2 rounded-full border border-white/10 hover:border-white/20"
    >
      AI Assistant
    </NavLink>
  );
}