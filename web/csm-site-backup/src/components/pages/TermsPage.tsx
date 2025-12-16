import React from 'react';
import { Layout } from '../layout/Layout';
import { TermsContent } from '../sections/legal/TermsContent';

export function TermsPage() {
  return (
    <Layout 
      title="Terms of Service | Complex Simplicity Media"
      description="Terms of Service for Complex Simplicity Media - Understanding our service agreement and user responsibilities."
    >
      <TermsContent />
    </Layout>
  );
}