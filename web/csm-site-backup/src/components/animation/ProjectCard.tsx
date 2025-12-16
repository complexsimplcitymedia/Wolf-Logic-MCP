import React from 'react';

interface ProjectCardProps {
  title: string;
  description: string;
  image: string;
  category: string;
}

export function ProjectCard({ title, description, image, category }: ProjectCardProps) {
  return (
    <div className="group relative overflow-hidden rounded-xl">
      <div className="aspect-video overflow-hidden">
        <img 
          src={image} 
          alt={title}
          className="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500"
        />
      </div>
      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent p-6 flex flex-col justify-end">
        <span className="text-sm font-medium text-white/70 mb-2">{category}</span>
        <h3 className="text-xl font-bold mb-2">{title}</h3>
        <p className="text-white/80">{description}</p>
      </div>
    </div>
  );
}