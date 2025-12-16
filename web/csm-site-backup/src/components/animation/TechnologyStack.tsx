import React from 'react';
import { TECH_STACK } from '../../utils/animation/constants';
import type { TechStack } from '../../utils/animation/types';

interface TechBadgeProps {
  tech: TechStack;
}

function TechBadge({ tech }: TechBadgeProps) {
  return (
    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-white/10 text-white/90">
      {tech}
    </span>
  );
}

export function TechnologyStack() {
  return (
    <section className="py-16 bg-black/40 backdrop-blur-sm">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold mb-8 text-center">Technology Expertise</h2>
        <div className="flex flex-wrap gap-4 justify-center">
          {Object.values(TECH_STACK).map((tech) => (
            <TechBadge key={tech} tech={tech} />
          ))}
        </div>
      </div>
    </section>
  );
}