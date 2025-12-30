import React from 'react';
import { Layout } from '../layout/Layout';
import { PortfolioGrid } from '../portfolio/PortfolioGrid';
import { PortfolioHeader } from '../portfolio/PortfolioHeader';

export function PortfolioPage() {
  return (
    <Layout 
      title="Portfolio | Complex Simplicity Media"
      description="View our portfolio of professional 3D animation work, including Hollywood productions, game development, and architectural visualization projects."
    >
      <div className="container mx-auto px-4 py-12 mt-16">
        <PortfolioHeader />
        <PortfolioGrid />
      </div>
    </Layout>
  );
}