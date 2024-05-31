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

import {
  questions,
  handleQuery
} from "./queries";

import { GlobeContext } from "@/App";
import { GLOBE_SETTINGS } from "@/components/Globe/constants";

import type ThreeGlobe from "three-globe";

const listing = questions.map((q, idx) => ({
  label: q.question,
  value: idx,
}));

export default function CypherSearch() {
  const { globe, setRegionData, setCountryData } = useContext(GlobeContext);
  const [message, setMessage] = useState("Run CYPHER");

  const onValueChange = (value: string) => {
    if (value == "")
      return;

    const idx = parseInt(value);

    setMessage(listing?.[idx].label);
    
    handleQuery({
      id: idx, 
      globe,
      setRegionData: setRegionData,
      setCountryData: setCountryData
    });
  }

  const clear = () => {
    setMessage("");
    handleClear(globe);
  }

  return (
    <div className="w-11/12 flex flex-row gap-2">
    <Select onValueChange={onValueChange}>
      <SelectTrigger className="w-11/12 dark text-gray-300 border-gray-500 text-xs">
        <SelectValue placeholder="Run CYPHER" value={message}>
          {message}
        </SelectValue>
      </SelectTrigger>
      <SelectContent className="dark border-0 bg-[#14141f]">
        <SelectGroup className="dark">
          <SelectLabel>Preguntas</SelectLabel>
          <SelectSeparator/>
          {listing.map((q) => (
            <SelectItem id={q.label} key={q.value} value={String(q.value)}>
              {q.label}
            </SelectItem>
          ))}
        </SelectGroup>
        
      </SelectContent>
    </Select>
    <button onClick={clear} className="w-16 dark rounded-lg text-white p-1">&#10060;</button>
    </div>
  )
}

const handleClear = (
  globe: null | ThreeGlobe,
  setRegionData: any,
  setCountryData: any
) => {
  if (!globe) return;

  const defaultColor = new Color(GLOBE_SETTINGS.COLORS.polygon);
  globe
    .hexPolygonsData()
    .forEach((d: any) => {
      d.__threeObj.material.color = defaultColor;
    });

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

  document.querySelectorAll(".country-marker")?.forEach((marker) => {
    marker.classList.add("hidden");
  });

  document.querySelectorAll(".region-marker")?.forEach((marker) => {
    marker.classList.add("hidden");
  });
}