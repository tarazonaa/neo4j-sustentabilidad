import { Color } from "three";
import type ThreeGlobe from "three-globe";

import { GLOBE_SETTINGS } from "@/components/Globe/constants";

import { RegionSet, regions } from "@/assets/regions.ts";

export const questions = [
  {
    question:
      "¿En qué regiones se ha avanzado / retrocedido por métrica en mayor / menor medida?",
    endpoint: "/api/metrics/by-region",
    returns: ["regions", "metrics"],
    strategies: ["absolute", "relative"],
    order: ["asc", "desc"],
  },
  {
    question:
      "¿Qué países han avanzado / retrocedido comparado vs otros en su región?",
    endpoint: "/api/metrics/by-country?strategy=absolute",
    returns: ["countries"],
    strategies: ["absolute", "relative"],
    order: ["asc", "desc"],
  },
  {
    question:
      "¿Qué métricas son las que más han avanzado / retrocedido globalmente?",
    endpoint: "/api/metrics/changes",
    returns: ["metrics"], // Didn't know wtf
  },
  {
    question: "¿Cuáles serían los 10 países a tomar como referencia?",
    endpoint: "/api/metrics/top-countries",
    returns: ["countries"],
  },
  {
    question:
      "¿Cuáles serían los 10 países donde más oportunidad hay? Y ¿qué les beneficiaría más?",
    endpoint: "/api/metrics/top-countries?order=asc",
    returns: ["countries"],
  },
  {
    question: "La distancia entre países, ¿afecta en algo los resultados?",
    endpoint: "/api/bonus",
    returns: ["countries"], // Maybe needs its own handler?
  },
];

const API_URL = import.meta.env.VITE_API_URL;

interface HandleQueryParams {
  id: number;
  globe: null | ThreeGlobe;
  setRegionData: ((d: any) => void) | null;
  setCountryData: ((d: any) => void) | null;
}

export const handleQuery = async ({
  id,
  globe,
  setRegionData,
  setCountryData,
}: HandleQueryParams) => {
  if (!globe) return;

  const endpoint = questions?.[id]?.endpoint;
  if (!endpoint) return;

  if (!setRegionData || !setCountryData) return;
  
  setRegionData((prev: any) => {
    const regionData = { ...prev };
    Object.keys(regionData).forEach((region) => {
      regionData[region] = {};
    });
    return regionData;
  })

  setCountryData((prev: any) => {
    const countryData = { ...prev };
    Object.keys(countryData).forEach((country) => {
      countryData[country] = {};
    });
    return countryData;
  });

  const response = await fetch(API_URL + endpoint)
    .then((res) => res.json())
    .catch((err) => console.error(err));

  if (!response?.data) return;

  if (questions?.[id]?.returns?.includes("regions")) {
    updateRegions(globe, response?.data, setRegionData);
  } else if (questions?.[id]?.returns?.includes("countries")) {
    updateCountries(globe, response?.data, setCountryData);
  }
};

const minColor = new Color(GLOBE_SETTINGS.COLORS.highlightPolygonMin);
const maxColor = new Color(GLOBE_SETTINGS.COLORS.highlightPolygonMax);
const inactiveColor = new Color(GLOBE_SETTINGS.COLORS.inactivePolygon);
const colorSpace = (alpha: number) => minColor.clone().lerp(maxColor, alpha);

const updateRegions = (
  globe: ThreeGlobe,
  regionData: any,
  setRegionData: ((d: any) => void) | null
) => {
  if (!setRegionData) return;
  const regionNames = new Set<string>();

  regionData.forEach((regionObj: any) => {
    const metric = regionObj?.metric;
    const value = regionObj?.value;
    const regionName = regionObj?.region;

    setRegionData((prev: any) => ({
      ...prev,
      [regionName]: {
        ...prev?.[regionName],
        [metric]: value,
      },
    }));

    regionName && regionNames.add(regionName);
  });

  // @ts-expect-error - set difference is defined?
  const unusedRegions = RegionSet?.difference(regionNames);
  const regionSlugs = new Set(regions.map((region) => {
    if (regionNames.has(region.name))
      return region.slug;
  }));

  if (unusedRegions) {
    const unusedCountries = new Set(
      regions
        .filter((region) => unusedRegions.has(region.name))
        .map((region) => region.countries)
        .flat()
    );

    globe.hexPolygonsData().forEach((d: any) => {
      if (unusedCountries.has(d?.properties?.ISO_A3)) {
        d.__threeObj.material.color = inactiveColor;
      }
    });
  }

  const markers = document.querySelectorAll(".region-marker");
  markers?.forEach((marker) => {
    const region = marker?.id?.split("label-")?.[1];
    if (regionSlugs.has(region)) {
      marker.classList.remove("hidden")
    } else {
      marker.classList.add("hidden")
    }
  });
};

const updateCountries = (
  globe: ThreeGlobe,
  countryData: any,
  setCountryData: ((d: any) => void) | null
) => {
  if (!setCountryData) return;
  const countryCodes = new Set<string>();

  countryData.forEach((countryObj: any) => {
    const metric = countryObj?.metric;
    const value = countryObj?.value;
    const countryCode = countryObj?.country;
    
    setCountryData((prev: any) => ({
      ...prev,
      [countryCode]: {
        ...prev?.[countryCode],
        [metric ?? "score"]: value,
      },
    }));

    countryCode && countryCodes.add(countryCode);
  });

  let current = 0;
  const increment = 1 / countryCodes.size;

  globe
    .hexPolygonsData()
    .forEach((d: any) => {
      if (countryCodes.has(d?.properties?.ISO_A3)) {
        d.__threeObj.material.color = colorSpace(current);
        current += increment
      } else {
        d.__threeObj.material.color = inactiveColor;
      }
    });
  
  const markers = document.querySelectorAll(".country-marker");
  markers?.forEach((marker) => {
    const country = marker?.id?.split("label-")?.[1];
    if (countryCodes.has(country)) {
      marker.classList.remove("hidden")
    } else {
      marker.classList.add("hidden")
    }
  });
}