import { existsSync, mkdirSync, copyFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const siteDir = dirname(dirname(fileURLToPath(import.meta.url)));
const origemDir = join(siteDir, "..", "pipeline", "out");
const destinoDir = join(siteDir, "public", "data");

mkdirSync(destinoDir, { recursive: true });

const core = join(origemDir, "core.json");
if (!existsSync(core)) {
  throw new Error(`core.json não encontrado em ${core}`);
}
copyFileSync(core, join(destinoDir, "core.json"));
console.log("core.json copiado para site/public/data/");

const bonus = join(origemDir, "bonus.json");
if (existsSync(bonus)) {
  copyFileSync(bonus, join(destinoDir, "bonus.json"));
  console.log("bonus.json copiado para site/public/data/");
} else {
  console.log("bonus.json ainda não disponível em pipeline/out/ — pulando (site funciona sem ele).");
}
