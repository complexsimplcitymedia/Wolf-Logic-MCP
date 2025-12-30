import React from 'react';
import { Layout } from '../layout/Layout';
import { PrivacyContent } from '../sections/legal/PrivacyContent';

export function PrivacyPage() {
  return (
    <Layout 
      title="Privacy Policy | Complex Simplicity Media"
      description="Privacy Policy for Complex Simplicity Media - Learn how we collect, use, and protect your personal information."
    >
      <PrivacyContent />
    </Layout>
  );
}