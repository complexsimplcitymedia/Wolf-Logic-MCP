import React from 'react';
import { keywords } from '../../utils/seo/keywords';

export function HiddenContent() {
  // Create SEO-friendly content that's hidden from users
  const content = Object.values(keywords).flat().map(keyword => (
    `${keyword} expertise and professional services`
  )).join('. ');

  return (
    <div className="hidden" aria-hidden="true">
      <h2>Professional 3D Animation and Unreal Engine Development Services</h2>
      <p>{content}</p>
      <p>
        Expert in Unreal Engine, 3D animation, game development, and visual effects.
        Specializing in real-time rendering, virtual reality, and augmented reality applications.
        Advanced skills in Blueprint scripting, materials editing, and shader development.
      </p>
    </div>
  );
}