import { lazy, useState, useEffect, Suspense, createContext } from 'react';
import Navbar from './components/Navbar';

import type { GlobeContextProps } from './types';

const Globe = lazy(() => import('./components/Globe'));

export const GlobeContext = createContext<GlobeContextProps>({
  globe: null, setGlobe: null,
});

function App() {
  const [closed, setClosed] = useState(false);

  const [globe, setGlobe] = useState<any>();

  useEffect(() => {
    setTimeout(() => {
      setClosed(false);
    }, 500);
  }, [closed]);

  return (
    <GlobeContext.Provider value={{
      globe, setGlobe,
    }}>
      <div className="flex m-0 p-0 flex-[1] justify-center -z-10">
        <div className='globe-container'>
          <Suspense fallback={<div className='loading-container'><div className='lds-ripple'><div></div><div></div></div></div>}>
            <Globe />
          </Suspense>
        </div>
      </div>
      <Navbar />
      <div className='opacity-box'></div> 
    </GlobeContext.Provider>
  );
}

export default App;