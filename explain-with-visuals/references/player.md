# Build a portable figure

Author the geometry and state transitions for the explanation. Use the shared player for playback controls and complete-state seeking. The stage may contain SVG, HTML, or a canvas used by an authored spatial renderer.

## Package a figure

Run the packager from this skill's `scripts` directory, or substitute its actual absolute path.

```bash
python package_figure.py --figure diagram.svg --title "How the mechanism works" --caption "A concise explanatory caption." --output explanation.html
python package_figure.py --figure diagram.svg --scene scene.js --title "How the mechanism works" --output explanation.html
python package_figure.py --figure diagram.svg --scene scene.js --title "How the mechanism works" --format fragment --output figure-fragment.html
```

Supply SVG with a `viewBox`, useful title and description, and inline presentation attributes. Supply extra styles with `--style figure.css`. Start every ordinary rule with `__ROOT__` so the packager can scope it to the generated figure ID. Use the bundled CSS variables for the background, foreground, muted labels, structural lines, and accent. Define and explain additional category colors when needed.

Keep style and script tags in their separate input files. Use local `[data-part="name"]` queries for scene elements. The packager namespaces IDs, `url(#...)` references, fragment links, and accessible label references. Use data attributes or scoped classes for CSS selectors. Each separately packaged fragment receives a distinct root ID. Regenerate with a new ID when embedding another instance of the same figure.

The output embeds the supplied code and bundled assets. Inline any further dependencies and images required by the scene, and verify offline operation. The packager does not download dependencies. Open the completed HTML in a browser to inspect the figure and exercise its controls.

## Define a scene

Define `createScene(root)` in the JavaScript input. Return a `steps` array and a `render` function. Each step supplies a caption and a complete `state`. An optional duration controls playback pacing in milliseconds, with 2400 ms as the default. Keep actual process time in the explanatory data and labels.

```javascript
function createScene(root) {
  const marker = root.querySelector('[data-part="marker"]');
  const value = root.querySelector('[data-part="value"]');
  return {
    duration: 2400,
    steps: [
      { caption: 'The item begins at the entrance.', state: { x: 40 } },
      { caption: 'It moves to the inspection point.', state: { x: 180 } },
      { caption: 'It reaches the exit.', state: { x: 320 } }
    ],
    render({ state, from, progress }) {
      const x = from.x + (state.x - from.x) * progress;
      marker.setAttribute('cx', String(x));
      value.textContent = `${Math.round(x)} mm`;
    }
  };
}
```

This snippet documents the API. Author a diagram whose geometry and captions express the actual mechanism. A moving point can represent a physical item, a selected observation, or another entity only when its route is meaningful.

The render callback receives `root`, `stage`, `index`, `state`, `from`, `progress`, and `reducedMotion`. `state` is the target snapshot and `from` is the immediately preceding snapshot, even after seeking. `progress` ranges from zero to one. A direct seek and a reduced-motion render use one. Set every scene property that can vary from these arguments. Keep the stored snapshots immutable.

Derive moving positions from the model or an SVG path. Update labels, occupancy, active routes, and counters from the same state. For transient moving objects, define their visibility for both endpoints. Use the same rendering function for a static export at a selected step.

The player initializes at the first complete state. Next animates one transition. Previous and the slider seek directly to a complete state. Play continues from the current state or a paused transition. Replay returns to the beginning. Print captures the current complete step and hides controls. Reduced motion keeps state changes and controls available while rendering each transition at its endpoint.

`mountVisualPlayer(root, scene)` returns `seek(index)`, `pause()`, and `destroy()`. The packager mounts it automatically. A custom host can retain the returned controller and call `destroy()` before removing an interactive figure. An optional `scene.destroy()` releases resources owned by a canvas or spatial renderer.

## Verify reuse

Check the authored scene through its controls. Seek to an intermediate state from both directions and compare the geometry and values. Pause mid-transition and resume. Replay after the last step. Verify the reduced-motion view and two independently packaged instances in one document. Check the static SVG or image separately when it will be embedded in Markdown.
