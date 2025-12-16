import React, { useState } from 'react';
import { Layout } from './components/Layout';
import { HeroContent } from './components/HeroContent';
import { PortfolioSection } from './components/portfolio/PortfolioSection';
import { VideoIntro } from './components/VideoIntro';

export default function App() {
  const [showIntro, setShowIntro] = useState(true);

  const handleIntroComplete = () => {
    setShowIntro(false);
  };

  return (
    <>
      {showIntro ? (
        <VideoIntro onIntroComplete={handleIntroComplete} />
      ) : (
        <Layout>
          <HeroContent />
          <PortfolioSection />
        </Layout>
      )}
    </>
  );
}