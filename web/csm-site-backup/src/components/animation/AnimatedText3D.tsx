import React, { useEffect, useRef } from 'react';

interface AnimatedText3DProps {
  children: React.ReactNode;
}

export function AnimatedText3D({ children }: AnimatedText3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let frame: number;
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouseX = (e.clientX - rect.left - rect.width / 2) / rect.width;
      mouseY = (e.clientY - rect.top - rect.height / 2) / rect.height;
    };

    const animate = () => {
      targetX += (mouseX - targetX) * 0.1;
      targetY += (mouseY - targetY) * 0.1;

      const transform = `
        perspective(1000px)
        rotateX(${targetY * 10}deg)
        rotateY(${-targetX * 10}deg)
        translateZ(50px)
      `;

      container.style.transform = transform;

      frame = requestAnimationFrame(animate);
    };

    window.addEventListener('mousemove', handleMouseMove);
    frame = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div 
      ref={containerRef}
      className="transition-transform duration-200 ease-out will-change-transform"
      style={{ transformStyle: 'preserve-3d' }}
    >
      {children}
    </div>
  );
}