import React from 'react';
import { ExternalLink } from 'lucide-react';

interface PortfolioLinkProps {
  href: string;
  title: string;
  description?: string;
}

export function PortfolioLink({ href, title, description }: PortfolioLinkProps) {
  return (
    <a 
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex items-center space-x-3 p-3 rounded-lg hover:bg-white/5 transition-colors duration-300"
    >
      <ExternalLink className="w-5 h-5 text-gray-400 group-hover:text-white transition-colors duration-300" />
      <div>
        <h3 className="text-white font-medium group-hover:text-white/90 transition-colors duration-300">
          {title}
        </h3>
        {description && (
          <p className="text-sm text-gray-400 group-hover:text-gray-300 transition-colors duration-300">
            {description}
          </p>
        )}
      </div>
    </a>
  );
}