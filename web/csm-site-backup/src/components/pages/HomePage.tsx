import React from 'react';
import { Layout } from '../layout/Layout';
import { HeroSection } from '../sections/home/HeroSection';
import { ExpertiseSection } from '../sections/home/ExpertiseSection';
import { ServicesPreview } from '../sections/home/ServicesPreview';
import { PortfolioPreview } from '../sections/home/PortfolioPreview';
import { ContactCTA } from '../sections/shared/ContactCTA';

export function HomePage() {
  return (
    <Layout>
      <HeroSection />
      <ExpertiseSection />
      <ServicesPreview />
      <PortfolioPreview />
      <ContactCTA />
    </Layout>
  );
}