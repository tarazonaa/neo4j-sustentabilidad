import { Info } from "../Icons";
import CypherSearch from "../Cypher";

export default function Navbar() {
  return (
    <nav className="h-24 w-full z-10 bg-[#1e1e2e] absolute bottom-0 m-0 p-0 flex justify-center">
      <div className="flex flex-row gap-10 h-full w-6/12 min-w-96 justify-center items-center mt-1">
      <div className="flex">
        <h1 className="text-gray-300 font-bold">Earth4j</h1>
      </div>
        <CypherSearch />
      <div className="flex justify-center items-center mt-1 github-wrapper group">
        <a
          href="https://github.com/tarazonaa/neo4j-sustentabilidad"
          aria-label="Info"
        >
          <Info />
        </a>
      </div>
      </div>
    </nav>
  );
}
