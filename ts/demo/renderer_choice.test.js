import { describe, expect, it } from "vitest";
import { prepareRenderer } from "./renderer_choice.js";

const context = /** @type {BaseAudioContext} */ ({});
const oscillator = { createRenderer: () => ({ name: "oscillator", play() {}, allOff() {} }) };
const named = (name, extra = {}) => ({ createRenderer: () => ({ name, play() {}, allOff() {}, ...extra }) });

describe("prepareRenderer", () => {
  it("uses the injected module when it loads", async () => {
    const { renderer, notice } = await prepareRenderer(Promise.resolve(named("injected", { load: async () => true })), oscillator, context);
    expect(renderer.name).toBe("injected");
    expect(notice).toBe("");
  });
  it("falls back when the import fails", async () => {
    const { renderer, notice } = await prepareRenderer(Promise.reject(new Error("404")), oscillator, context);
    expect(renderer.name).toBe("oscillator");
    expect(notice).toMatch(/404/);
  });
  it("falls back when the module has no createRenderer", async () => {
    const { renderer, notice } = await prepareRenderer(Promise.resolve({}), oscillator, context);
    expect(renderer.name).toBe("oscillator");
    expect(notice).toMatch(/no createRenderer/);
  });
  it("falls back when createRenderer throws, load rejects, or load reports failure", async () => {
    const throws = { createRenderer: () => { throw new Error("boom"); } };
    const rejects = named("x", { load: async () => { throw new Error("no worklet"); } });
    const fails = named("x", { load: async () => false, status: { message: "bank 404" } });
    for (const [module, why] of [[throws, /boom/], [rejects, /no worklet/], [fails, /bank 404/]]) {
      const { renderer, notice } = await prepareRenderer(Promise.resolve(module), oscillator, context);
      expect(renderer.name).toBe("oscillator");
      expect(notice).toMatch(why);
    }
  });
});
