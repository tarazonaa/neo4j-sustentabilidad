import {
  useContext,
  useState
} from "react";

import { Color } from "three";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
  SelectSeparator
} from "@/components/ui/select";

import * as API from "./queries";

import { GlobeContext } from "@/App";
import { GLOBE_SETTINGS } from "@/components/Globe/constants";

import type ThreeGlobe from "three-globe";

const queries = [
  { 
    value: "MATCH (c:Country) RETURN c", 
    label: "List countries",
  },
  {
    value: "MATCH (c:Country)-[:NEIGHBOR]->(n:Country) RETURN c, n",
    label: "List countries and neighbors",
  },
]

export default function CypherSearch() {
  const [cypher, setCypher] = useState("Run CYPHER");
  const { globe } = useContext(GlobeContext);

  const onValueChange = (value: string) => {
    if (value == "")
      return;

    handleQuery({cypher: value, globe});
    setCypher(value);
  }

  const clear = () => {
    handleClear(globe);
    setCypher("");
  }

  return (
    <div className="w-11/12 flex flex-row gap-2">
    <Select onValueChange={onValueChange} value={cypher}>
      <SelectTrigger className="w-11/12 dark text-gray-300 border-gray-500 text-xs">
        <SelectValue placeholder="Run CYPHER">
          {cypher}
        </SelectValue>
      </SelectTrigger>
      <SelectContent className="dark border-0 bg-[#14141f]">
        <SelectGroup className="dark">
          <SelectLabel>Queries</SelectLabel>
          <SelectSeparator/>
          {queries.map((query) => (
            <SelectItem id={query.label} key={query.value} value={query.value}>
              {query.label}
            </SelectItem>
          ))}
        </SelectGroup>
        
      </SelectContent>
    </Select>
    <button onClick={clear} className="w-16 dark rounded-lg text-white p-1">&#10060;</button>
    </div>
  )
}

interface HandleQueryParams {
  cypher: string;
  globe: null | ThreeGlobe;
}

const handleQuery = async ({cypher, globe}: HandleQueryParams) => {
  if (!globe) return;

  const countries = await API.getCountries();
  if (!countries || !countries?.length) return;

  const codes = new Set(countries.map((country: any) => String(country?.code).trim()));

  const markers = document.querySelectorAll(".country-marker");
  markers?.forEach((marker) => {
    const countryCode = marker?.id?.split("-")?.[1];
    if (codes.has(countryCode)) {
      marker.classList.remove("hidden")
    } else {
      marker.classList.add("hidden")
    }
  });

  const minColor = new Color(GLOBE_SETTINGS.COLORS.highlightPolygonMin);
  const maxColor = new Color(GLOBE_SETTINGS.COLORS.highlightPolygonMax);
  const inactiveColor = new Color(GLOBE_SETTINGS.COLORS.inactivePolygon);

  const colorSpace = (alpha: number) => minColor.clone().lerp(maxColor, alpha);

  let current = 0.15;

  globe
    .hexPolygonsData()
    .forEach((d: any) => {
      if (codes.has(d?.properties?.ISO_A3)) {
        d.__threeObj.material.color = colorSpace(current);
        current += 0.15;
      } else {
        d.__threeObj.material.color = inactiveColor;
      }
    });
}

const handleClear = (globe: null | ThreeGlobe) => {
  if (!globe) return;

  const defaultColor = new Color(GLOBE_SETTINGS.COLORS.polygon);
  globe
    .hexPolygonsData()
    .forEach((d: any) => {
      d.__threeObj.material.color = defaultColor;
    });
  
  const markers = document.querySelectorAll(".country-marker");
  markers?.forEach((marker) => {
    marker.classList.add("hidden")
  });
}