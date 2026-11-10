import { describe, expect, it } from "vitest";
import { injectedRendererUrl } from "./renderer_url.js";

const page = "http://localhost:5174/demo/";

describe("injectedRendererUrl", () => {
  it("is null without ?renderer=", () => {
    expect(injectedRendererUrl("", page)).toBeNull();
  });
  it("resolves a relative or same-origin module", () => {
    expect(injectedRendererUrl("?renderer=/mount/r.js", page)).toBe("http://localhost:5174/mount/r.js");
    expect(injectedRendererUrl("?renderer=./r.js", page)).toBe("http://localhost:5174/demo/r.js");
  });
  it("refuses another origin: another host, a protocol-relative URL, another port, another scheme", () => {
    for (const value of ["https://evil.example/r.js", "//evil.example/r.js", "http://localhost:9999/r.js", "https://localhost:5174/r.js"]) {
      expect(() => injectedRendererUrl(`?renderer=${encodeURIComponent(value)}`, page)).toThrow(/another origin/);
    }
  });
  it("refuses data:, javascript: and blob: URLs", () => {
    for (const value of ["data:text/javascript,alert(1)", "javascript:alert(1)", "blob:http://localhost:5174/x"]) {
      expect(() => injectedRendererUrl(`?renderer=${encodeURIComponent(value)}`, page)).toThrow(/another origin/);
    }
  });
  it("refuses anything on a page without a web origin (file:, opaque)", () => {
    expect(() => injectedRendererUrl("?renderer=data:text/javascript,x", "file:///tmp/demo/index.html")).toThrow(/web origin/);
    expect(() => injectedRendererUrl("?renderer=./r.js", "file:///tmp/demo/index.html")).toThrow(/web origin/);
  });
});
