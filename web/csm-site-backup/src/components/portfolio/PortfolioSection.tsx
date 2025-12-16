import React from 'react';
import { PortfolioLink } from './PortfolioLink';

const portfolioItems = [
  {
    href: 'https://www.youtube.com/@complexs1mplicity',
    title: 'Complex Simplicity',
    description: 'Professional 3D Animation Portfolio'
  },
  {
    href: 'https://www.youtube.com/@GuerradeLosGallos',
    title: 'Guerra de Los Gallos',
    description: 'Creative Production & Music Videos'
  }
];

export function PortfolioSection() {
  return (
    <div className="py-12 bg-black/50 backdrop-blur-sm">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold text-white mb-8">Portfolio</h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {portfolioItems.map((item) => (
            <PortfolioLink
              key={item.href}
              href={item.href}
              title={item.title}
              description={item.description}
            />
          ))}
        </div>
      </div>
    </div>
  );
}