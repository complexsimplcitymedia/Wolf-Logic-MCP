import React, { useState, useRef, useCallback, useEffect } from 'react';
import type { YouTubeEvent } from 'react-youtube';
import { videos } from '../types/video';
import { VideoPlayer } from './VideoPlayer';
import { VideoOverlay } from './VideoOverlay';
import { WarpSpeedTransition } from './transitions/WarpSpeedTransition';

export function VideoBackground() {
  const [isReady, setIsReady] = useState(false);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const playerRef = useRef<any>(null);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleReady = useCallback((event: YouTubeEvent) => {
    setIsReady(true);
    playerRef.current = event.target;
    event.target.playVideo();

    const quality = videos[currentVideoIndex].quality?.[isMobile ? 'mobile' : 'desktop'] || 'default';
    event.target.setPlaybackQuality(quality);
  }, [currentVideoIndex, isMobile]);

  const handleEnd = useCallback(() => {
    setIsTransitioning(true);
  }, []);

  const handleTransitionComplete = useCallback(() => {
    setCurrentVideoIndex((prev) => (prev + 1) % videos.length);
    setIsTransitioning(false);
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden">
      <VideoOverlay />
      <WarpSpeedTransition 
        isActive={isTransitioning} 
        onComplete={handleTransitionComplete} 
      />
      <div className={`transition-opacity duration-1000 ${isReady ? 'opacity-100' : 'opacity-0'}`}>
        <div className={`relative w-full h-screen ${!isMobile ? 'md:scale-150' : ''}`}>
          <VideoPlayer
            videoId={videos[currentVideoIndex].id}
            onReady={handleReady}
            onEnd={handleEnd}
            isReady={isReady}
            isMobile={isMobile}
          />
        </div>
      </div>
      {!isReady && <div className="absolute inset-0 bg-black z-0" />}
    </div>
  );
}