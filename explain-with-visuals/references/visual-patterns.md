# Choosing explanatory detail

Use the question to select what becomes an object, a boundary, a coordinate, or a transition. These examples illustrate reusable decisions across subjects. Adapt their structure and verify the facts for the current task.

## Contents

- [General decomposition operations](#general-decomposition-operations)
- [Partition and conservation](#example-a--partition-and-conservation)
- [Overlap and multiplicity](#example-b--overlap-and-multiplicity)
- [Transformation and grouping](#example-c--transformation-and-grouping)
- [A conditional process](#example-d--a-conditional-process)
- [Geometry and constrained motion](#example-e--geometry-and-constrained-motion)
- [Dimensions and slices](#example-f--dimensions-and-slices)
- [Selective annotations](#selective-annotations)

## General decomposition operations

| Relationship to expose | Useful graphical operation | Check |
| --- | --- | --- |
| Whole and parts | Open a container, cut a section, or explode an assembly. | Each part has a relevant role and an identifiable boundary. |
| Input and output correspondence | Track selected items through splitting, merging, reordering, or transformation. | Identity and multiplicity follow the stated rule. |
| Quantity and capacity | Show equal units, a calibrated extent, or occupied and available regions. | Counts, scale, and totals agree. |
| Spatial intersection | Overlay boundaries and label the actual intersecting regions. | The value belongs to the area or volume it measures. |
| Time and resource use | Align intervals or lanes on a shared axis. | Duration, overlap, waiting, and causality are distinguishable. |
| Conditional behavior | Show the current state, the condition, and the resulting branch. | A representative journey reaches its stated outcome. |
| Influence and constraint | Show what is connected, what is fixed, and what can change. | The drawing exposes the mechanism behind the effect. |
| Many dimensions | Show named axes, selected slices, and linked views. | Every visible dimension has a stated interpretation. |

For a new domain, translate the question into these relationships before choosing shapes. Add a more suitable representation when the subject calls for it.

## Example A — partition and conservation

**Brief**

Show how a five-liter supply can fill a two-liter vessel and leave three liters in the supply. Treat the vessels as ideal and assume no loss.

**Representation**

Draw calibrated vessel cross-sections. Mark one-liter intervals, identify the transferred amount, and place the capacity labels beside their containers. Use height as volume only for a constant cross-section. Otherwise derive the level from the vessel geometry or use a separate calibrated volume scale.

**Sequence**

Show the initial five liters, transfer two liters while keeping the running total at five, and show the final three-plus-two partition. Keep the transferred portion identifiable if provenance is the question. A single liquid color suffices when only total volume matters.

**Reader check**

The reader can locate the two parts of the original amount and verify their sum. The operation generalizes to budget allocation, storage partitions, and inventory splitting.

## Example B — overlap and multiplicity

**Brief**

Show why adding the areas of two overlapping rectangular service regions counts their shared area twice.

**Representation**

Use a shared coordinate plane with the true region boundaries. Place a count of one in each exclusive region and two in the intersection. Let the labels or a key explain region identity and counting multiplicity. Use distinct visual channels if both must be visible together.

**Sequence**

Highlight the contribution from each region in turn, then inspect the shared area. Keep the geometry stable so the duplicated contribution is visible in place.

**Reader check**

The reader can point to the exact area that was counted twice. The operation transfers to set union, coverage, repeated scans, and volume intersections.

## Example C — transformation and grouping

**Brief**

Two orders contain three and five parcels. Show how they share an eight-slot carrier while remaining attributable to their orders.

**Representation**

Draw each parcel as one unit and each order as a labeled group. Show eight carrier positions. Assign an order label to every parcel or use two explained colors with persistent group labels. Show parcel-to-position correspondence as the parcels move into the carrier.

**Detail decision**

Subdivision exposes count and capacity. Group identity explains attribution after combining. If the question instead concerns only total carrier weight, use measured weights and totals appropriate to that question.

**Reader check**

The reader can recover which positions belong to each order and count every occupied slot. The same representation applies to memory layout, grouped observations, and allocating work to resources.

## Example D — a conditional process

**Brief**

A manufactured item passes inspection or returns for one rework attempt. After a failed second inspection it leaves for disposal. Show what happens to one initially rejected item that passes on its second inspection.

**Representation**

Draw the item's route through inspection, rework, and completed storage. Label the test and attempt count at the decision. Give each item a persistent identifier. Show the disposal branch with its condition so the exit from repeated failure is apparent.

**Sequence**

Arrival, failed inspection, rework, second inspection, completed storage. Place the item at its current location and animate the actual connecting route. If capacity explains waiting, open the relevant buffer and show its occupied slots.

**Reader check**

The reader can trace the advertised journey and identify the condition selecting every transition. This applies to software retries, document review, and repair workflows.

## Example E — geometry and constrained motion

**Brief**

Explain how a rigid door moves around a fixed hinge axis and why points farther from that axis travel farther during the same rotation.

**Representation**

Show the hinge axis, the door plane, two marked points at different distances, and their circular paths. Attach angle and radius labels to the correct geometry. Use a plan view when it exposes the distances well. Add a linked spatial view when the hinge orientation needs explanation.

**Sequence**

Rotate both points by the same angle from the same rigid-body model. Preserve their identities and label the common angle. Verify the trajectories from the model used to draw them.

**Reader check**

The reader can identify what is fixed, what rotates, and why the path lengths differ. This transfers to robot joints, rotating tools, and changing coordinate frames.

## Example F — dimensions and slices

**Brief**

Show measurements indexed by location, day, and sensor type, then compare one sensor type across days and locations.

**Representation**

Name the indices and their sizes. Represent the chosen sensor type as a two-dimensional location-by-day grid. Show other types as labeled neighboring slices or expose them with a selector. Use values or a calibrated scale for the measurement itself. Preserve the selected cell's indices across views.

**Detail decision**

The extra view makes membership and indexing inspectable. Add a depth axis when it clarifies slice organization. Use additional selectors or repeated views for further dimensions.

**Reader check**

The reader can locate one observation, change one index at a time, and state what each axis means. This transfers to tensors, experimental datasets, and multidimensional inventories.

## Selective annotations

Place names on identifiable objects, dimensions along the measured extent, conditions beside decision branches, and counts inside the region they count. Use a leader line when attachment is ambiguous. Preserve enough nearby context in a close-up to show where it belongs. Name a repeated unit once and label exceptional units where their behavior changes.

Record why each visual distinction helps the inspection task. If removing a distinction leaves the task equally clear, simplify it. If the reader must infer an unseen boundary or intermediate transformation, expose it. Treat both omissions and gratuitous subdivisions as design failures to repair.
