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
  it("refuses another origin, including a protocol-relative URL", () => {
    expect(() => injectedRendererUrl("?renderer=https://evil.example/r.js", page)).toThrow(/another origin/);
    expect(() => injectedRendererUrl("?renderer=//evil.example/r.js", page)).toThrow(/another origin/);
    expect(() => injectedRendererUrl("?renderer=data:text/javascript,alert(1)", page)).toThrow(/another origin/);
  });
});
