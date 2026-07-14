import { describe, it, expect, vi } from "vitest";
import { registrarEvento, lerEstatisticas } from "./eventos.mjs";

describe("registrarEvento", () => {
  it("sem cliente redis, retorna ok:false", async () => {
    expect(await registrarEvento(null, "visita")).toEqual({ ok: false });
  });

  it("tipo desconhecido retorna ok:false sem tocar no redis", async () => {
    const cliente = { incr: vi.fn() };
    expect(await registrarEvento(cliente, "qualquercoisa")).toEqual({ ok: false });
    expect(cliente.incr).not.toHaveBeenCalled();
  });

  it("visita incrementa quiz:visitas", async () => {
    const cliente = { incr: vi.fn().mockResolvedValue(1) };
    expect(await registrarEvento(cliente, "visita")).toEqual({ ok: true });
    expect(cliente.incr).toHaveBeenCalledWith("quiz:visitas");
  });

  it("share incrementa quiz:shares", async () => {
    const cliente = { incr: vi.fn().mockResolvedValue(3) };
    expect(await registrarEvento(cliente, "share")).toEqual({ ok: true });
    expect(cliente.incr).toHaveBeenCalledWith("quiz:shares");
  });

  it("erro no redis retorna ok:false (gracioso, nunca quebra)", async () => {
    const cliente = { incr: vi.fn().mockRejectedValue(new Error("timeout")) };
    expect(await registrarEvento(cliente, "visita")).toEqual({ ok: false });
  });
});

describe("lerEstatisticas", () => {
  it("sem cliente redis, retorna tudo null", async () => {
    expect(await lerEstatisticas(null)).toEqual({
      visitas: null, shares: null, conclusoes: null,
    });
  });

  it("chaves ausentes viram 0", async () => {
    const cliente = { mGet: vi.fn().mockResolvedValue([null, null, null]) };
    expect(await lerEstatisticas(cliente)).toEqual({
      visitas: 0, shares: 0, conclusoes: 0,
    });
    expect(cliente.mGet).toHaveBeenCalledWith([
      "quiz:visitas", "quiz:shares", "quiz:conclusoes",
    ]);
  });

  it("valores string do redis viram números", async () => {
    const cliente = { mGet: vi.fn().mockResolvedValue(["10", "2", "5"]) };
    expect(await lerEstatisticas(cliente)).toEqual({
      visitas: 10, shares: 2, conclusoes: 5,
    });
  });

  it("erro no redis retorna tudo null", async () => {
    const cliente = { mGet: vi.fn().mockRejectedValue(new Error("timeout")) };
    expect(await lerEstatisticas(cliente)).toEqual({
      visitas: null, shares: null, conclusoes: null,
    });
  });
});
