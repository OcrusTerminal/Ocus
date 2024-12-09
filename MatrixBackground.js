"use client";

import React, { useEffect, useRef } from 'react';

const MatrixBackground = ({ isComplete }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const chars = '01';
    
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    const tunnelSegments = Array.from({ length: 300 }, () => ({
      angle: Math.random() * Math.PI * 2,    
      radius: Math.random() * 0.5 + 0.5,    
      size: Math.random() * 20 + 10          
    }));

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    const clearCenterArea = () => {
      ctx.save();
      ctx.globalCompositeOperation = 'destination-out';
      const gradient = ctx.createRadialGradient(
        centerX, centerY, 100,  // Smaller inner clear area
        centerX, centerY, 250   // Larger gradient edge
      );
      gradient.addColorStop(0, 'rgba(0,0,0,1)');
      gradient.addColorStop(1, 'rgba(0,0,0,0)');
      
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.restore();
    };

    const animate = () => {
      if (isComplete) return;
      
      ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      tunnelSegments.forEach(segment => {
        segment.z -= 1.5;
        
        const perspective = 400 / (400 + segment.z);
        const tunnelRadius = 800 * segment.radius; 
        
        const x = centerX + Math.cos(segment.angle) * tunnelRadius * perspective;
        const y = centerY + Math.sin(segment.angle) * tunnelRadius * perspective;
        
        const char = chars[Math.floor(Math.random() * chars.length)];
        const size = Math.max(1, Math.floor(segment.size * perspective));
        const alpha = Math.min(1, (1500 - segment.z) / 1500);
        const distanceAlpha = segment.radius * alpha; // Fade based on radius
        
        ctx.font = `${size}px monospace`;
        ctx.fillStyle = `rgba(0, ${Math.floor(255 * alpha)}, 0, ${distanceAlpha})`;
        ctx.fillText(char, x, y);
        
        if (segment.z < 0) {
          segment.z = 1500;
          segment.angle = Math.random() * Math.PI * 2;
          segment.radius = Math.random() * 0.5 + 0.5;
        }
      });
      
      clearCenterArea();
      requestAnimationFrame(animate);
    };
    
    animate();
    
    return () => window.removeEventListener('resize', resizeCanvas);
  }, [isComplete]);
  
  return (
    <canvas
      ref={canvasRef}
      className="absolute top-0 left-0 w-full h-full"
      style={{ 
        opacity: isComplete ? 0 : 1, 
        transition: 'opacity 0.5s',
        background: 'black' 
      }}
    />
  );
};

export default MatrixBackground;