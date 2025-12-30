import React from 'react';
import { ANIMATION_CATEGORIES } from '../../utils/animation/constants';
import type { AnimationCategory } from '../../utils/animation/types';

interface ExpertiseCardProps {
  category: AnimationCategory;
  description: string;
}

function ExpertiseCard({ category, description }: ExpertiseCardProps) {
  return (
    <div className="bg-gradient-to-br from-black/30 to-black/50 backdrop-blur-sm rounded-lg p-6 border border-white/10">
      <h3 className="text-xl font-bold mb-3">{category}</h3>
      <p className="text-white/80">{description}</p>
    </div>
  );
}

export function ExpertiseAreas() {
  const expertiseDescriptions = {
    [ANIMATION_CATEGORIES.FILM]: 'High-end visual effects and character animation for major film productions',
    [ANIMATION_CATEGORIES.GAMES]: 'Interactive game animation and real-time rendering using Unreal Engine',
    [ANIMATION_CATEGORIES.ARCH]: 'Photorealistic architectural visualization and virtual walkthroughs',
    [ANIMATION_CATEGORIES.VR]: 'Immersive VR/AR experiences with cutting-edge technology',
    [ANIMATION_CATEGORIES.MOTION]: 'Dynamic motion graphics for broadcast and digital media',
    [ANIMATION_CATEGORIES.PRODUCT]: 'Product visualization and animation for marketing'
  };

  return (
    <section className="py-24 bg-black/60">
      <div className="container mx-auto px-4">
        <h2 className="text-4xl font-bold mb-12 text-center">Areas of Expertise</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {Object.entries(expertiseDescriptions).map(([category, description]) => (
            <ExpertiseCard
              key={category}
              category={category as AnimationCategory}
              description={description}
            />
          ))}
        </div>
      </div>
    </section>
  );
}