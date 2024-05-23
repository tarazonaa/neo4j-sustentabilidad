import { Logo, Info } from "../Icons";


export default function Navbar() {
  return (
    <nav>
      <div className="logo-area">
        <Logo className={"globus-logo"} />
        <h1 className="logo">Earth4j</h1>
      </div>
      <div className="search-area">
        {/* Searchbar is not working in this repo idk */}
      </div>
      <div className="github-wrapper">
        <a
          className="info-link"
          href="https://github.com/tarazonaa/neo4j-sustentabilidad"
          aria-label="Info"
        >
          <Info />
        </a>
      </div>
    </nav>
  );
}
