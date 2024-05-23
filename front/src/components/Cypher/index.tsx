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
  useState
} from "react";

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

  return (
    <Select onValueChange={(value) => setCypher(value)}>
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

