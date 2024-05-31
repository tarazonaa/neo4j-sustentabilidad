import regions from "./regions.json";

const RegionSet = new Set(regions.map((region) => region.name));

export {
  RegionSet,
  regions,
}