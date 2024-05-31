import { useContext, useRef, useState } from 'react';

import { useGlobe, useAnimate } from './hooks';
import { GlobeContext } from '@/App';

import type { FrameData } from '@/types.ts';

const Globe = () => {
  const containerRef = useRef(null);
  const [frameData, setFrameData] = useState<FrameData | null>(null);
  const { setGlobe, setOpenModal } = useContext(GlobeContext);

  useGlobe(containerRef, setFrameData, setGlobe, setOpenModal);
  useAnimate(frameData);

  return (
    <div ref={containerRef} id='globe-visualizer' className='transition-colors'></div>
  )
};

export default Globe;
