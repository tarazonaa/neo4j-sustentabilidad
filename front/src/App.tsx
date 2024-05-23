import './App.css';
import { lazy, useState, useEffect, Suspense, createContext } from 'react';
import Navbar from './components/Navbar';

const Globe = lazy(() => import('./components/Globe'));

export const GlobeContext = createContext({

});

function App() {
  const [closed, setClosed] = useState(false);

  useEffect(() => {
    setTimeout(() => {
      setClosed(false);
    }, 500);
  }, [closed]);

  return (
    <>
      <GlobeContext.Provider value={{
        closed,
        setClosed,
      }}>
        <div className="container">
          <div className='globe-container'>
            <Suspense fallback={<div className='loading-container'><div className='lds-ripple'><div></div><div></div></div></div>}>
              <Globe />
            </Suspense>
          </div>
        </div>
      </GlobeContext.Provider>
      <Navbar />
      <div className='opacity-box'></div> 
    </>
  );
}

export default App;