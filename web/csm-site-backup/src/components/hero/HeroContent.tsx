import React from 'react';
import { LightingRig } from '../lighting/LightingRig';
import { HeroTitle } from './HeroTitle';
import { HeroDescription } from './HeroDescription';
import { HeroStats } from './HeroStats';
import { SocialStats } from '../social/SocialStats';

export function HeroContent() {
  return (
    <div className="container mx-auto min-h-screen flex flex-col justify-center items-center px-4 relative py-12">
      <LightingRig />
      <div className="w-full max-w-5xl mx-auto relative z-10">
        <div className="space-y-8">
          <HeroTitle />
          <HeroDescription />
          <HeroStats />
          <div className="mt-12">
            <SocialStats />
          </div>
        </div>
      </div>
    </div>
  );
}