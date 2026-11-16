---
name: explain-with-visuals
description: Create explanatory SVG figures, process replays, and spatial or 3D views from a focused brief. Use for a requested diagram or visual explanation, or when a larger task needs a figure that reveals structure, quantities, transformations, or causal relationships.
---

# Explain with visuals

Turn a question into a figure the reader can inspect to answer it. Make quantities, relationships, boundaries, and changes visible. Use this skill for the visual portion of any task, independently of the calling workflow or subject domain. Honor the user's requested scope and format.

## Receive a brief

Accept ordinary prose, a structured brief, or relevant context already established in the conversation. Resolve these items from available information.

| Item | Purpose |
| --- | --- |
| Question or intended insight | Establish what the reader should be able to locate, compare, trace, measure, or predict. |
| Content and evidence | Establish the relevant objects, relationships, rules, quantities, and sources. Mark illustrative assumptions. |
| Reader context | Use familiar terms and identify the prerequisite that needs to become visible. |
| Scenario, when useful | Establish an initial condition, events, conditions for transitions, and resulting states. |
| Presentation | Choose a static SVG, standalone HTML, embedded figure, or spatial view. Respect the caller's destination and surrounding design. |

Infer routine presentation choices. Resolve facts that change the meaning from supplied evidence or explicitly authorized sources. Return any unresolved semantic gap to the calling workflow. Keep the rest of its task progressing. Let the caller own audience dialogue, learning checkpoints, document assembly, and the final response.

## Choose what to expose

1. State the inspection task privately in one sentence, such as “follow one item through a transformation” or “see which region is counted twice.”
2. Identify the relationship that makes the answer true. It may involve containment, correspondence, partition, order, accumulation, allocation, geometry, overlap, dependency, conservation, or a change of state.
3. Start with the objects relevant to that relationship. Open an object when its internal parts, boundaries, or organization explain the result. Open a transformation when the correspondence between its inputs and outputs needs explanation.
4. For each subdivision, name what the reader gains from seeing its parts. Useful gains include count, position, identity, provenance, grouping, capacity, interaction, state, and physical structure. Merge subdivisions that carry no relevant distinction.
5. Stop when the reader can perform the inspection task using the drawing and its labels. Keep familiar surroundings compact. Use a close-up, linked view, or a later step when detail needs more room.

Choose detail by explanatory purpose. A diagram of a hierarchy, a process, a physical assembly, and a numerical operation can require different objects and scales. Read [visual-patterns.md](references/visual-patterns.md) when choosing a representation or when the obvious boxes leave the mechanism hidden. Its examples demonstrate decisions that transfer across subjects.

## Define the visual meaning

Before rendering, privately establish the following mappings.

- Assign a meaning to each visible unit. State whether it represents one item, an aggregate, a region, or an illustrative sample. Use actual counts when the argument depends on counting. Label aggregation and schematic scales explicitly.
- Map position, extent, and orientation to relevant relationships. Name axes, units, reference frames, boundaries, and thresholds near their geometry.
- Assign persistent identity or category meaning to color only when that distinction helps the reader. Keep the mapping stable across panels and time. Distinguish transient emphasis with a ring, weight, or another treatment. Pair color with labels, patterns, or shapes.
- Explain a mapping at its first use through direct labels or a nearby legend. Expand unfamiliar abbreviations. Attach annotations to the exact object or region they describe.
- Give arrows a consistent relationship and direction. Use separate treatments when transfer, dependency, force, and annotation pointers occur together. Preserve the input-to-output correspondence through splits, merges, and rearrangements.
- For each claimed transformation, expose enough of the action or rule to explain the result. Trace an exemplar through it. Verify conservation, multiplicity, dimensions, and boundary conditions where applicable.
- Use selected objects to illustrate a class only when the example preserves the relevant mechanism. State material simplifications and the limits of an analogy.

Treat textual labels as names, quantities, conditions, or brief explanations tied to the drawing. Allocate space to the visual relationship carrying the argument. Choose a readable composition with minimal crossings, stable alignment, and room for annotations.

## Choose a rendering method

- Use SVG for diagrams, arrangements, labeled geometry, and precise static figures. Use a responsive viewBox and legible text at the intended display size. Add an accessible title and description.
- Use SVG projection or an exploded view when a fixed spatial view explains the relationship. Use interactive 3D when inspecting orientation, depth, occlusion, or linked motion materially helps. Generate geometry and annotations from a consistent coordinate model.
- For higher-dimensional structures, name the dimensions mapped to visible axes. Represent further dimensions through slices, selectors, or repeated panels. Preserve the distinction between data coordinates and camera position.
- Use a shared state model for multiple views. Keep object identity, labels, and quantities consistent between overview, close-up, and spatial views.

Use readable typography compatible with the surrounding work. Favor direct labels, restrained color, and enough whitespace to resolve boundaries. Treat accurate geometry and annotations as part of correctness.

## Add motion when it explains a change

Write a short sequence of states and the events joining them. Give each state a reproducible complete description. Associate movement with a transfer, transformation, accumulation, condition, or physical change. Make the event and its cause inspectable at each step.

Preserve object identity and spatial context across steps. Express concurrent activity as concurrent when it matters. Distinguish actual system time from playback pacing. Support pause, step navigation, and seeking. Render a readable static state under reduced motion.

Use the bundled player for ordinary process replays. Read [player.md](references/player.md) before using it. It controls time and navigation while the authored scene controls geometry and meaning. Keep specialized interactions such as rotation or slicing local to their figure. Use a domain model for a claimed simulation and identify a scripted replay as illustrative when appropriate.

## Deliver a composable artifact

- For static figures, deliver a self-contained SVG. Embed it in Markdown with image syntax, useful alternative text, and a brief caption at the point where it is needed. Keep document image paths resolvable at the delivery destination.
- For motion or interactive 3D, deliver standalone HTML with its code and assets embedded. Provide a representative SVG or rendered image for Markdown and print when those are requested delivery surfaces. Link the interactive HTML from that static view. Markdown image embedding supplies the static view.
- For embedding into another HTML document, return a scoped figure fragment. Namespace IDs and SVG definitions, scope CSS and DOM queries, and verify multiple figures can coexist.
- Use `scripts/package_figure.py` to wrap an authored SVG or HTML stage and an optional scene. Read the command examples in [player.md](references/player.md). It supports standalone and fragment output and embeds the bundled player and styles.
- Return the artifact location, a one-sentence description, source references, and material assumptions or unresolved gaps to the caller. Apply the host's save and presentation rules when delivering directly to the user.

## Verify the explanation

Check the artifact through its actual delivery surface.

1. Perform the inspection task from the figure. Locate or trace the objects that answer the question. Check that its visual distinctions contribute relevant information.
2. Verify quantities, units, proportions, mapping across operations, and labels against the facts. For schematic geometry, make the simplification clear.
3. Follow every advertised scenario from its start to its stated outcome. Check branch conditions, arrow direction, joins, and intentional cycles. For relationship maps, verify the relationship being claimed without imposing an artificial process order.
4. Inspect label placement, crossings, clipping, occlusion, contrast, and the figure at its intended size. Verify referenced static images actually display.
5. For interactive work, test stepping, jumping forward and backward, pausing, replaying, and reduced motion. Check that counts and state match at the same step regardless of how it was reached. Check two instances together when producing fragments.

Fix failures that change the explanation before delivery. Report any remaining material uncertainty accurately.
