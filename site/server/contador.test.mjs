import { describe, it, expect, vi } from "vitest";
import { lerOuIncrementar } from "./contador.mjs";

describe("lerOuIncrementar", () => {
  it("sem cliente redis, retorna count:null", async () => {
    const r = await lerOuIncrementar(null, "GET");
    expect(r).toEqual({ count: null });
  });

  it("POST incrementa via incr()", async () => {
    const cliente = { incr: vi.fn().mockResolvedValue(7) };
    const r = await lerOuIncrementar(cliente, "POST");
    expect(cliente.incr).toHaveBeenCalledWith("quiz:conclusoes");
    expect(r).toEqual({ count: 7 });
  });

  it("GET sem chave existente retorna 0", async () => {
    const cliente = { get: vi.fn().mockResolvedValue(null) };
    const r = await lerOuIncrementar(cliente, "GET");
    expect(cliente.get).toHaveBeenCalledWith("quiz:conclusoes");
    expect(r).toEqual({ count: 0 });
  });

  it("GET com chave existente retorna o valor como numero", async () => {
    const cliente = { get: vi.fn().mockResolvedValue("42") };
    const r = await lerOuIncrementar(cliente, "GET");
    expect(r).toEqual({ count: 42 });
  });

  it("erro no redis retorna count:null (gracioso, nunca quebra)", async () => {
    const cliente = { incr: vi.fn().mockRejectedValue(new Error("timeout")) };
    const r = await lerOuIncrementar(cliente, "POST");
    expect(r).toEqual({ count: null });
  });
});
