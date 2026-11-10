// Make the demo's renderer from a module, falling back to the oscillator synth whenever the
// injected module cannot be used: no createRenderer export, a throw while creating it, or a load()
// that rejects or reports failure. The demo never ends up with no sound and a stuck button.

/**
 * @param {Promise<{ createRenderer: Function }>} modulePromise the injected (or default) module
 * @param {{ createRenderer: Function }} fallbackModule the oscillator synth's module
 * @param {BaseAudioContext} context
 * @returns {Promise<{ renderer: { play: Function, allOff: Function }, notice: string }>}
 *   the renderer, loaded, and why the fallback plays instead ("" when it does not)
 */
export async function prepareRenderer(modulePromise, fallbackModule, context) {
  try {
    const module = await modulePromise;
    if (typeof module?.createRenderer !== "function") throw new Error("the module has no createRenderer export");
    const renderer = module.createRenderer({ context });
    // load() may be called more than once; a renderer must make it idempotent (or cache its promise).
    if (renderer.load && (await renderer.load()) === false) throw new Error(renderer.status?.message ?? "its sounds did not load");
    return { renderer, notice: "" };
  } catch (error) {
    return { renderer: fallbackModule.createRenderer({ context }), notice: ` (renderer module not used: ${error?.message ?? error}; oscillator synth)` };
  }
}
