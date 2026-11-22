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
  /** The injected renderer once created: released if it turns out not to be used. */
  let abandoned = null;
  try {
    const module = await modulePromise;
    if (typeof module?.createRenderer !== "function") throw new Error("the module has no createRenderer export");
    const renderer = module.createRenderer({ context });
    abandoned = renderer;
    // load() may be called more than once; a renderer must make it idempotent (or cache its promise).
    if (renderer.load && (await renderer.load()) === false) throw new Error(renderer.status?.message ?? "its sounds did not load");
    return { renderer, notice: "" };
  } catch (error) {
    await closeRenderer(abandoned);
    return { renderer: fallbackModule.createRenderer({ context }), notice: ` (renderer module not used: ${error?.message ?? error}; oscillator synth)` };
  }
}

/**
 * Release a renderer that is no longer used (swapped out, or abandoned by the fallback): its
 * optional close() frees what it holds (a connected synth, a decoded bank). Never throws: a
 * renderer that fails to close must not break the swap.
 * @param {{ close?: Function } | null | undefined} renderer
 */
export async function closeRenderer(renderer) {
  try {
    await renderer?.close?.();
  } catch {
    /* nothing more to release */
  }
}
