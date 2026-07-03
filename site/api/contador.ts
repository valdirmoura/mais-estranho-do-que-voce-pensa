import type { VercelRequest, VercelResponse } from "@vercel/node";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) return res.status(200).json({ count: null });
  const cmd = req.method === "POST" ? "INCR" : "GET";
  const r = await fetch(`${url}/${cmd}/quiz:conclusoes`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const j = (await r.json()) as { result?: string | number };
  res.status(200).json({ count: Number(j.result ?? 0) });
}
