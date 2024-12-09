"use client";

import { motion } from 'framer-motion';
import React, { useMemo, useEffect, useState } from 'react';
import GlowingHourglass from './GlowingHourglass';

const HexagonNode = ({ 
  x, 
  y, 
  label, 
  active, 
  delay, 
  size = 'normal',
  isHub = false
}) => {
  const [isMobile, setIsMobile] = useState(false);
  
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    checkMobile();
    
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const sizes = {
    small: { outer: 30, inner: 25, text: 8 },
    normal: { outer: 35, inner: 30, text: 10 },
    large: { outer: 45, inner: 40, text: 12 }
  };
  
  const { outer: outerSize, inner: innerSize, text: textSize } = sizes[size];

  const { points, starPoints } = useMemo(() => {
    if (isHub) {
      const hexPoints = Array.from({ length: 6 }, (_, i) => {
        const angle = (i * 60 - 30) * (Math.PI / 180);
        return {
          x: Number((outerSize * Math.cos(angle)).toFixed(5)),
          y: Number((outerSize * Math.sin(angle)).toFixed(5))
        };
      });
      return { points: hexPoints, starPoints: [] };
    } else {
      const heptPoints = [];
      const stars = [];
      
      for (let i = 0; i < 7; i++) {
        const angle = (i * (360 / 7)) * (Math.PI / 180);
        heptPoints.push({
          x: Number((outerSize * Math.cos(angle)).toFixed(5)),
          y: Number((outerSize * Math.sin(angle)).toFixed(5))
        });

        const angle1 = (i * (360 / 7)) * (Math.PI / 180);
        const angle2 = ((i + 3) * (360 / 7)) * (Math.PI / 180);
        stars.push({
          x1: Number((innerSize * 0.6 * Math.cos(angle1)).toFixed(5)),
          y1: Number((innerSize * 0.6 * Math.sin(angle1)).toFixed(5)),
          x2: Number((innerSize * 0.6 * Math.cos(angle2)).toFixed(5)),
          y2: Number((innerSize * 0.6 * Math.sin(angle2)).toFixed(5))
        });
      }
      return { points: heptPoints, starPoints: stars };
    }
  }, [outerSize, innerSize, isHub]);

  const getPathFromPoints = (points) => {
    return points.map((point, i) => 
      `${i === 0 ? 'M' : 'L'} ${point.x} ${point.y}`
    ).join(' ') + 'Z';
  };

  const getForeignObjectProps = () => {
    if (isHub && isMobile) {
      return {
        x: -outerSize * 0.5,    
        y: -outerSize * 0.5,    
        width: outerSize * 1.5,
        height: outerSize * 1.5  
      };
    }
    
    return {
      x: -outerSize,
      y: -outerSize,
      width: outerSize * 2,
      height: outerSize * 2
    };
  };

  return (
    <motion.g
      id={`node-${label.replace(/\s+/g, '-')}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: active ? 1 : 0.3 }}
      transition={{ duration: 0.5, delay }}
    >
      {active && (
        <motion.path
          d={getPathFromPoints(points)}
          fill="rgba(0, 255, 0, 0.1)"
          transform={`translate(${x} ${y})`}
          style={{ filter: 'blur(8px)' }}
        />
      )}

      <g transform={`translate(${x} ${y})`}>
        <motion.path
          d={getPathFromPoints(points)}
          fill="none"
          stroke="#00ff00"
          strokeWidth="2"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.5, delay }}
        />

        {isHub ? (
          <foreignObject {...getForeignObjectProps()}>
            <GlowingHourglass size={outerSize * (isMobile ? 1.5 : 2)} />
          </foreignObject>
        ) : (
          <>
            {starPoints.map((point, i) => (
              <motion.line
                key={`star-${i}`}
                x1={point.x1}
                y1={point.y1}
                x2={point.x2}
                y2={point.y2}
                stroke="#00ff00"
                strokeWidth="0.5"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: active ? 1 : 0 }}
                transition={{ duration: 0.5, delay: delay + i * 0.1 }}
              />
            ))}
            <motion.circle
              r="2"
              fill="#00ff00"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.3, delay: delay + 0.8 }}
            />
          </>
        )}

        {active && Array.from({ length: 2 }).map((_, i) => (
          <motion.path
            key={`pulse-${i}`}
            d={getPathFromPoints(points)}
            stroke="#00ff00"
            strokeWidth="1"
            fill="none"
            initial={{ scale: 0.8, opacity: 1 }}
            animate={{ scale: 1.2, opacity: 0 }}
            transition={{
              duration: 2,
              delay: i * 1,
              repeat: Infinity,
              ease: "linear"
            }}
          />
        ))}
      </g>

      <motion.text
        x={x}
        y={y + outerSize * 1.6}
        textAnchor="middle"
        fill="#00ff00"
        style={{ 
          fontSize: `${textSize}px`,
          fontFamily: 'monospace',
          letterSpacing: '0.1em'
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: delay + 1.5 }}
      >
        {label.toUpperCase()}
      </motion.text>
    </motion.g>
  );
};

export default HexagonNode;