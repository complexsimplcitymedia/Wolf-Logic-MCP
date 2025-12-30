import React from 'react';

interface FooterLinkProps {
  href: string;
  children: React.ReactNode;
}

export function FooterLink({ href, children }: FooterLinkProps) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-sm text-gray-400 hover:text-white transition-colors duration-300"
    >
      {children}
    </a>
  );
}