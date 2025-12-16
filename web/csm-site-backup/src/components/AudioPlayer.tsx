import React, { useEffect, useRef } from 'react';

export function AudioPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Create audio element
    const audio = new Audio('https://www.youtube.com/watch?v=cD1nlaoMR_A');
    audio.volume = 0.5;
    audio.loop = true;
    audioRef.current = audio;

    // Start playing after a short delay
    const timer = setTimeout(() => {
      audio.play().catch(error => {
        console.log('Audio autoplay failed:', error);
      });
    }, 1000);

    return () => {
      clearTimeout(timer);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  return null;
}