import React from 'react';
import { MovingLight } from './MovingLight';

export function LightingRig() {
  return (
    <div className="absolute inset-x-0 -top-40 h-96 overflow-hidden pointer-events-none">
      <div className="relative w-full h-full">
        {/* Main moving lights */}
        <MovingLight side="left" color="blue" delay={0} intensity={0.3} />
        <MovingLight side="right" color="purple" delay={2000} intensity={0.3} />
        
        {/* Accent lights */}
        <MovingLight side="left" color="white" delay={1000} intensity={0.15} offset={-100} />
        <MovingLight side="right" color="white" delay={3000} intensity={0.15} offset={-100} />
        
        {/* Ambient fill light */}
        <div className="absolute inset-0 bg-gradient-radial from-white/5 to-transparent" />
      </div>
    </div>
  );
}