# AUEVO local decision and document register

Status: working draft, 1 November 2026. This register indexes the new repository
documents only. It does not claim to replace or reconcile the external Master
Document Index, approve v1.2, or archive an established document.

## Documents

| ID | Active repository location | Version/status |
| --- | --- | --- |
| LOCAL-STATUS | `docs/PROJECT_STATUS.md` | Working evidence inventory |
| C3-SPEC | `docs/THIRD_COMPILER_SPEC_v0.1.md` | v0.1 DRAFT, founder review pending |
| MEDIA-SPEC | `docs/EVO_MEDIA_SPEC_v0.1.md` | v0.1 DRAFT, founder review pending |
| LOCAL-DECISIONS | This file | Working decision/proposal log |

Draft master v1.2 and logic review v0.1 were read from the user's attachments.
They remain separate source documents; no duplicate active master PDF was added
to this repository. Their established permanent location is not verified here.
V1.1 remains established according to the received master draft, but its full
contents were not directly received. Future controlled releases should preserve
superseded versions/history and index their source IDs and locations; do not
archive v1.1 on the strength of these local drafts.

## Decisions and proposals

| ID | Status/origin | Record |
| --- | --- | --- |
| D-001 | User direction | Compiler 1/2/3 are not architecturally complete; existing state compiler is a component. Apply authoritative wording in status and README. |
| D-002 | User direction | Power Platform remains paused and outside the local critical path. Do not infer current configuration from a report. |
| D-003 | User direction and current code | NFT/blockchain exports excluded; sampled recording JSON supersedes historical NFT-style export. |
| D-004 | Draft review proposal | Separate source, measurements, deterministic transformations, optional interpretation, canonical state, telemetry and artifacts. Full enforcement not yet implemented. |
| D-005 | Prototype proposal, OPEN | Portable local JSON authority; possible later Dataverse mirror. No production platform decision claimed. |
| D-006 | OPEN | Final canonical dimensions and meanings. Preserve five legacy Orb channels only for compatibility. No final AUEVO equation. |
| D-007 | OPEN | Audio-analysis location: source stage vs separate service. Source preservation and measured/derived labels required whichever is chosen. |
| D-008 | Compatibility behavior; future semantics OPEN | Intensity/focus/activity/complexity remain explicitly chosen configuration for current code, not inferred psychological state. Future measurement-derived dimensions need separate transforms/evaluation. |
| D-009 | Draft proposal | 369 is AUEVO_DEFINED; digital-root/3-6-9 effects are experimental transformations; live response gets a distinct name. No physical resonance claim. |
| D-010 | Draft proposal | Read-only baseline + bounded live modulation; neutral conditions restore baseline. Not currently guaranteed by renderer. |
| D-011 | Draft proposal | Content hash excludes run time/ID; run envelope separately hashed. Same inputs reproduce semantic state without claiming changing timestamps produce identical package bytes. |
| D-012 | User-requested specifications | Draft the two controlled specifications before implementing new orchestration, dimensions, four-mode playback or experimental mappings. |
| D-013 | OPEN | Identity record ownership/retention: labels may be configured, never measured from audio. Removed export labels are not silently restored. |

## Next evidence to collect

- Confirm the Windows binaries are built from the pulled checkout and explicit
  output paths are honored; the manual JSON copy was a workaround.
- Obtain external controlled sources only if needed for a specific feature;
  do not block synthetic adapter development on unrelated archives.
- Designate and preserve a founder-owned original for Prototype 001 with actual
  technical properties and permissions; existing recorded demos are test evidence.
- Record any future approvals of open semantic/measurement choices explicitly;
  drafting a proposal or publishing an environment does not approve them.

Documentation-only change: no executable behavior, master release, configuration
publication, cloud deployment, Power Platform setup or source archive mutation.

## Implementation increment after drafting

Legacy adapter v0.1 uses an explicitly incomplete schema and Python sorted-JSON
hashing, preserving the distinction from the proposed full contract/JCS encoding.
Its local snapshot command is opt-in and preserves existing outputs. This does
not close D-005 through D-011 or approve new dimensions/formulas. Seven adapter
tests and five compiler cases pass; no playback, master promotion or Power
Platform changes are included.

## Local Compiler 3 prototype increment

Implemented a separate `AUEVO-Compiler3Prototype/v0.1` compatibility package and
synthetic demo; the final controlled contract and canonical semantics remain
open. No new audio mapping or dimension set approved. Package changes are
observed differences, not presumed founder-approved corrections. Claims can
block compilation on conflict but cannot override evidence. Explicit local
permissions and manual retention are a prototype boundary, not a production
rights or identity system. The Python test suite now contains 19 passing cases.
