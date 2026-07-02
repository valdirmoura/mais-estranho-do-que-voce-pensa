export interface CoreMeta {
  fonte: string;
  ano: number;
  salario_minimo: number;
  total_pop: number;
  total_n: number;
  dims: [string, string[]][];
}

export interface Core {
  meta: CoreMeta;
  cells: Record<string, [number, number]>;
}

export interface Bonus {
  meta: {
    fonte: string;
    n: number;
    religiao: string[];
    politica: string[];
    niveis: string[];
  };
  dist: Record<string, Record<string, Record<string, number>>>;
}

export type Resultado =
  | { tipo: "exato"; umEmX: number; pessoas: number; nAmostral: number }
  | { tipo: "piso"; limiteUmEm: number };
