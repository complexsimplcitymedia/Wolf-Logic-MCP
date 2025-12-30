import React, { useState } from 'react';
import YouTube from 'react-youtube';

interface VideoIntroProps {
  onIntroComplete: () => void;
}

export function VideoIntro({ onIntroComplete }: VideoIntroProps) {
  const [isReady, setIsReady] = useState(false);

  const opts = {
    height: '100%',
    width: '100%',
    playerVars: {
      autoplay: 1,
      controls: 0,
      disablekb: 1,
      modestbranding: 1,
      playsinline: 1,
      rel: 0,
      showinfo: 0,
      iv_load_policy: 3,
      fs: 0,
      origin: window.location.origin,
      vq: 'hd720',
      mute: 1 // Required for autoplay
    }
  };

  const handleReady = (event: { target: any }) => {
    setIsReady(true);
    event.target.playVideo();
    event.target.setPlaybackQuality('hd720');
  };

  const handleStateChange = (event: { target: any; data: number }) => {
    // YouTube player state: -1 (unstarted), 0 (ended), 1 (playing), 2 (paused), 3 (buffering), 5 (video cued)
    if (event.data === 0) {
      onIntroComplete();
    } else if (event.data === -1 || event.data === 2) {
      // If video is unstarted or paused, try to start playback
      event.target.playVideo();
    }
  };

  return (
    <div className="fixed inset-0 bg-black z-50">
      <div className={`w-full h-full transition-opacity duration-1000 ${isReady ? 'opacity-100' : 'opacity-0'}`}>
        <YouTube
          videoId="zTchPmGVsAk"
          opts={opts}
          onReady={handleReady}
          onStateChange={handleStateChange}
          className="w-screen h-screen"
          iframeClassName="w-full h-full object-cover"
          loading="eager"
        />
      </div>
    </div>
  );
}