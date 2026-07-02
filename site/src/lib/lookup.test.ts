import { describe, it, expect } from "vitest";
import { buscar, buscarBonus, fe3, es3 } from "./lookup";
import type { Core, Bonus } from "./tipos";

const core: Core = {
  meta: {
    fonte: "t",
    ano: 2024,
    salario_minimo: 1412,
    total_pop: 160_000_000,
    total_n: 400_000,
    dims: [
      ["sexo", ["H", "M"]],
      ["faixa_etaria", ["a", "b", "c", "d", "e", "f"]],
      ["regiao", ["N", "NE", "SE", "S", "CO"]],
      ["cor", ["b", "p", "pa", "am", "i"]],
      ["escolaridade", ["1", "2", "3", "4", "5"]],
      ["renda", ["1", "2", "3", "4", "5"]],
      ["trabalho", ["1", "2", "3", "4", "5"]],
      ["internet", ["s", "n"]],
    ],
  },
  cells: { "0|1|2|2|2|1|0|0": [16_000_000, 40_000] },
};

const bonus: Bonus = {
  meta: {
    fonte: "t",
    n: 2000,
    religiao: ["Cat", "Ev", "Out", "Sem"],
    politica: ["Esq", "Cen", "Dir", "NP"],
    niveis: [
      "regiao|sexo|faixa3|escol3",
      "regiao|escol3",
      "escol3",
      "global",
    ],
  },
  dist: {
    "0": { "2|0|0|1": { "1|2": 0.25 } },
    "1": {},
    "2": {},
    "3": { "": { "1|2": 0.2 } },
  },
};

describe("lookup", () => {
  it("célula existente: 1 em 10", () => {
    const r = buscar(core, [0, 1, 2, 2, 2, 1, 0, 0]);
    expect(r).toEqual({
      tipo: "exato",
      umEmX: 10,
      pessoas: 16_000_000,
      nAmostral: 40_000,
    });
  });

  it("célula ausente: piso = total_n", () => {
    const r = buscar(core, [1, 1, 2, 2, 2, 1, 0, 0]);
    expect(r).toEqual({ tipo: "piso", limiteUmEm: 400_000 });
  });

  it("bônus usa nível 0 quando disponível", () => {
    // indices: sexo=0, faixa=1 (fe3->0), regiao=2, escol=2 (es3->1)
    const r = buscarBonus(core, bonus, [0, 1, 2, 2, 2, 1, 0, 0], 1, 2);
    // 1/10 * 0.25 = 1/40
    expect(r).toEqual(expect.objectContaining({ tipo: "exato", umEmX: 40 }));
  });

  it("bônus recua até o global", () => {
    const b2: Bonus = {
      ...bonus,
      dist: { "0": {}, "1": {}, "2": {}, "3": { "": { "1|2": 0.2 } } },
    };
    const r = buscarBonus(core, b2, [0, 1, 2, 2, 2, 1, 0, 0], 1, 2);
    expect(r).toEqual(expect.objectContaining({ umEmX: 50 })); // 1/10 * 0.2
  });

  it("grupos espelham o python", () => {
    expect([0, 1, 2, 3, 4, 5].map(fe3)).toEqual([0, 0, 1, 1, 2, 2]);
    expect([0, 1, 2, 3, 4].map(es3)).toEqual([0, 0, 1, 2, 2]);
  });
});
