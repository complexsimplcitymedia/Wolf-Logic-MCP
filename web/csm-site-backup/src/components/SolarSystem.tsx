import React from 'react';

const PLANETS = [
  { name: 'Mercury', color: 'from-gray-300 to-gray-500', size: 'w-4 h-4' },
  { name: 'Venus', color: 'from-yellow-500 to-yellow-700', size: 'w-5 h-5' },
  { name: 'Earth', color: 'from-blue-400 to-blue-600', size: 'w-5 h-5' },
  { name: 'Mars', color: 'from-red-400 to-red-600', size: 'w-4 h-4' },
  { name: 'Jupiter', color: 'from-orange-300 to-orange-500', size: 'w-8 h-8' },
  { name: 'Saturn', color: 'from-yellow-200 to-yellow-400', size: 'w-7 h-7' },
  { name: 'Uranus', color: 'from-cyan-300 to-cyan-500', size: 'w-6 h-6' },
  { name: 'Neptune', color: 'from-blue-500 to-blue-700', size: 'w-6 h-6' },
  { name: 'Pluto', color: 'from-gray-400 to-gray-600', size: 'w-3 h-3' }
];

export function SolarSystem() {
  return (
    <div className="fixed top-0 left-0 right-0 pointer-events-none">
      <div className="relative h-24 overflow-hidden">
        {/* Sun positioned exactly at the banner border */}
        <div className="absolute left-1/2 bottom-0 -translate-x-1/2 translate-y-1/2">
          <div className="w-24 h-24 rounded-full relative">
            {/* Core of the sun */}
            <div className="absolute inset-0 bg-gradient-to-r from-yellow-300 via-orange-400 to-yellow-300 
                          rounded-full animate-pulse-slow" />
            
            {/* Inner glow */}
            <div className="absolute inset-0 bg-gradient-to-r from-yellow-200 via-orange-300 to-yellow-200 
                          rounded-full blur-sm opacity-80" />
            
            {/* Outer glow */}
            <div className="absolute -inset-4 bg-gradient-to-r from-yellow-100/30 via-orange-200/30 to-yellow-100/30 
                          rounded-full blur-xl" />
            
            {/* Emissive effect */}
            <div className="absolute -inset-8 bg-yellow-400/20 rounded-full blur-2xl" />
          </div>
        </div>
        
        {/* Planets in a line along the banner border */}
        <div className="absolute bottom-0 left-0 right-0 h-px">
          {PLANETS.map((planet, index) => (
            <div
              key={planet.name}
              className="absolute bottom-0 transform -translate-y-1/2"
              style={{ left: `${10 + (index * 10)}%` }}
            >
              <div className={`${planet.size} rounded-full relative group cursor-pointer
                             bg-gradient-to-br ${planet.color}
                             transition-all duration-300 hover:scale-150`}>
                {/* Planet glow */}
                <div className="absolute inset-0 rounded-full blur-sm bg-white opacity-30" />
                
                {/* Planet ring (Saturn) */}
                {planet.name === 'Saturn' && (
                  <div className="absolute -inset-x-4 h-full top-1/2 -translate-y-1/2 
                                bg-gradient-to-r from-yellow-200/50 to-yellow-400/50 
                                transform -rotate-12 rounded-full blur-[1px]" />
                )}
                
                {/* Planet name tooltip */}
                <span className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 
                               text-xs font-bold text-white opacity-0 group-hover:opacity-100 
                               transition-opacity duration-300 whitespace-nowrap text-glow 
                               pointer-events-auto z-10">
                  {planet.name}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}