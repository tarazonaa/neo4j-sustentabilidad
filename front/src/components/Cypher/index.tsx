import {
  useContext,
  useState
} from "react";

import type { Camera } from "three";
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

import countryData from "@/assets/countries.json";

import { GlobeContext } from "@/App";

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
    handleQuery({cypher: value, globe});
    setCypher(value);
  }

  return (
    <Select onValueChange={onValueChange}>
      <SelectTrigger className="w-10/12 dark text-gray-300 border-gray-500 text-xs">
        <SelectValue placeholder="Run CYPHER">
          {cypher}
        </SelectValue>
      </SelectTrigger>
      <SelectContent className="dark border-0 bg-[#14141f]">
        <SelectGroup className="dark">
          <SelectLabel>Queries</SelectLabel>
          <SelectSeparator/>
          {queries.map((query) => (
            <SelectItem id={query.label} key={query.value} value={query.value} onSelect={(e) => console.log(e)}>
              {query.label}
            </SelectItem>
          ))}
        </SelectGroup>
        
      </SelectContent>
    </Select>
  )
}

interface HandleQueryParams {
  cypher: string;
  globe: any;
  camera?: Camera;
}

// Esto ahorita solo colorea USA de rojo (falta usar los datos del api y maybe agregar labels?)
const handleQuery = ({cypher, globe}: HandleQueryParams) => {
  if (!globe) return;
  let coordinates: any = null;

  console.log("Running query: ", cypher);

  globe
    .hexPolygonsData()
    .filter((d: any) => d.properties["ISO_A3"] == "USA")
    .forEach((d:any) => {
      d["__threeObj"].material.color = new Color('#FF0000');
      console.log(d)
      if (coordinates == null)
        coordinates = countryData.countriesCollection["USA"].coordinates;
    });
  
  if (!coordinates) return;
}