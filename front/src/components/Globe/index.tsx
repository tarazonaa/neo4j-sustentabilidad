import { useContext, useRef, useState } from 'react';

import { useGlobe, useAnimate } from './hooks';
import { GlobeContext } from '@/App';

import type { FrameData } from '@/types.ts';

const Globe = () => {
  const containerRef = useRef(null);
  const [frameData, setFrameData] = useState<FrameData | null>(null);
  const { setGlobe } = useContext(GlobeContext);

  useGlobe(containerRef, setFrameData, setGlobe);
  useAnimate(frameData);

  return (
    <div ref={containerRef} id='globe-visualizer'></div>
  )
};

export default Globe;
