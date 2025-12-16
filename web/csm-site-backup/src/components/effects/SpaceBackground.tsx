import React from 'react';

export function SpaceBackground() {
  return (
    <div className="fixed inset-0 bg-black">
      <div className="absolute inset-0 opacity-30">
        <div className="absolute inset-0 bg-gradient-radial from-purple-500/10 via-transparent to-transparent" 
             style={{ transform: 'translate(-30%, -30%)' }} />
        <div className="absolute inset-0 bg-gradient-radial from-blue-500/10 via-transparent to-transparent"
             style={{ transform: 'translate(40%, 40%)' }} />
      </div>
    </div>
  );
}