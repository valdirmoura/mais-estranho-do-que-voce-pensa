export function codificar(indices: number[]): string {
  return indices.join(".");
}

export function decodificar(
  s: string,
  dims: [string, string[]][]
): number[] | null {
  const partes = s.split(".");
  if (partes.length !== dims.length) return null;
  const idx = partes.map((p) => Number(p));
  const ok = idx.every(
    (v, i) => Number.isInteger(v) && v >= 0 && v < dims[i][1].length
  );
  return ok ? idx : null;
}
