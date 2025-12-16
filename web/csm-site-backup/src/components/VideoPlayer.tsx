import React from 'react';
import YouTube from 'react-youtube';
import type { YouTubeEvent } from 'react-youtube';
import { X } from 'lucide-react';

interface VideoPlayerProps {
  videoId: string;
  onClose: () => void;
  visible: boolean;
}

export function VideoPlayer({ videoId, onClose, visible }: VideoPlayerProps) {
  if (!visible) return null;
  
  const opts = {
    width: '100%',
    height: '100%',
    playerVars: {
      autoplay: 1,
      controls: 1,
      disablekb: 0,
      modestbranding: 1,
      mute: 0,
      playsinline: 1,
      rel: 0,
      showinfo: 0,
      loop: 0,
      vq: 'hd720'
    }
  };

  const handleStateChange = (event: YouTubeEvent) => {
    if (event.data === 1) {
      event.target.setPlaybackQuality('hd720');
    }
  };

  // Prevent clicking inside the player from closing the modal
  const handleContentClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90">
      <div className="absolute inset-0" onClick={onClose}></div>
      <div 
        className="relative z-10 w-full max-w-4xl aspect-video bg-black" 
        onClick={handleContentClick}
      >
        <YouTube
          videoId={videoId}
          opts={opts}
          onStateChange={handleStateChange}
          className="w-full h-full"
          iframeClassName="w-full h-full"
        />
        
        <button 
          onClick={onClose}
          className="absolute -top-12 right-0 text-white bg-black/50 hover:bg-black/70 rounded-full p-2 transition-colors"
          aria-label="Close video"
        >
          <X size={24} />
        </button>
      </div>
    </div>
  );
}