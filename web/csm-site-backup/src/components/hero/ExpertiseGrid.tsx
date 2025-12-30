import React from 'react';
import { expertiseGridData } from '../../data/expertiseGrid';

interface ExpertiseCardProps {
  title: string;
  description: string;
  color: string;
}

function ExpertiseCard({ title, description, color }: ExpertiseCardProps) {
  return (
    <div className="bg-black/30 backdrop-blur-sm rounded-lg p-4 border border-white/10 hover:border-white/20 transition-all duration-300 transform hover:scale-105">
      <div className="flex items-center justify-center space-x-2 mb-2">
        <span className={`w-2 h-2 ${color} rounded-full`} />
        <span className="font-semibold">{title}</span>
      </div>
      <p className="text-base text-gray-400">{description}</p>
    </div>
  );
}

export function ExpertiseGrid() {
  return (
    <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl mx-auto">
      {expertiseGridData.map((item, index) => (
        <ExpertiseCard key={index} {...item} />
      ))}
    </div>
  );
}