import React from 'react';
import { LucideIcon } from 'lucide-react';

interface ServiceIconProps {
  Icon?: LucideIcon;
  label: string;
  imageUrl?: string;
  imageClassName?: string;
  compact?: boolean;
  large?: boolean;
}

export function ServiceIcon({ Icon, label, imageUrl, imageClassName, compact = false, large = false }: ServiceIconProps) {
  const sizeClasses = large 
    ? `${compact ? 'w-14 h-14' : 'w-20 h-20 sm:w-24 sm:h-24'}`
    : `${compact ? 'w-10 h-10' : 'w-16 h-16 sm:w-20 sm:h-20'}`;

  const iconSizeClasses = large
    ? `${compact ? 'w-8 h-8' : 'w-12 h-12 sm:w-14 sm:h-14'}`
    : `${compact ? 'w-6 h-6' : 'w-8 h-8 sm:w-10 sm:h-10'}`;

  return (
    <div className="group">
      <div className={`flex items-center ${compact ? 'space-x-2' : 'flex-col space-y-2'}`}>
        <div className={`${sizeClasses} 
                      rounded-full bg-white/5 flex items-center justify-center
                      backdrop-blur-sm transition-all duration-500 group-hover:bg-white/20 
                      group-hover:scale-110 overflow-hidden border border-white/10`}>
          {Icon ? (
            <Icon className={`${iconSizeClasses} 
                          text-white transition-transform duration-500 
                          group-hover:scale-110`} />
          ) : (
            <img 
              src={imageUrl} 
              alt={label} 
              className={`${iconSizeClasses} 
                       object-contain transition-transform duration-500 
                       group-hover:scale-110 ${imageClassName || ''}`}
            />
          )}
        </div>
        <span className={`text-xs tracking-widest text-gray-300 group-hover:text-white 
                       transition-colors duration-500 font-medium text-glow
                       ${compact ? 'inline-block' : 'text-center'}`}>
          {label}
        </span>
      </div>
    </div>
  );
}