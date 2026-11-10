// Serve ts/ statically (no dependencies) so demo/index.html can import ../dist/index.js.
// Usage: npm run demo   (builds, then serves http://localhost:5174/demo/)
import { createReadStream, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const PORT = Number(process.env.PORT ?? 5174);
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".map": "application/json" };

createServer((req, res) => {
  const path = normalize(join(ROOT, decodeURIComponent(new URL(req.url ?? "/", "http://x").pathname)));
  let file = path.endsWith("/") ? join(path, "index.html") : path;
  try {
    if (!file.startsWith(ROOT)) throw new Error("outside root");
    if (statSync(file).isDirectory()) file = join(file, "index.html");
    statSync(file);
  } catch {
    res.writeHead(404).end("not found");
    return;
  }
  res.writeHead(200, { "content-type": TYPES[extname(file)] ?? "application/octet-stream" });
  createReadStream(file).pipe(res);
}).listen(PORT, "127.0.0.1", () => console.log(`accompy demo: http://localhost:${PORT}/demo/`));
