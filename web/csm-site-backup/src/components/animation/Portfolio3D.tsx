import React from 'react';
import { ProjectCard } from './ProjectCard';

export function Portfolio3D() {
  const projects = [
    {
      title: "Black Panther 2 - VFX Animation",
      description: "Lead animator for key action sequences and character animations",
      image: "https://images.unsplash.com/photo-1578632292335-df3abbb0d586?auto=format&fit=crop&q=80",
      category: "Film VFX"
    },
    {
      title: "Unreal Engine Character Rigging",
      description: "Advanced character rigging and animation for AAA game titles",
      image: "https://images.unsplash.com/photo-1614729373692-902db8558544?auto=format&fit=crop&q=80",
      category: "Game Animation"
    },
    {
      title: "Architectural Visualization",
      description: "Photorealistic 3D renders and animations for luxury real estate",
      image: "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&q=80",
      category: "Architecture"
    }
  ];

  return (
    <section id="portfolio" className="py-24 bg-gradient-to-b from-black/60 to-black/80">
      <div className="container mx-auto px-4">
        <h2 className="text-4xl md:text-5xl font-bold text-center mb-16">
          Featured 3D Animation Projects
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {projects.map((project) => (
            <ProjectCard key={project.title} {...project} />
          ))}
        </div>
      </div>
    </section>
  );
}