import React from 'react';
import { LegalSection } from './LegalSection';
import { privacyContent } from '../../../data/legal/privacy';

export function PrivacyContent() {
  return (
    <div className="container mx-auto px-4 py-12">
      <h1 className="text-4xl font-bold text-center mb-8">Privacy Policy</h1>
      <div className="max-w-4xl mx-auto space-y-8">
        {privacyContent.map((section, index) => (
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