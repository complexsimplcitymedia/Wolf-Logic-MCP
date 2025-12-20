import React, { useState } from 'react';
import VirtualLCD from '../components/VirtualLCD';
import SetupWizard from '../components/SetupWizard';
import './Home.css';

const Home: React.FC = () => {
  const [nodeInitialized, setNodeInitialized] = useState<boolean>(() => {
    return localStorage.getItem('wolf-node-initialized') === 'true';
  });

  const handleSetupComplete = () => {
    localStorage.setItem('wolf-node-initialized', 'true');
    setNodeInitialized(true);
  };

  return (
    <div className="home-page">
      {!nodeInitialized ? (
        <SetupWizard onComplete={handleSetupComplete} />
      ) : (
        <VirtualLCD />
      )}
    </div>
  );
};

export default Home;
