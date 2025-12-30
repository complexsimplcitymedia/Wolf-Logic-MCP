import React from 'react';
import { Layout } from '../layout/Layout';
import { ContactSection } from '../contact/ContactSection';

export function ContactPage() {
  return (
    <Layout 
      title="Contact Us | Complex Simplicity Media"
      description="Get in touch with Complex Simplicity Media for professional 3D animation services and project inquiries."
    >
      <div className="mt-16">
        <ContactSection />
      </div>
    </Layout>
  );
}