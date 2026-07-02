import { it, expect } from "vitest";
import { codificar, decodificar } from "./share";

const dims: [string, string[]][] = [
  ["sexo", ["H", "M"]],
  ["faixa_etaria", ["a", "b", "c", "d", "e", "f"]],
  ["regiao", ["N", "NE", "SE", "S", "CO"]],
  ["cor", ["b", "p", "pa", "am", "i"]],
  ["escolaridade", ["1", "2", "3", "4", "5"]],
  ["renda", ["1", "2", "3", "4", "5"]],
  ["trabalho", ["1", "2", "3", "4", "5"]],
  ["internet", ["s", "n"]],
];

it("ida e volta", () => {
  const idx = [1, 5, 4, 2, 0, 3, 2, 1];
  expect(decodificar(codificar(idx), dims)).toEqual(idx);
});

it("rejeita fora do domínio e lixo", () => {
  expect(decodificar("9.0.0.0.0.0.0.0", dims)).toBeNull();
  expect(decodificar("abc", dims)).toBeNull();
  expect(decodificar("1.1.1", dims)).toBeNull();
});
