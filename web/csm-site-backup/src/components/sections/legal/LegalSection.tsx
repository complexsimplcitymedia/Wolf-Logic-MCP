import React from 'react';

interface LegalSectionProps {
  title: string;
  content: string | string[];
}

export function LegalSection({ title, content }: LegalSectionProps) {
  return (
    <section className="bg-white/5 backdrop-blur-sm rounded-lg p-4 md:p-6 border border-white/10">
      <h2 className="text-xl md:text-2xl font-semibold mb-4">{title}</h2>
      {Array.isArray(content) ? (
        <div className="space-y-4">
          {content.map((paragraph, index) => (
            <p key={index} className="text-sm md:text-base text-gray-300 leading-relaxed">
              {paragraph}
            </p>
          ))}
        </div>
      ) : (
        <p className="text-sm md:text-base text-gray-300 leading-relaxed">{content}</p>
      )}
    </section>
  );
}