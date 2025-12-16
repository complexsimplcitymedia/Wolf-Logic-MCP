import React from 'react';
import VirtualLCD from '../components/VirtualLCD';
import './Home.css';

const Home: React.FC = () => {
  return (
    <div className="home-page">
      <VirtualLCD />
    </div>
  );
};

export default Home;
