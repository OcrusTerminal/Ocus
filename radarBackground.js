import { motion } from "framer-motion";

const RadarMapBackground = () => {
  const circles = Array.from({ length: 3 }, (_, index) => ({
    id: index,
    initialScale: 0.2,
    animateScale: 2.5,
    duration: 4,
    delay: index * 1.3,
  }));

  return (
    <div className="absolute inset-0 overflow-hidden bg-black">
      <div className="absolute inset-0 z-0">
        <img
          src="/worldmap.png"
          alt="World Map"
          className="absolute inset-0 w-full h-full object-contain opacity-40"
          style={{
            filter: "brightness(0) sepia(100%) saturate(400%) hue-rotate(90deg) brightness(0.4) contrast(1)",
            mixBlendMode: "screen"
          }}
        />
      </div>

      <svg
        className="absolute inset-0 w-full h-full z-10"
        viewBox="0 0 800 600"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <pattern id="radar-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path
              d="M 40 0 L 0 0 0 40"
              fill="none"
              stroke="#00ff0022"
              strokeWidth="1"
            />
          </pattern>

          <filter id="radar-glow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feComposite in="blur" in2="SourceGraphic" operator="out" result="glowOut" />
            <feComposite in="glowOut" in2="SourceGraphic" operator="atop" />
          </filter>
        </defs>

        <rect width="800" height="600" fill="url(#radar-grid)" fillOpacity="0.3" />

        {circles.map((circle) => (
          <motion.circle
            key={circle.id}
            cx="400"
            cy="300"
            r="100"
            fill="none"
            stroke="#00ff00"
            strokeWidth="1.5"
            initial={{ 
              scale: circle.initialScale, 
              opacity: 0.7 
            }}
            animate={{ 
              scale: circle.animateScale, 
              opacity: 0 
            }}
            transition={{
              duration: circle.duration,
              repeat: Infinity,
              delay: circle.delay,
              ease: "linear"
            }}
            className="origin-center"
          />
        ))}

        <circle
          cx="400"
          cy="300"
          r="100"
          fill="none"
          stroke="#00ff0033"
          strokeWidth="1"
        />
        <circle
          cx="400"
          cy="300"
          r="200"
          fill="none"
          stroke="#00ff0033"
          strokeWidth="1"
        />
      </svg>
    </div>
  );
};

export default RadarMapBackground;