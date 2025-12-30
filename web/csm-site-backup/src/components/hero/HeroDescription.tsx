import React from 'react';
import { ExpertiseList } from './ExpertiseList';
import { ExpertiseGrid } from './ExpertiseGrid';

export function HeroDescription() {
  return (
    <div className="relative max-w-4xl mx-auto text-center">
      <div className="space-y-8">
        <h2 className="text-2xl md:text-3xl text-gray-100 font-bold leading-relaxed">
          Unreal Engine Cinematic Sequencer Specialist
        </h2>
        
        <div className="bg-black/30 backdrop-blur-sm rounded-xl p-6 border border-white/10">
          <ExpertiseList />
        </div>

        <div className="text-lg text-gray-300 leading-relaxed max-w-3xl mx-auto">
          Pioneering innovative projects in gaming and film, leveraging comprehensive skills 
          to create immersive, cutting-edge cinematic experiences.
        </div>

        <ExpertiseGrid />
      </div>
    </div>
  );
}