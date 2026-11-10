// Serve ts/ statically (no dependencies) so demo/index.html can import ../dist/index.js.
// Usage: npm run demo   (builds, then serves http://localhost:5174/demo/)
// ACCOMPY_DEMO_MOUNT=<dir> also serves that folder at /mount/ (for example an injected renderer
// module and its files: http://localhost:5174/demo/?renderer=/mount/<module>.js).
import { createReadStream, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const PORT = Number(process.env.PORT ?? 5174);
const MOUNT = process.env.ACCOMPY_DEMO_MOUNT ? resolve(process.env.ACCOMPY_DEMO_MOUNT) : null;
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".map": "application/json", ".md": "text/markdown" };

createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url ?? "/", "http://x").pathname);
  const mounted = MOUNT && pathname.startsWith("/mount/");
  const root = mounted ? MOUNT : ROOT;
  const path = normalize(join(root, mounted ? pathname.slice("/mount".length) : pathname));
  let file = path.endsWith("/") ? join(path, "index.html") : path;
  try {
    if (file !== root && !file.startsWith(root + sep)) throw new Error("outside root");
    if (statSync(file).isDirectory()) file = join(file, "index.html");
    statSync(file);
  } catch {
    res.writeHead(404).end("not found");
    return;
  }
  res.writeHead(200, { "content-type": TYPES[extname(file)] ?? "application/octet-stream", "content-length": statSync(file).size });
  createReadStream(file).pipe(res);
}).listen(PORT, "127.0.0.1", () => console.log(`accompy demo: http://localhost:${PORT}/demo/`));
