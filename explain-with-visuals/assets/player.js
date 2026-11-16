function mountVisualPlayer(root, scene) {
  const stage = root.querySelector('[data-stage]');
  const controls = root.querySelector('[data-controls]');
  const caption = root.querySelector('[data-caption]');
  if (!stage || !controls || !caption) {
    throw new Error('A figure needs a stage, controls, and caption.');
  }
  if (!Array.isArray(scene.steps) || !scene.steps.length || typeof scene.render !== 'function') {
    throw new Error('A scene needs steps and a render function.');
  }
  for (const step of scene.steps) {
    if (typeof step.caption !== 'string' || !Object.hasOwn(step, 'state')) {
      throw new Error('Each step needs a caption and complete state.');
    }
    const duration = step.duration ?? scene.duration ?? 2400;
    if (!Number.isFinite(duration) || duration <= 0) {
      throw new Error('Playback durations must be positive milliseconds.');
    }
  }

  const document = root.ownerDocument;
  const view = document.defaultView;
  const listeners = new AbortController();
  const motion = view.matchMedia('(prefers-reduced-motion: reduce)');
  const previous = document.createElement('button');
  previous.type = 'button';
  previous.textContent = 'Previous';
  previous.dataset.previous = '';
  const play = document.createElement('button');
  play.type = 'button';
  play.dataset.play = '';
  const next = document.createElement('button');
  next.type = 'button';
  next.textContent = 'Next';
  next.dataset.next = '';
  const range = document.createElement('input');
  range.type = 'range';
  range.min = '0';
  range.max = String(scene.steps.length - 1);
  range.step = '1';
  range.setAttribute('aria-label', 'Step');
  const position = document.createElement('span');
  position.dataset.position = '';
  controls.replaceChildren(previous, play, range, next, position);
  controls.hidden = scene.steps.length < 2;

  let index = 0;
  let progress = 1;
  let running = false;
  let continuous = false;
  let holding = false;
  let frame = 0;
  let startedAt = 0;
  let startProgress = 0;
  let printedState = null;

  function updateControls() {
    play.textContent = running ? 'Pause' : (index === scene.steps.length - 1 && progress === 1 ? 'Replay' : 'Play');
    previous.disabled = index === 0;
    next.disabled = index === scene.steps.length - 1;
    range.value = String(index);
    range.setAttribute('aria-valuetext', scene.steps[index].caption);
    position.textContent = `${index + 1} / ${scene.steps.length}`;
  }

  function draw() {
    root.dataset.step = String(index);
    root.dataset.progress = String(progress);
    if (caption.textContent !== scene.steps[index].caption) {
      caption.textContent = scene.steps[index].caption;
    }
    scene.render({
      root,
      stage,
      index,
      state: scene.steps[index].state,
      from: scene.steps[Math.max(0, index - 1)].state,
      progress: motion.matches ? 1 : progress,
      reducedMotion: motion.matches
    });
    updateControls();
  }

  function pause() {
    view.cancelAnimationFrame(frame);
    running = false;
    updateControls();
  }

  function seek(target) {
    if (!Number.isInteger(target)) {
      throw new Error('A step index must be an integer.');
    }
    pause();
    index = Math.max(0, Math.min(scene.steps.length - 1, target));
    progress = 1;
    holding = false;
    draw();
  }

  function tick(now) {
    if (!root.isConnected) {
      pause();
      return;
    }
    const duration = scene.steps[index].duration ?? scene.duration ?? 2400;
    const elapsed = Math.min(1, startProgress + (now - startedAt) / duration);
    progress = holding ? 1 : elapsed;
    try {
      draw();
    } catch (error) {
      pause();
      caption.textContent = `Unable to render this step. ${error.message}`;
      throw error;
    }
    if (elapsed === 1) {
      if (!continuous || index === scene.steps.length - 1) {
        pause();
        return;
      }
      index += 1;
      progress = 0;
      holding = false;
      startProgress = 0;
      startedAt = now;
    }
    frame = view.requestAnimationFrame(tick);
  }

  function start(keepPlaying) {
    continuous = keepPlaying;
    startProgress = holding ? 0 : progress;
    startedAt = view.performance.now();
    running = true;
    updateControls();
    frame = view.requestAnimationFrame(tick);
  }

  previous.addEventListener('click', () => seek(index - 1), { signal: listeners.signal });
  range.addEventListener('input', () => seek(Number(range.value)), { signal: listeners.signal });
  next.addEventListener('click', () => {
    pause();
    index = Math.min(scene.steps.length - 1, index + 1);
    progress = 0;
    holding = false;
    draw();
    start(false);
  }, { signal: listeners.signal });
  play.addEventListener('click', () => {
    if (running) {
      pause();
      return;
    }
    if (progress === 1) {
      if (index === scene.steps.length - 1) {
        index = 0;
        holding = true;
      } else {
        index += 1;
        progress = 0;
        holding = false;
      }
    }
    draw();
    start(true);
  }, { signal: listeners.signal });
  motion.addEventListener('change', draw, { signal: listeners.signal });
  view.addEventListener('beforeprint', () => {
    printedState = { index, progress };
    pause();
    progress = 1;
    draw();
  }, { signal: listeners.signal });
  view.addEventListener('afterprint', () => {
    if (printedState) {
      index = printedState.index;
      progress = printedState.progress;
      printedState = null;
      draw();
    }
  }, { signal: listeners.signal });

  draw();
  return {
    seek,
    pause,
    destroy() {
      pause();
      listeners.abort();
      scene.destroy?.();
    }
  };
}
