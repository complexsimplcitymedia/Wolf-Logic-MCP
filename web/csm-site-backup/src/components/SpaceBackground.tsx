import React, { useEffect, useState } from 'react';

export function SpaceBackground() {
  const [opacity, setOpacity] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setOpacity(1);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden">
      <div 
        className="absolute inset-0 bg-black transition-opacity duration-2000"
        style={{ opacity }}
      >
        {/* Subtle nebula effect */}
        <div className="absolute inset-0 opacity-10 mix-blend-screen bg-[radial-gradient(circle_at_50%_50%,rgba(76,0,255,0.05),rgba(0,0,0,0)_70%)]" />
        <div className="absolute inset-0 opacity-5 mix-blend-screen bg-[radial-gradient(circle_at_30%_70%,rgba(255,0,128,0.05),rgba(0,0,0,0)_70%)]" />
      </div>
    </div>
  );
}