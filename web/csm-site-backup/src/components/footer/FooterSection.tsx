import React from 'react';

interface FooterSectionProps {
  title: string;
  children: React.ReactNode;
}

export function FooterSection({ title, children }: FooterSectionProps) {
  return (
    <div className="flex flex-col space-y-3">
      <h3 className="text-sm font-semibold text-white/90">{title}</h3>
      {children}
    </div>
  );
}