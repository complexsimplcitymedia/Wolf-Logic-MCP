import React from 'react';
import { Layout } from '../layout/Layout';
import { BiographyContent } from '../sections/biography/BiographyContent';

export function BiographyPage() {
  return (
    <Layout 
      title="Biography | Complex Simplicity Media"
      description="Learn about the journey and expertise of our lead creative director and 3D animation specialist."
    >
      <BiographyContent />
    </Layout>
  );
}