import React from 'react';
import { LegalSection } from './LegalSection';
import { termsContent } from '../../../data/legal/terms';

export function TermsContent() {
  return (
    <div className="container mx-auto px-4 py-12">
      <h1 className="text-4xl font-bold text-center mb-8">Terms of Service</h1>
      <div className="max-w-4xl mx-auto space-y-8">
        {termsContent.map((section, index) => (
          <LegalSection
            key={index}
            title={section.title}
            content={section.content}
          />
        ))}
      </div>
    </div>
  );
}