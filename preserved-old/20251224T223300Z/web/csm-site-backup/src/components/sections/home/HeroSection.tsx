import React from 'react';
import { motion } from 'framer-motion';
import { ExpertiseList } from './ExpertiseList';
import { HeroTitle } from './HeroTitle';
import { HeroBackground } from './HeroBackground';

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      <HeroBackground />
      <div className="container mx-auto px-4 py-20 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl mx-auto text-center"
        >
          <HeroTitle />
          <ExpertiseList />
        </motion.div>
      </div>
    </section>
  );
}