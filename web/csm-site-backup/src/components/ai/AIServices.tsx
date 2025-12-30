import React from 'react';
import { Brain, Cpu, Network, Workflow } from 'lucide-react';

const services = [
  {
    icon: Brain,
    title: "Local LLM Integration",
    description: "Powerful local language model integration for enhanced creative workflows and automation."
  },
  {
    icon: Cpu,
    title: "Real-time Processing",
    description: "Fast, efficient processing of complex tasks using local computational resources."
  },
  {
    icon: Network,
    title: "Secure Environment",
    description: "All processing happens locally, ensuring data privacy and security."
  },
  {
    icon: Workflow,
    title: "Custom Workflows",
    description: "Tailored AI solutions integrated directly into your production pipeline."
  }
];

export function AIServices() {
  return (
    <section className="py-16 bg-black/60">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-12">GemOLLama AI Services</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {services.map((service) => (
            <div key={service.title} className="bg-black/40 backdrop-blur-sm rounded-lg p-6 border border-white/10">
              <service.icon className="w-10 h-10 text-purple-500 mb-4" />
              <h3 className="text-xl font-bold mb-2">{service.title}</h3>
              <p className="text-gray-400">{service.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}