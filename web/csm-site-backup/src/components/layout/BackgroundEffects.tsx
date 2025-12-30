import React from 'react';
import { StarField } from '../effects/StarField';
import { SpaceBackground } from '../effects/SpaceBackground';

export function BackgroundEffects() {
  return (
    <>
      <SpaceBackground />
      <StarField />
      <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/40" />
    </>
  );
}