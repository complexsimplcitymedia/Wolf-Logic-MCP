import React from 'react';
import { LucideIcon } from 'lucide-react';

interface NavLinkProps {
  href: string;
  children: React.ReactNode;
  Icon?: LucideIcon;
  external?: boolean;
  onClick?: () => void;
  className?: string;
}

export function NavLink({ 
  href, 
  children, 
  Icon, 
  external = false,
  onClick,
  className = ''
}: NavLinkProps) {
  const linkProps = external ? {
    target: '_blank',
    rel: 'noopener noreferrer'
  } : {};

  return (
    <a 
      href={href}
      onClick={onClick}
      className={`flex items-center space-x-2 text-gray-300 hover:text-white 
                transition-colors duration-300 ${className}`}
      {...linkProps}
    >
      {Icon && <Icon className="w-5 h-5" />}
      <span>{children}</span>
    </a>
  );
}