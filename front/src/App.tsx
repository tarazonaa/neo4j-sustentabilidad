import { lazy, useState, useEffect, Suspense, createContext } from 'react';
import Navbar from './components/Navbar';

const Globe = lazy(() => import('./components/Globe'));

interface GlobeContextProps {
  globe: any;
  setGlobe: null | ((d: any) => void);
  camera: any;
  setCamera: null | ((d: any) => void);
  renderers: any[];
  setRenderers: any | ((d: any) => void);
}

export const GlobeContext = createContext<GlobeContextProps>({
  globe: null, setGlobe: null,
  camera: null, setCamera: null,
  renderers: [], setRenderers: null,
});

function App() {
  const [closed, setClosed] = useState(false);

  // Probs conviene cambiar estos 3 useStates a un solo objeto xd
  const [globe, setGlobe] = useState<any>();
  const [camera, setCamera] = useState<any>();
  const [renderers, setRenderers] = useState<any[]>([]);

  useEffect(() => {
    setTimeout(() => {
      setClosed(false);
    }, 500);
  }, [closed]);

  return (
    <GlobeContext.Provider value={{
      globe, setGlobe,
      camera, setCamera,
      renderers, setRenderers
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