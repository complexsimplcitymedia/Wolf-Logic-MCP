import React, { useState } from 'react';
import { ServiceIcon } from '../ServiceIcon';
import { useAudioContext } from '../../hooks/useAudioContext';
import { AIPreviewOverlay } from '../ai/AIPreviewOverlay';
import { VideoPlayer } from '../VideoPlayer';

export function ServiceIcons() {
  const { setIsMuted } = useAudioContext();
  const [showAIOverlay, setShowAIOverlay] = useState(false);
  const [showVideo, setShowVideo] = useState(false);
  const [currentVideoId, setCurrentVideoId] = useState('');

  const handleAIClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsMuted(true);
    setShowAIOverlay(true);
  };

  const handleVideoClick = (e: React.MouseEvent, videoId: string) => {
    e.preventDefault();
    setCurrentVideoId(videoId);
    setShowVideo(true);
    // Ensure body doesn't scroll when video is open
    document.body.style.overflow = 'hidden';
  };

  const handleCloseVideo = () => {
    setShowVideo(false);
    // Re-enable scrolling
    document.body.style.overflow = '';
  };

  return (
    <>
      <div className="hidden md:flex items-center ml-8 space-x-8">
        <a href="#" onClick={(e) => handleVideoClick(e, '4mPSxZXOHTM')}>
          <ServiceIcon 
            imageUrl="https://i.pinimg.com/736x/12/28/db/1228db1d48e6ae03ddbb5eaaf8b7f273.jpg"
            label="Dialogue Development" 
            compact
          />
        </a>
        <a href="#" onClick={(e) => handleVideoClick(e, 'P5puVCgGjqA')}>
          <ServiceIcon 
            imageUrl="https://cdn2.unrealengine.com/ue-logotype-2023-vertical-white-1686x2048-bbfded26daa7.png"
            label="Unreal Engine" 
            compact
          />
        </a>
        <a 
          href="https://llama.complexsimplicityai.com"
          target="_blank"
          rel="noopener noreferrer"
          className="focus:outline-none"
        >
          <ServiceIcon 
            imageUrl="https://cdn.prod.website-files.com/625447c67b621ab49bb7e3e5/6595a3f16ea6fac5e47d75f3_ollama.png"
            label="AI/LLMs Demo" 
            imageClassName="invert"
            compact
          />
        </a>
        <a 
          href="https://cloud.complexsimplicityai.com" 
          target="_blank" 
          rel="noopener noreferrer"
        >
          <ServiceIcon 
            imageUrl="https://www.svgrepo.com/show/1699/web-development.svg"
            label="Cloud Services" 
            imageClassName="invert"
            compact
          />
        </a>
        <a href="https://hub.docker.com/u/cadillacdave" target="_blank" rel="noopener noreferrer">
          <ServiceIcon 
            imageUrl="https://www.docker.com/wp-content/uploads/2022/03/vertical-logo-monochromatic.png"
            label="Docker Desktop"
            imageClassName="invert brightness-0"
            compact
          />
        </a>
        <a href="https://gitlab.com/cadillacthewolf" target="_blank" rel="noopener noreferrer">
          <ServiceIcon 
            imageUrl="https://about.gitlab.com/images/press/logo/png/gitlab-icon-1-color-white-rgb.png"
            label="GitLab"
            compact
            large
          />
        </a>
      </div>

      <AIPreviewOverlay 
        isVisible={showAIOverlay}
        onClose={() => {
          setShowAIOverlay(false);
          setIsMuted(false);
        }}
      />

      <VideoPlayer
        videoId={currentVideoId}
        onClose={handleCloseVideo}
        visible={showVideo}
      />
    </>
  );
}