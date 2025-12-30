import React from 'react';
import { Film, Monitor, Laptop, Gamepad2, Box, Sparkles, Brain } from 'lucide-react';
import { ServiceCard } from './ServiceCard';

export function AnimationServices() {
  const services = [
    {
      icon: Film,
      title: "3D Character Animation",
      description: "Industry-leading character animation for films, games, and interactive media using cutting-edge techniques and tools."
    },
    {
      icon: Sparkles,
      title: "Visual Effects & Compositing",
      description: "Seamless integration of 3D elements with live-action footage, creating stunning visual effects for film and television."
    },
    {
      icon: Monitor,
      title: "Motion Graphics",
      description: "Dynamic motion graphics combining 3D elements with typography and design for broadcast and digital media."
    },
    {
      icon: Laptop,
      title: "Architectural Visualization",
      description: "Photorealistic 3D architectural visualization and walkthroughs for real estate and construction projects."
    },
    {
      icon: Gamepad2,
      title: "Game Animation",
      description: "Custom 3D animation for games, including character movements, cutscenes, and environmental animations."
    },
    {
      icon: Brain,
      title: "AI-Enhanced Animation",
      description: "Cutting-edge AI integration for advanced animation workflows and procedural generation."
    },
    {
      icon: Box,
      title: "Product Visualization",
      description: "High-end 3D product visualization and animation for marketing and e-commerce."
    }
  ];

  return (
    <section id="animation-services" className="py-24 bg-black/80">
      <div className="container mx-auto px-4">
        <h2 className="text-4xl md:text-5xl font-bold text-center mb-16">
          Professional 3D Animation Services
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {services.map((service) => (
            <ServiceCard key={service.title} {...service} />
          ))}
        </div>
      </div>
    </section>
  );
}