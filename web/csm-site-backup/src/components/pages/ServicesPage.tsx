import React from 'react';
import { Layout } from '../layout/Layout';
import { AnimationServices } from '../animation/AnimationServices';
import { ExpertiseAreas } from '../animation/ExpertiseAreas';
import { TechnologyStack } from '../animation/TechnologyStack';

export function ServicesPage() {
  return (
    <Layout 
      title="Services | Complex Simplicity Media"
      description="Professional 3D animation services including character animation, VFX, game development, and architectural visualization."
    >
      <div className="mt-16">
        <AnimationServices />
        <ExpertiseAreas />
        <TechnologyStack />
      </div>
    </Layout>
  );
}