# Recovered sensor binding selector

`discovery::bound_sensor` reconstructs the decision logic in `CamHwIsp20::getBindedSnsEntNmByVd`, ELF entry `0x25430` (Ghidra `0x35430`), from the pinned `librkaiq.so`. It accepts an already constructed, ordered sensor inventory. **It does not populate the live inventory or create/configure media links.**

The original traverses the `mSensorHwInfos` inventory, whose native global object is at ELF `0x1adcdc`. For each candidate:

1. Skip names containing `1608`, and skip candidates without an ISP descriptor.
2. If a CIF descriptor exists, substring-match the requested video path against its four path fields. Otherwise match the two ISP path fields. CIF presence prevents fallback to ISP paths.
3. Matching `FakeCamera` or `_s_` names return immediately without checking the media device.
4. For other names, check the associated `/dev/mediaN`. An inaccessible path skips the candidate. If the path exists but opening a media object fails, the original returns null immediately rather than trying the next candidate.
5. Missing sensor entity or zero links skips the candidate. The original checks the **first link's complete flags value equals 1**, rather than masking an enabled bit. Flags 3 or 5 therefore do not match. Preserve this pinned behavior for equivalence; do not treat it as a general media-topology recommendation.
6. Return the first eligible name in inventory order, or null if none qualifies.

The function accepts a null query (returns null). An empty query matches any path through native `strstr`, and a partial path such as `/dev/video1` can match `/dev/video10`. The Rust API deliberately preserves these details; callers should pass a complete resolved path. Embedded NUL bytes are outside the checked string API domain. There is no inference that this selector alone establishes an enabled end-to-end camera path.

## Independent comparison

`mise run camera:rust:binding` executes the original ARM selector under Unicorn with 1,000 deterministic controlled inventories. Native linked-inventory traversal and smart-pointer increment/decrement instructions execute normally; reference counts are checked for balance. `strstr`, path access, formatting, and media helper calls have explicit stubs. The native function chooses which probes to invoke and which candidate to return. Unexpected imported dependencies fail the harness. [Report](binding-equivalence.json).

The initial translation reversed two inferred string roles; exact comparisons exposed this and the mapping was corrected against binary literal addresses. Tests cover empty/null and partial queries, no sensors, multiple candidates, ISP/CIF precedence, special names, absent descriptors, media access/open/entity failures, zero links and several link-flag combinations.

These checks do not verify the stubbed media operations or the library's global inventory-population code. The remaining implementation must discover sensor entities and ISP/CIF associations on the actual media graph, populate ordered records, and inspect links without relying on vendor initialization. The existing camera inventory command provides raw entities/device nodes but does not yet supply that complete native inventory.
