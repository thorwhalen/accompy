// Which renderer module the demo may import from ?renderer=: same origin as the page, or none.
// A link that named another origin would run that origin's code in the page, so it is refused.

/**
 * @param {string} search the page's query string
 * @param {string} base the page's URL
 * @returns {string | null} the module URL, or null when none was asked for
 */
export function injectedRendererUrl(search = location.search, base = location.href) {
  const value = new URLSearchParams(search).get("renderer");
  if (!value) return null;
  const url = new URL(value, base);
  if (url.origin !== new URL(base).origin) throw new Error(`refusing a renderer module from another origin (${url.origin})`);
  return url.href;
}
