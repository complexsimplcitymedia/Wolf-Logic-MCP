import React from 'react';
import { CheckCircle } from 'lucide-react';
import { expertiseItems } from '../../data/expertise';

export function ExpertiseList() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
      {expertiseItems.map((item, index) => (
        <div key={index} className="flex items-start space-x-2">
          <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
          <span className="text-gray-200">{item}</span>
        </div>
      ))}
    </div>
  );
}