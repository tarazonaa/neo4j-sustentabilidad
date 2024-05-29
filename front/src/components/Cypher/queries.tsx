const API_URL = import.meta.env.VITE_API_URL;

export const getCountries = async () => (
  await fetch(`${API_URL}/countries`)
    .then((response) => response.json())
    .then((data) => data?.countries)
    .catch((error) => console.error(error))
);