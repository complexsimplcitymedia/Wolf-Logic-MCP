import React from 'react';
import { PortfolioLink } from './PortfolioLink';
import { portfolioItems } from '../../data/portfolio';

export function PortfolioGrid() {
  return (
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
  );
}