import React from 'react';
import { StarField } from '../../effects/StarField';

export function BiographyContent() {
  return (
    <div className="relative min-h-screen">
      <StarField />
      <div className="container mx-auto px-4 py-24">
        <div className="max-w-4xl mx-auto space-y-12">
          <div className="text-center mb-12">
            <img
              src="https://images.unsplash.com/photo-1533738363-b7f9aef128ce?auto=format&fit=crop&q=80&w=300&h=300"
              alt="Profile"
              className="w-32 h-32 rounded-full mx-auto mb-6 object-cover"
            />
            <h1 className="text-4xl md:text-5xl font-bold mb-4">David Adams</h1>
            <p className="text-xl text-gray-300">Creative Director & 3D Animation Specialist</p>
          </div>

          <div className="prose prose-invert max-w-none space-y-8">
            <div className="bg-black/30 backdrop-blur-sm rounded-lg p-6 border border-white/10">
              <h2 className="text-2xl font-bold mb-4">Professional Journey</h2>
              <p className="text-gray-300 leading-relaxed">
                With over 13 years of experience in the film and television industry, David has established himself as a leading expert in 3D animation and visual effects. His work on major Hollywood productions, including Black Panther 2, has showcased his ability to create compelling and innovative visual narratives.
              </p>
            </div>

            <div className="bg-black/30 backdrop-blur-sm rounded-lg p-6 border border-white/10">
              <h2 className="text-2xl font-bold mb-4">Technical Expertise</h2>
              <p className="text-gray-300 leading-relaxed">
                Specializing in Unreal Engine 5 with over 6000 hours of hands-on experience, David has mastered advanced animation sequencing, motion capture integration, and real-time rendering. His technical proficiency extends to AI-enhanced workflow optimization and implementation.
              </p>
            </div>

            <div className="bg-black/30 backdrop-blur-sm rounded-lg p-6 border border-white/10">
              <h2 className="text-2xl font-bold mb-4">Creative Vision</h2>
              <p className="text-gray-300 leading-relaxed">
                David's approach combines technical excellence with artistic innovation. He believes in pushing the boundaries of what's possible in digital storytelling, consistently delivering projects that blend cutting-edge technology with compelling narratives.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}