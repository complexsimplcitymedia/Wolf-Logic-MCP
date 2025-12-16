import React from 'react';
import { CheckCircle } from 'lucide-react';

const expertise = [
  '13+ years of experience in film and television industry',
  'Advanced animation sequencing and motion capture integration specialist',
  'AI-enhanced workflow optimization and implementation expert',
  'Skilled in lighting, storytelling, and narrative development',
  '6000+ hours of expertise in Unreal Engine 5',
  'Proficient in rig optimization and performance enhancement',
  'Expert in advanced cinematic production techniques',
  'Specialized in real-time rendering and virtual production',
  'Experienced in AI technology integration and fine-tuning',
  'Proven track record in pushing visual narrative boundaries',
  'Network forensics and security incident investigation specialist',
  'AI-powered threat detection and vulnerability research expert'
];

export function ExpertiseList() {
  return (
    <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-4 text-left max-w-4xl mx-auto">
      {expertise.map((item, index) => (
        <div key={index} className="flex items-start space-x-3 bg-black/30 backdrop-blur-sm rounded-lg p-4">
          <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
          <span className="text-gray-200">{item}</span>
        </div>
      ))}
    </div>
  );
}