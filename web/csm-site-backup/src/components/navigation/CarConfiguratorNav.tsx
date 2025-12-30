import React from 'react';
import { Car } from 'lucide-react';
import { NavLink } from './NavLink';

export function CarConfiguratorNav() {
  return (
    <NavLink
      href="https://carconfig.everythingsawrap.com"
      Icon={Car}
      external
      className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 px-4 py-2 rounded-full border border-white/10 hover:border-white/20"
    >
      Car Configurator
    </NavLink>
  );
}