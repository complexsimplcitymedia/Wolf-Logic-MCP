import React from 'react';
import { CheckCircle } from 'lucide-react';

const capabilities = [
  "Advanced natural language processing",
  "Real-time response generation",
  "Context-aware interactions",
  "Multi-turn conversations",
  "Custom knowledge integration",
  "Secure data handling",
  "Local processing guarantee",
  "Low-latency responses"
];

export function AICapabilities() {
  return (
    <section className="py-16 bg-gradient-to-b from-black/40 to-black/60">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-12">AI Capabilities</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
          {capabilities.map((capability, index) => (
            <div 
              key={index}
              className="flex items-start space-x-2 bg-black/30 backdrop-blur-sm rounded-lg p-4 border border-white/10"
            >
              <CheckCircle className="w-5 h-5 text-purple-500 mt-0.5 flex-shrink-0" />
              <span className="text-gray-300">{capability}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}