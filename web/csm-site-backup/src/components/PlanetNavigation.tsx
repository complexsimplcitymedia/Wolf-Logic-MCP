import React, { useState } from 'react';
import { videos } from '../types/video';
import { VideoPlayer } from './VideoPlayer';

interface Planet {
  name: string;
  color: string;
  size: string;
  videoId: string;
  description: string;
}

const PLANETS: Planet[] = [
  { 
    name: 'Mercury', 
    color: 'from-gray-300 to-gray-500', 
    size: 'w-4 h-4', 
    videoId: videos[0].id,
    description: 'Behind the Scenes'
  },
  { 
    name: 'Venus', 
    color: 'from-yellow-500 to-yellow-700', 
    size: 'w-5 h-5', 
    videoId: videos[1].id,
    description: 'Main Reel'
  },
  { 
    name: 'Earth', 
    color: 'from-blue-400 to-blue-600', 
    size: 'w-5 h-5', 
    videoId: videos[2].id,
    description: 'Documentary'
  },
  { 
    name: 'Mars', 
    color: 'from-red-400 to-red-600', 
    size: 'w-4 h-4', 
    videoId: videos[3].id,
    description: 'Music Production'
  },
  { 
    name: 'Jupiter', 
    color: 'from-orange-300 to-orange-500', 
    size: 'w-8 h-8', 
    videoId: videos[4].id,
    description: 'Commercial'
  },
  { 
    name: 'Saturn', 
    color: 'from-yellow-200 to-yellow-400', 
    size: 'w-7 h-7', 
    videoId: videos[5].id,
    description: 'Creative Direction'
  },
  { 
    name: 'Uranus', 
    color: 'from-cyan-300 to-cyan-500', 
    size: 'w-6 h-6', 
    videoId: videos[6].id,
    description: 'Music Video'
  },
  { 
    name: 'Neptune', 
    color: 'from-blue-500 to-blue-700', 
    size: 'w-6 h-6', 
    videoId: videos[7].id,
    description: 'Commercial Production'
  }
];

interface PlanetNavigationProps {
  mobile?: boolean;
}

export function PlanetNavigation({ mobile = false }: PlanetNavigationProps) {
  const [transitioning, setTransitioning] = useState(false);
  const [showVideo, setShowVideo] = useState(false);
  const [currentVideoId, setCurrentVideoId] = useState('');

  const handlePlanetClick = (e: React.MouseEvent, videoId: string) => {
    e.preventDefault();
    if (transitioning) return;
    
    setCurrentVideoId(videoId);
    setShowVideo(true);
    document.body.style.overflow = 'hidden';
  };

  const handleCloseVideo = () => {
    setShowVideo(false);
    document.body.style.overflow = '';
  };

  return (
    <>
      <div className={`flex ${mobile ? 'flex-col space-y-4' : 'items-center space-x-4'}`}>
        {PLANETS.map((planet) => (
          <button
            key={planet.name}
            onClick={(e) => handlePlanetClick(e, planet.videoId)}
            className="group relative flex items-center"
            disabled={transitioning}
          >
            <div className={`${planet.size} rounded-full relative
                          bg-gradient-to-br ${planet.color}
                          transition-all duration-300 group-hover:scale-150 cursor-pointer
                          ${transitioning ? 'animate-pulse' : ''}`}>
              {/* Planet glow */}
              <div className="absolute inset-0 rounded-full blur-sm bg-white opacity-30" />
              
              {/* Planet ring (Saturn) */}
              {planet.name === 'Saturn' && (
                <div className="absolute -inset-x-4 h-full top-1/2 -translate-y-1/2 
                              bg-gradient-to-r from-yellow-200/50 to-yellow-400/50 
                              transform -rotate-12 rounded-full blur-[1px]" />
              )}
              
              {/* Planet name and description tooltip */}
              <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 
                           opacity-0 group-hover:opacity-100 transition-opacity duration-300 
                           whitespace-nowrap text-center">
                <span className="block text-xs font-bold text-white text-glow">
                  {planet.name}
                </span>
                <span className="block text-[10px] text-gray-400">
                  {planet.description}
                </span>
              </div>
            </div>
          </button>
        ))}
      </div>

      <VideoPlayer
        videoId={currentVideoId}
        onClose={handleCloseVideo}
        visible={showVideo}
      />
    </>
  );
}