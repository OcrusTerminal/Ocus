import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const CoinMatchView = ({ matches }) => {
  const [discoveredMatches, setDiscoveredMatches] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [currentlyScanning, setCurrentlyScanning] = useState(null);
  
  const addRandomMatch = useCallback(() => {
    if (!matches || matches.length === 0) return;
    
    const randomMatch = matches[Math.floor(Math.random() * matches.length)];
    
    setCurrentlyScanning(randomMatch);
    
    setTimeout(() => {
      setDiscoveredMatches(prev => {
        if (prev.find(m => m.id === randomMatch.id)) return prev;
        const updatedMatches = [randomMatch, ...prev].slice(0, 10);
        setSelectedMatch(randomMatch);
        return updatedMatches;
      });
    }, 1800);
  }, [matches]);
  useEffect(() => {
    if (!matches || matches.length === 0) return;
    
    const initial = [matches[Math.floor(Math.random() * matches.length)]];
    setDiscoveredMatches(initial);
    setSelectedMatch(initial[0]);
    
    const interval = setInterval(addRandomMatch, 4000);
    return () => clearInterval(interval);
  }, [matches, addRandomMatch]);

  if (!matches || matches.length === 0) {
    return (
      <div className="text-green-500 font-mono p-8">
        No coin matches found in analysis.
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="mb-6 border border-green-500/30 rounded-lg p-4 bg-black/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-green-400 animate-pulse">⚡</span>
            <span className="text-green-400 font-mono">
              {currentlyScanning ? 'MATCH FOUND' : 'SCANNING MEME ECOSYSTEM'}
            </span>
          </div>
        </div>
        
        {currentlyScanning && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-3 text-green-500/80 font-mono text-sm"
          >
            Processing: {currentlyScanning.meme.name} → {currentlyScanning.coin.name}
          </motion.div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-4">
          <h3 className="text-green-400 font-mono text-lg mb-4">
            Live Match Feed ⚡
          </h3>
          
          <div className="space-y-2">
            <AnimatePresence>
              {discoveredMatches.map((match) => (
                <motion.div
                  key={`${match.id}-${match.coin.name}`}
                  initial={{ opacity: 0, x: -20, height: 0 }}
                  animate={{ opacity: 1, x: 0, height: 'auto' }}
                  exit={{ opacity: 0, x: 20, height: 0 }}
                  className={`border ${
                    selectedMatch?.id === match.id 
                      ? 'border-green-500' 
                      : 'border-green-500/30'
                  } p-4 rounded-lg cursor-pointer hover:bg-green-500/5 transition-colors`}
                  onClick={() => setSelectedMatch(match)}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="text-green-400 font-mono font-bold">
                        {match.coin.name}
                      </div>
                      <div className="text-green-500/60 text-sm">
                        {match.coin.symbol} • Score: {match.meme.matchScore.toFixed(1)}
                      </div>
                    </div>
                    <div className={`text-sm font-mono ${
                      parseFloat(match.price.changes.h24) >= 0 
                        ? 'text-green-400' 
                        : 'text-red-400'
                    }`}>
                      {parseFloat(match.price.changes.h24).toFixed(2)}%
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>

        <AnimatePresence mode="wait">
          {selectedMatch && (
            <motion.div
              key={selectedMatch.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="border border-green-500/30 p-6 rounded-lg"
            >
              <div className="space-y-6">
                <div>
                  <h4 className="text-green-400 font-mono mb-2">Meme Source</h4>
                  <div className="text-green-500 font-mono">
                    {selectedMatch.meme.name}
                  </div>
                  <div className="mt-2 text-sm text-green-500/60">
                    Match Score: {selectedMatch.meme.matchScore.toFixed(1)}
                  </div>
                </div>

                <div>
                  <h4 className="text-green-400 font-mono mb-2">Token Details</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-green-500/60">Name</div>
                      <div className="text-green-500">{selectedMatch.coin.name}</div>
                    </div>
                    <div>
                      <div className="text-green-500/60">Symbol</div>
                      <div className="text-green-500">{selectedMatch.coin.symbol}</div>
                    </div>
                    <div>
                      <div className="text-green-500/60">Chain</div>
                      <div className="text-green-500">{selectedMatch.coin.chain}</div>
                    </div>
                    <div>
                      <div className="text-green-500/60">Price</div>
                      <div className="text-green-500">
                        ${parseFloat(selectedMatch.price.current).toFixed(10)}
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-green-400 font-mono mb-2">Performance</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-green-500/60">1h</div>
                      <div className={parseFloat(selectedMatch.price.changes.h1) >= 0 
                        ? 'text-green-400' 
                        : 'text-red-400'
                      }>
                        {parseFloat(selectedMatch.price.changes.h1).toFixed(2)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-green-500/60">6h</div>
                      <div className={parseFloat(selectedMatch.price.changes.h6) >= 0 
                        ? 'text-green-400' 
                        : 'text-red-400'
                      }>
                        {parseFloat(selectedMatch.price.changes.h6).toFixed(2)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-green-500/60">24h</div>
                      <div className={parseFloat(selectedMatch.price.changes.h24) >= 0 
                        ? 'text-green-400' 
                        : 'text-red-400'
                      }>
                        {parseFloat(selectedMatch.price.changes.h24).toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-green-400 font-mono mb-2">Volume</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-green-500/60">1h</div>
                      <div className="text-green-500">
                        ${selectedMatch.volume.h1.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-green-500/60">6h</div>
                      <div className="text-green-500">
                        ${selectedMatch.volume.h6.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-green-500/60">24h</div>
                      <div className="text-green-500">
                        ${selectedMatch.volume.h24.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-green-400 font-mono mb-2">Links</h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(selectedMatch.links).map(([key, url]) => (
                      <a
                        key={key}
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1 text-sm border border-green-500/30 
                          rounded hover:bg-green-500/10 text-green-400"
                      >
                        {key}
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default CoinMatchView;