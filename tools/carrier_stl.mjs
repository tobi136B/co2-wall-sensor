// Build a sensor carrier with the configurator code (site/carrier.js) in Node, for the CI check.
// Usage: node tools/carrier_stl.mjs PARAMS.json PROFILE OUT.stl   (model coordinates, like cad/stl)
import { readFileSync, writeFileSync } from "node:fs";
import Module from "manifold-3d";
import { buildCarrier, toStl } from "../site/carrier.js";

const [paramsFile, profile, out] = process.argv.slice(2);
const params = JSON.parse(readFileSync(paramsFile, "utf8"));
const wasm = await Module();
wasm.setup();
const carrier = buildCarrier(wasm, params.base, params.boards[profile]);
writeFileSync(out, Buffer.from(toStl(carrier, `sensor_carrier_${profile}`, false)));
console.log(`written: ${out} (${carrier.volume().toFixed(1)} mm3)`);
