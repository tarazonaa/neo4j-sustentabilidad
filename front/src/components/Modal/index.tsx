import { useContext } from 'react';
import { GlobeContext } from '@/App';

export default function CountryModal({ 
  openModal, 
  setOpenModal 
}: {
  openModal: string | null;
  setOpenModal: (value: string | null) => void;
}) {
  const { countryData } = useContext(GlobeContext);

  if (!openModal || !countryData) return null;

  const country = countryData[openModal];

  const fields = Object.keys(country ?? {});
  if (!fields) return null;

  return (
    <div className={`absolute top-0 right-0 z-10 bg-[#1E1E2E] text-gray-300 rounded-xl w-[20vw] p-10 m-10 ${openModal ? 'is-active' : 'hidden'}`}>
      <header className="text-xl p-4 text-center font-bold">
        <p className="modal-card-title">{openModal}</p>
      </header>
      <hr className='mb-4'/>
      <section className="modal-card-body">
        <div className="content">
          { fields.map((field, index) => {
              if (field == 'iso2' || field == 'coordinates')
                return null;
              return <p key={index}><strong>{field}: </strong>{countryData[openModal][field]}</p>
            })
          }
        </div>
      </section>
      <div className="flex justify-center flex-row py-6">
        <button className="modal-close" aria-label="close" onClick={() => setOpenModal(null)}>
          <span aria-hidden="true">❌</span>
        </button>
      </div>
    </div>
  );
}