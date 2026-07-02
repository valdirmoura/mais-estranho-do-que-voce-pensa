import type { Core, Bonus, Resultado } from "./tipos";

export const fe3 = (f6: number) => [0, 0, 1, 1, 2, 2][f6];
export const es3 = (e5: number) => [0, 0, 1, 2, 2][e5];

export function buscar(core: Core, indices: number[]): Resultado {
  const cell = core.cells[indices.join("|")];
  if (!cell) return { tipo: "piso", limiteUmEm: core.meta.total_n };
  const [peso, n] = cell;
  return {
    tipo: "exato",
    umEmX: Math.round(core.meta.total_pop / peso),
    pessoas: Math.round(peso),
    nAmostral: n,
  };
}

export function buscarBonus(
  core: Core,
  bonus: Bonus,
  indices: number[],
  rel: number,
  pol: number
): Resultado {
  const base = buscar(core, indices);
  const [sexo, f6, regiao, , e5] = indices;
  const chaves = [
    `${regiao}|${sexo}|${fe3(f6)}|${es3(e5)}`,
    `${regiao}|${es3(e5)}`,
    `${es3(e5)}`,
    "",
  ];
  let p: number | undefined;
  for (let nivel = 0; nivel < 4; nivel++) {
    const grupo = bonus.dist[String(nivel)]?.[chaves[nivel]];
    if (grupo) {
      p = grupo[`${rel}|${pol}`] ?? 0;
      break;
    }
  }
  if (p === undefined || p <= 0)
    return { tipo: "piso", limiteUmEm: core.meta.total_n };
  if (base.tipo === "piso") return base;
  const share = (1 / base.umEmX) * p;
  return {
    tipo: "exato",
    umEmX: Math.round(1 / share),
    pessoas: Math.round(core.meta.total_pop * share),
    nAmostral: base.nAmostral,
  };
}
