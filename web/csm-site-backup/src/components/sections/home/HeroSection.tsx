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

          <div className="mt-12">
            <a 
              href="/WolfLogic.apk" 
              className="inline-block px-8 py-3 text-lg font-bold text-black bg-white rounded-full hover:bg-gray-200 transition-colors duration-300 shadow-[0_0_20px_rgba(255,255,255,0.3)] hover:shadow-[0_0_30px_rgba(255,255,255,0.5)]"
              download
            >
              Download Complex Logic App
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
}