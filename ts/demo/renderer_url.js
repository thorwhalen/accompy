// Which renderer module the demo may import from ?renderer=: an http(s) URL on the page's own
// origin, or none. A link that named another origin (or a data:/javascript:/file: URL, or any URL
// on a page whose origin is opaque) would run code the page did not choose, so it is refused.

/**
 * @param {string} search the page's query string
 * @param {string} base the page's URL
 * @returns {string | null} the module URL, or null when none was asked for
 */
export function injectedRendererUrl(search = location.search, base = location.href) {
  const value = new URLSearchParams(search).get("renderer");
  if (!value) return null;
  const page = new URL(base);
  const url = new URL(value, base);
  const web = (u) => u.protocol === "http:" || u.protocol === "https:";
  if (!web(page) || page.origin === "null") throw new Error("refusing a renderer module on a page without a web origin");
  if (!web(url) || url.origin !== page.origin) throw new Error(`refusing a renderer module from another origin (${url.origin})`);
  return url.href;
}
