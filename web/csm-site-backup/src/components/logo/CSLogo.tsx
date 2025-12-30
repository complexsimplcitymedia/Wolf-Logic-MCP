import React from 'react';

export function CSLogo() {
  return (
    <div className="relative w-16 h-16 flex items-center justify-center">
      {/* Outer ring */}
      <div className="absolute inset-0 rounded-full border-2 border-white/20 backdrop-blur-sm" />
      
      {/* Inner glow */}
      <div className="absolute inset-2 rounded-full bg-gradient-radial from-white/10 to-transparent" />
      
      {/* Logo text */}
      <div className="relative text-2xl font-bold tracking-wider text-white/90">
        <span className="relative inline-block transform -skew-x-12">
          CS
          {/* Text glow effect */}
          <span className="absolute inset-0 blur-sm text-white/50">CS</span>
        </span>
      </div>
      
      {/* Animated accent lines */}
      <div className="absolute inset-0 rounded-full">
        <div className="absolute inset-0 border border-white/10 rounded-full animate-pulse-slow" />
        <div className="absolute inset-0 border border-white/5 rounded-full animate-spin-slow" 
             style={{ animationDuration: '20s' }} />
      </div>
    </div>
  );
}