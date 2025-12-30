import React from 'react';

interface MovingLightProps {
  side: 'left' | 'right';
  color?: string;
  delay?: number;
  intensity?: number;
  offset?: number;
}

export function MovingLight({ 
  side, 
  color = 'white', 
  delay = 0, 
  intensity = 0.2,
  offset = 0
}: MovingLightProps) {
  const baseClasses = `
    absolute top-0 w-[400px] h-[800px]
    before:content-[''] before:absolute before:inset-0
    before:bg-gradient-radial before:from-${color}/30 before:to-transparent
    before:animate-pulse-slow
    after:content-[''] after:absolute after:inset-0
    after:bg-gradient-conic after:from-${color}/20 after:via-${color}/10 after:to-transparent
    after:animate-spin-slow after:blur-lg
  `;

  const sideClasses = {
    left: `-left-32 ${offset ? `ml-[${offset}px]` : ''} origin-top-right rotate-45`,
    right: `-right-32 ${offset ? `mr-[${offset}px]` : ''} origin-top-left -rotate-45`
  };

  const animationDelay = `animation-delay-${delay}`;

  return (
    <div 
      className={`
        ${baseClasses}
        ${sideClasses[side]}
        ${animationDelay}
      `}
      style={{
        background: `radial-gradient(
          circle at ${side === 'left' ? '100%' : '0%'} 0%,
          ${color}${Math.floor(intensity * 255).toString(16).padStart(2, '0')} 0%,
          transparent 70%
        )`,
        boxShadow: `0 0 100px ${color}${Math.floor(intensity * 100).toString(16).padStart(2, '0')}`
      }}
    >
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/10 to-transparent" />
      <div className={`absolute inset-0 animate-pulse-slow`} style={{ animationDelay: `${delay}ms` }} />
    </div>
  );
}