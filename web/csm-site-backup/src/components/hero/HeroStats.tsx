import React from 'react';

interface StatItemProps {
  value: string;
  label: string;
  highlight?: boolean;
}

function StatItem({ value, label, highlight }: StatItemProps) {
  return (
    <div className={`px-6 py-4 rounded-lg backdrop-blur-sm border border-white/10 text-center
      ${highlight ? 'bg-white/10' : 'bg-black/30'}
      hover:border-white/20 transition-all duration-300 transform hover:scale-105`}>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  );
}

export function HeroStats() {
  return (
    <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatItem value="13+" label="Years Experience" highlight />
      <StatItem value="6000+" label="Hours in UE5" highlight />
      <StatItem value="100+" label="Projects Delivered" />
      <StatItem value="50+" label="Film Credits" />
    </div>
  );
}