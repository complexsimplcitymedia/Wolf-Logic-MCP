import React from 'react';
import { Facebook, Instagram, Youtube, Mail, Globe } from 'lucide-react';

export function SocialLinks() {
  const socialLinks = [
    {
      icon: Facebook,
      href: 'https://www.facebook.com/DaveAdams728',
      label: 'Facebook',
    },
    {
      icon: Instagram,
      href: 'https://www.instagram.com/wolfofallstreets/',
      label: 'Instagram',
      stats: '7K+ Followers'
    },
    {
      icon: Youtube,
      href: 'https://www.youtube.com/@complexs1mplicity',
      label: 'Complex Simplicity',
      stats: 'Professional Portfolio'
    },
    {
      icon: Youtube,
      href: 'https://www.youtube.com/@GuerradeLosGallos',
      label: 'Guerra de Los Gallos',
      stats: '20K+ Subscribers'
    },
    {
      icon: Globe,
      href: 'https://complexsimplicityai.com',
      label: 'Website',
    },
    {
      icon: Mail,
      href: 'mailto:complexsimplicitymedia@gmail.com',
      label: 'Email',
    },
  ];

  return (
    <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-20">
      <div className="flex items-center gap-6 px-8 py-4 bg-black/30 backdrop-blur-md rounded-full border border-white/10">
        {socialLinks.map((link, index) => (
          <a
            key={`${link.label}-${index}`}
            href={link.href}
            target="_blank"
            rel="noopener noreferrer"
            className="group relative"
            aria-label={link.label}
          >
            <link.icon className="w-6 h-6 text-white/70 hover:text-white transition-colors duration-300" />
            <div className="absolute -top-16 left-1/2 transform -translate-x-1/2 flex flex-col items-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
              <span className="px-2 py-1 bg-black/80 text-white text-xs rounded whitespace-nowrap">
                {link.label}
              </span>
              {link.stats && (
                <span className="px-2 py-1 bg-black/80 text-white/70 text-xs rounded whitespace-nowrap mt-1">
                  {link.stats}
                </span>
              )}
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}