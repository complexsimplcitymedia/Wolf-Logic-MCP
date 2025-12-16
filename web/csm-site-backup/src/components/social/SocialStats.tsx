import React, { useState, useEffect } from 'react';
import { Youtube, Instagram } from 'lucide-react';

interface SocialStatProps {
  platform: string;
  count: string;
  icon: React.ReactNode;
  subtext?: string;
  href?: string;
}

function SocialStat({ platform, count, icon, subtext, href }: SocialStatProps) {
  const content = (
    <div className="flex items-center space-x-3 bg-white/5 rounded-lg p-4 backdrop-blur-sm hover:bg-white/10 transition-all duration-300">
      <div className="text-white/80">
        {icon}
      </div>
      <div>
        <div className="text-xl font-bold text-white">{count}</div>
        <div className="text-sm text-gray-400">{platform}</div>
        {subtext && (
          <div className="text-xs text-gray-500 mt-0.5">{subtext}</div>
        )}
      </div>
    </div>
  );

  if (href) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className="cursor-pointer">
        {content}
      </a>
    );
  }
  return content;
}

export function SocialStats() {
  const [memoryCount, setMemoryCount] = useState<string>('--');

  useEffect(() => {
    const fetchMemoryCount = async () => {
      try {
        const response = await fetch('http://100.110.82.181:3550/api/memories/stats');
        const data = await response.json();
        if (data.total) {
          setMemoryCount(data.total.toLocaleString() + '+');
        }
      } catch {
        setMemoryCount('77K+');
      }
    };
    fetchMemoryCount();
    const interval = setInterval(fetchMemoryCount, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-wrap gap-4 justify-center">
      <SocialStat
        platform="Guerra de Los Gallos"
        count="20K+"
        subtext="YouTube Subscribers"
        icon={<Youtube className="w-6 h-6" />}
        href="https://www.youtube.com/@GuerradeLosGallos"
      />
      <SocialStat
        platform="Complex Simplicity"
        count="Growing"
        subtext="YouTube Channel"
        icon={<Youtube className="w-6 h-6" />}
        href="https://www.youtube.com/@ComplexSimplicityAI"
      />
      <SocialStat
        platform="Instagram Followers"
        count="7K+"
        icon={<Instagram className="w-6 h-6" />}
        href="https://www.instagram.com/complexsimplicityai"
      />
      <SocialStat
        platform="HackerOne"
        count="Active"
        subtext="Bug Bounty Hunter"
        icon={<img src="/icons/hackerone-logo.png" alt="HackerOne" className="w-6 h-6 object-contain invert" />}
        href="https://hackerone.com/wolflogic?type=user"
      />
      <SocialStat
        platform="Bugcrowd"
        count="Active"
        subtext="Security Researcher"
        icon={<img src="/icons/bugcrowd-logo.webp" alt="Bugcrowd" className="w-6 h-6 object-contain invert" />}
        href="https://bugcrowd.com/h/thewolfwalksalone"
      />
      <SocialStat
        platform="Google BugHunters"
        count="Active"
        subtext="Vulnerability Hunter"
        icon={<img src="/icons/wolf-street.png" alt="Wolf" className="w-6 h-6 rounded-full object-cover" />}
        href="https://bughunters.google.com/profile/c7417d46-f32a-4a11-9ff7-5e9efe60b255"
      />
      <SocialStat
        platform="Wolf Logic AI"
        count={memoryCount}
        subtext="Memories Stored"
        icon={<img src="/icons/brain-icon.avif" alt="AI Brain" className="w-6 h-6 object-contain" />}
        href="http://wolf-logic.complexsimplicityai.com"
      />
    </div>
  );
}