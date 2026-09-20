# Ablation Arms Human-Grading Packet v1

## Grading rules (read first)

- Grade every expected fact per arm: Supported / Partial / Unsupported.
- Reason and Evidence reference are blank for the grader.
- Locked FULL grades are reference only; they must not determine arm grades.
- 'No verifiable claims' does NOT automatically mean Unsupported: grade whether each fact is established, and respect abstention cases.
- NO-VERIFICATION rule: evaluate timeline observation/correlation/inference TEXT against each fact; judge whether the fact is established by that text and its evidence, not whether it reads as prose.
- Do not infer grades from mechanical statuses.

## Per-case index

case | facts | no-temporal output | no-verification output | no-planning output
| I01 | 3 | empty-report | timeline-6-items | empty-report |
| I02 | 2 | empty-report | failure:validation | empty-report |
| I03 | 2 | empty-report | timeline-6-items | empty-report |
| I04 | 1 | empty-report | timeline-13-items | empty-report |
| I05 | 1 | empty-report | empty-timeline | empty-report |
| I06 | 1 | empty-report | empty-timeline | empty-report |
| I07 | 1 | empty-report | timeline-13-items | empty-report |
| I08 | 2 | empty-report | timeline-6-items | empty-report |
| I09 | 1 | empty-report | timeline-11-items | empty-report |
| I10 | 2 | empty-report | timeline-6-items | empty-report |
| I11 | 2 | empty-report | failure:validation | empty-report |
| I12 | 2 | empty-report | timeline-6-items | empty-report |
| I13 | 2 | empty-report | timeline-9-items | empty-report |
| I14 | 2 | empty-report | timeline-6-items | empty-report |
| I15 | 2 | empty-report | timeline-11-items | empty-report |
| I16 | 1 | empty-report | empty-timeline | empty-report |
| I17 | 1 | empty-report | empty-timeline | empty-report |
| I18 | 1 | empty-report | empty-timeline | empty-report |
| I19 | 2 | empty-report | timeline-11-items | empty-report |
| I20 | 1 | empty-report | timeline-6-items | empty-report |
| I21 | 1 | empty-report | timeline-11-items | empty-report |
| I22 | 3 | empty-report | timeline-11-items | empty-report |
| I23 | 1 | empty-report | empty-timeline | empty-report |
| I24 | 1 | empty-report | timeline-6-items | empty-report |
| I25 | 2 | empty-report | empty-timeline | empty-report |
| I26 | 2 | empty-report | empty-timeline | empty-report |
| I27 | 1 | empty-report | empty-timeline | empty-report |
| I28 | 1 | empty-report | empty-timeline | empty-report |
| I29 | 1 | empty-report | timeline-7-items | empty-report |
| I30 | 1 | empty-report | empty-timeline | empty-report |

## Cases

### I01 — Show person detections in anomaly/Burglary/Burglary032_x264.mp4 between 27 and 49 seconds.

Expected facts (locked FULL grade in brackets):
- [F01] person detected in 9 evidence windows [locked full: Partial]
- [F02] windows span 27.7s to 48.9s [locked full: Supported]
- [F03] Burglary surveillance-event label present in all 9 windows [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f22, anomaly/Burglary/Burglary032_x264.mp4:f14

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____
- F03: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 48.933, "evidence_ids": ["anomaly/Burglary/Burglary032_x264.mp4:f13", "anomaly/Burglary/Burglary032_x264.mp4:f14", "anomaly/Burglary/Burglary032_x264.mp4:f15", "anomaly/Burglary/Burglary032_x264.mp4:f16", "anomaly/Burglary/Burglary032_x264.mp4:f17", "anomaly/Burglary/Burglary032_x264.mp4:f18", "anomaly/Burglary/Burglary032_x264.mp4:f19", "anomaly/Burglary/Burglary032_x264.mp4:f20", "a
- correlations: {"description": "The evidence indicates compatible Burglary hypotheses from the surveillance_event model persist across adjacent windows from approximately 27.7s to 48.9s.", "evidence_ids": ["anomaly/Burglary/Burglary032_x264.mp4:f13", "anomaly/Burglary/Burglary032_x264.mp4:f14", "anomaly/Burglary/Burglary032_x264.mp4:f15", "anomaly/Burglary/Burglary032_x264.mp4:f16", "anomaly/Burglary/Burglary032
- correlations: {"description": "The evidence indicates all listed windows belong to the same Phase 2D incident anomaly/Burglary/Burglary032_x264.mp4:i0.", "evidence_ids": ["anomaly/Burglary/Burglary032_x264.mp4:f13", "anomaly/Burglary/Burglary032_x264.mp4:f14", "anomaly/Burglary/Burglary032_x264.mp4:f15", "anomaly/Burglary/Burglary032_x264.mp4:f16", "anomaly/Burglary/Burglary032_x264.mp4:f17", "anomaly/Burglary/
- correlations: {"description": "The evidence indicates person detections from the object source temporally overlap Burglary hypotheses from the surveillance_event source in the same windows; this is source overlap only and does not confirm involvement.", "evidence_ids": ["anomaly/Burglary/Burglary032_x264.mp4:f13", "anomaly/Burglary/Burglary032_x264.mp4:f15", "anomaly/Burglary/Burglary032_x264.mp4:f16", "anomaly
- inferences: {"evidence_ids": ["anomaly/Burglary/Burglary032_x264.mp4:f13", "anomaly/Burglary/Burglary032_x264.mp4:f14", "anomaly/Burglary/Burglary032_x264.mp4:f15", "anomaly/Burglary/Burglary032_x264.mp4:f16", "anomaly/Burglary/Burglary032_x264.mp4:f17", "anomaly/Burglary/Burglary032_x264.mp4:f18", "anomaly/Burglary/Burglary032_x264.mp4:f19", "anomaly/Burglary/Burglary032_x264.mp4:f20", "anomaly/Burglary/Burg
- inferences: {"evidence_ids": ["anomaly/Burglary/Burglary032_x264.mp4:f13", "anomaly/Burglary/Burglary032_x264.mp4:f14", "anomaly/Burglary/Burglary032_x264.mp4:f15", "anomaly/Burglary/Burglary032_x264.mp4:f16", "anomaly/Burglary/Burglary032_x264.mp4:f17", "anomaly/Burglary/Burglary032_x264.mp4:f18", "anomaly/Burglary/Burglary032_x264.mp4:f19", "anomaly/Burglary/Burglary032_x264.mp4:f20", "anomaly/Burglary/Burg
plan queries: [{"query": "person", "source": "object"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____
- F03: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f22, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f14, anomaly/Burglary/Burglary032_x264.mp4:f20

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____
- F03: Grade: ____ Reason: ____ Evidence reference: ____

### I02 — Show car detections in anomaly/RoadAccidents/RoadAccidents011_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] car detected in 34 evidence windows [locked full: Partial]
- [F02] windows span 0.0s to 71.9s [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f23, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f15, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f30, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f17, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f21, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f26, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f1

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
FAILURE: {"error": "persistent_event windows are not adjacent or nearby", "stage": "3e", "type": "validation"}
plan queries: [{"query": "car", "source": "object"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f2, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f0, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f32, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f19, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f20, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f25, anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f23

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

### I03 — Show person detections in normal/Normal_Videos_251_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] person detected in 7 evidence windows [locked full: Supported]
- [F02] video carries no annotated anomaly interval [locked full: Unsupported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: normal/Normal_Videos_251_x264.mp4:f4, normal/Normal_Videos_251_x264.mp4:f2, normal/Normal_Videos_251_x264.mp4:f6, normal/Normal_Videos_251_x264.mp4:f5, normal/Normal_Videos_251_x264.mp4:f3, normal/Normal_Videos_251_x264.mp4:f1, normal/Normal_Videos_251_x264.mp4:f0

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 13.467, "evidence_ids": ["normal/Normal_Videos_251_x264.mp4:f0", "normal/Normal_Videos_251_x264.mp4:f1", "normal/Normal_Videos_251_x264.mp4:f2", "normal/Normal_Videos_251_x264.mp4:f3", "normal/Normal_Videos_251_x264.mp4:f4", "normal/Normal_Videos_251_x264.mp4:f5", "normal/Normal_Videos_251_x264.mp4:f6"], "observation": {"evidence_ids": ["normal/Normal_Videos_251_x264.mp4:f0", "normal/
- correlations: {"description": "The evidence indicates f0 through f6 belong to the same Phase 2D incident normal/Normal_Videos_251_x264.mp4:i0.", "evidence_ids": ["normal/Normal_Videos_251_x264.mp4:f0", "normal/Normal_Videos_251_x264.mp4:f1", "normal/Normal_Videos_251_x264.mp4:f2", "normal/Normal_Videos_251_x264.mp4:f3", "normal/Normal_Videos_251_x264.mp4:f4", "normal/Normal_Videos_251_x264.mp4:f5", "normal/Norm
- correlations: {"description": "The available evidence suggests the RoadAccidents model hypothesis persists across adjacent windows from 0.0s to 13.467s with confidences 0.5804-0.9384.", "evidence_ids": ["normal/Normal_Videos_251_x264.mp4:f0", "normal/Normal_Videos_251_x264.mp4:f1", "normal/Normal_Videos_251_x264.mp4:f2", "normal/Normal_Videos_251_x264.mp4:f3", "normal/Normal_Videos_251_x264.mp4:f4", "normal/Nor
- correlations: {"description": "The evidence indicates person object detections overlap in time with RoadAccidents surveillance-event hypotheses in the same windows, representing source agreement only and not confirmation of involvement.", "evidence_ids": ["normal/Normal_Videos_251_x264.mp4:f0", "normal/Normal_Videos_251_x264.mp4:f1", "normal/Normal_Videos_251_x264.mp4:f2", "normal/Normal_Videos_251_x264.mp4:f3"
- inferences: {"evidence_ids": ["normal/Normal_Videos_251_x264.mp4:f0", "normal/Normal_Videos_251_x264.mp4:f1", "normal/Normal_Videos_251_x264.mp4:f2", "normal/Normal_Videos_251_x264.mp4:f3", "normal/Normal_Videos_251_x264.mp4:f4", "normal/Normal_Videos_251_x264.mp4:f5", "normal/Normal_Videos_251_x264.mp4:f6"], "text": "The available evidence suggests at least one person was detectable throughout 0.0s to 13.467
- inferences: {"evidence_ids": ["normal/Normal_Videos_251_x264.mp4:f0", "normal/Normal_Videos_251_x264.mp4:f1", "normal/Normal_Videos_251_x264.mp4:f2", "normal/Normal_Videos_251_x264.mp4:f3", "normal/Normal_Videos_251_x264.mp4:f4", "normal/Normal_Videos_251_x264.mp4:f5", "normal/Normal_Videos_251_x264.mp4:f6"], "text": "The evidence is consistent with persons co-occurring with vehicles and a RoadAccidents model
plan queries: [{"query": "person", "source": "object"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: normal/Normal_Videos_251_x264.mp4:f4, normal/Normal_Videos_251_x264.mp4:f3, normal/Normal_Videos_251_x264.mp4:f6, normal/Normal_Videos_251_x264.mp4:f2, normal/Normal_Videos_251_x264.mp4:f1, normal/Normal_Videos_251_x264.mp4:f0, normal/Normal_Videos_251_x264.mp4:f5

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

### I04 — Show driving-car activity in anomaly/RoadAccidents/RoadAccidents016_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] driving car activity present in 14 evidence windows [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f34, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f10, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f11, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f12

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 4.133, "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1"], "observation": {"evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1"], "text": "The evidence indicates car and person detections overlapping generic-action driving-car hypotheses (con
- timeline: {"end_time": 10.533, "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4"], "observation": {"evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4"], "text": "The evidence indicates car and person detections overlapping driving-car hypotheses (confidence 0.1263
- timeline: {"end_time": 27.6, "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f9", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f10", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f11", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f12"], "observation": {"evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8", "an
- timeline: {"end_time": 72.934, "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f34"], "observation": {"evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f34"], "text": "The model produced a driving-car hypothesis (confidence 0.157) overlapping a RoadAccidents hypothesis (confidence 0.9826) with no object detections reported."}, "start_time": 72.534}
- correlations: {"description": "Compatible RoadAccidents hypotheses with overlapping driving-car hypotheses persist across adjacent windows from 0.0s to 4.133s.", "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1"], "type": "persistent_event"}
- correlations: {"description": "Compatible RoadAccidents hypotheses with overlapping driving-car hypotheses persist across adjacent windows from 6.4s to 10.533s.", "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4"], "type": "persistent_event"}
- correlations: {"description": "Compatible RoadAccidents hypotheses persist across nearby windows from 17.067s to 27.6s, with driving-car hypotheses in the first four windows and a motorcycling hypothesis in the last window.", "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f9", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f10", "anomaly
- correlations: {"description": "Object car/person detections co-occur in the same windows with generic-action hypotheses and RoadAccidents hypotheses; this is source agreement only, never confirmation.", "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccid
- correlations: {"description": "Generic-action driving-car hypothesis co-occurs with RoadAccidents hypothesis in the same late window with no object detections; source agreement only.", "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f34"], "type": "cross_source_support"}
- correlations: {"description": "Early windows from 0.0s occur before the late isolated window at 72.534s-72.934s.", "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f34"], "type": "temporal_sequence"}
- correlations: {"description": "All cited evidence records belong to the same Phase 2D incident anomaly/RoadAccidents/RoadAccidents016_x264.mp4:i0.", "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4", "anomaly/RoadAccidents/RoadAccid
- inferences: {"evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f9", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f10", "an
- inferences: {"evidence_ids": ["anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f9", "anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f10", "an
plan queries: [{"query": "driving car", "source": "generic_action"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f34, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f7, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f6, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f10, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f30, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f2, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f16, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I05 — Show garbage-collecting activity in anomaly/Shoplifting/Shoplifting020_x264.mp4 between 0 and 100 seconds.

Expected facts (locked FULL grade in brackets):
- [F01] garbage collecting activity present in 2 evidence windows [locked full: Unsupported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shoplifting/Shoplifting020_x264.mp4:f23, anomaly/Shoplifting/Shoplifting020_x264.mp4:f1, anomaly/Shoplifting/Shoplifting020_x264.mp4:f37, anomaly/Shoplifting/Shoplifting020_x264.mp4:f29, anomaly/Shoplifting/Shoplifting020_x264.mp4:f30, anomaly/Shoplifting/Shoplifting020_x264.mp4:f38, anomaly/Shoplifting/Shoplifting020_x264.mp4:f35, anomaly/Shoplifting/Shoplifting020_x264.mp4:f27, anomaly/Shoplifting/Shoplifting020_x264.mp4:f6, anomaly/Shoplifting/Shoplifting020_x264.mp4:f5

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
plan queries: [{"query": "garbage-collecting", "source": "generic_action"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shoplifting/Shoplifting020_x264.mp4:f23, anomaly/Shoplifting/Shoplifting020_x264.mp4:f1, anomaly/Shoplifting/Shoplifting020_x264.mp4:f37, anomaly/Shoplifting/Shoplifting020_x264.mp4:f29, anomaly/Shoplifting/Shoplifting020_x264.mp4:f30, anomaly/Shoplifting/Shoplifting020_x264.mp4:f38, anomaly/Shoplifting/Shoplifting020_x264.mp4:f35, anomaly/Shoplifting/Shoplifting020_x264.mp4:f27, anomaly/Shoplifting/Shoplifting020_x264.mp4:f6, anomaly/Shoplifting/Shoplifting020_x264.mp4:f5

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I06 — Show extinguishing-fire activity in anomaly/Arson/Arson041_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] extinguishing fire activity present in 2 evidence windows [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Arson/Arson041_x264.mp4:f55, anomaly/Arson/Arson041_x264.mp4:f56, anomaly/Arson/Arson041_x264.mp4:f57, anomaly/Arson/Arson041_x264.mp4:f54, anomaly/Arson/Arson041_x264.mp4:f51, anomaly/Arson/Arson041_x264.mp4:f23, anomaly/Arson/Arson041_x264.mp4:f35, anomaly/Arson/Arson041_x264.mp4:f41, anomaly/Arson/Arson041_x264.mp4:f53, anomaly/Arson/Arson041_x264.mp4:f49

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
plan queries: [{"query": "extinguishing-fire", "source": "generic_action"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Arson/Arson041_x264.mp4:f55, anomaly/Arson/Arson041_x264.mp4:f56, anomaly/Arson/Arson041_x264.mp4:f57, anomaly/Arson/Arson041_x264.mp4:f54, anomaly/Arson/Arson041_x264.mp4:f51, anomaly/Arson/Arson041_x264.mp4:f23, anomaly/Arson/Arson041_x264.mp4:f35, anomaly/Arson/Arson041_x264.mp4:f41, anomaly/Arson/Arson041_x264.mp4:f53, anomaly/Arson/Arson041_x264.mp4:f49

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I07 — Show Arrest evidence in anomaly/Arrest/Arrest039_x264.mp4 between 0 and 120 seconds.

Expected facts (locked FULL grade in brackets):
- [F01] Arrest surveillance-event label present in 11 evidence windows [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Arrest/Arrest039_x264.mp4:f38, anomaly/Arrest/Arrest039_x264.mp4:f14, anomaly/Arrest/Arrest039_x264.mp4:f41, anomaly/Arrest/Arrest039_x264.mp4:f16, anomaly/Arrest/Arrest039_x264.mp4:f44, anomaly/Arrest/Arrest039_x264.mp4:f30, anomaly/Arrest/Arrest039_x264.mp4:f15, anomaly/Arrest/Arrest039_x264.mp4:f45, anomaly/Arrest/Arrest039_x264.mp4:f25, anomaly/Arrest/Arrest039_x264.mp4:f17

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 38.267, "evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f14", "anomaly/Arrest/Arrest039_x264.mp4:f15", "anomaly/Arrest/Arrest039_x264.mp4:f16", "anomaly/Arrest/Arrest039_x264.mp4:f17"], "observation": {"evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f14", "anomaly/Arrest/Arrest039_x264.mp4:f15", "anomaly/Arrest/Arrest039_x264.mp4:f16", "anomaly/Arrest/Arrest039_x264.mp4:f17"],
- timeline: {"end_time": 55.333, "evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f25"], "observation": {"evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f25"], "text": "The evidence indicates chair (5) and person (2) detections from 53.333-55.333s, with the model producing an Arrest hypothesis (0.3735) and low-confidence high kick (0.1103)."}, "start_time": 53.333}
- timeline: {"end_time": 66.0, "evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f30"], "observation": {"evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f30"], "text": "The evidence indicates chair (12) and person (3) detections from 64.0-66.0s, with the model producing an Arrest hypothesis (0.4844) and low-confidence side kick (0.1297)."}, "start_time": 64.0}
- timeline: {"end_time": 83.067, "evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f38"], "observation": {"evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f38"], "text": "The evidence indicates chair (6) and person (3) detections from 81.067-83.067s, with the model producing an Arrest hypothesis (0.5051) and low-confidence headbutting (0.0586)."}, "start_time": 81.067}
- timeline: {"end_time": 89.467, "evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f41"], "observation": {"evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f41"], "text": "The evidence indicates chair (6) and person (2) detections from 87.467-89.467s, with the model producing an Arrest hypothesis (0.49) and low-confidence drop kicking (0.1356)."}, "start_time": 87.467}
- timeline: {"end_time": 98.0, "evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f44", "anomaly/Arrest/Arrest039_x264.mp4:f45"], "observation": {"evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f44", "anomaly/Arrest/Arrest039_x264.mp4:f45"], "text": "The evidence indicates persistent chair (6-9) and person (2-3) detections from 93.867-98.0s. The model produced Arrest hypotheses in both adjacent windows (
- correlations: {"description": "Windows f14 and f15 are adjacent and both contain person and chair detections with the surveillance_event model producing an Arrest hypothesis, indicating persistence of compatible model output.", "evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f14", "anomaly/Arrest/Arrest039_x264.mp4:f15"], "type": "persistent_event"}
- correlations: {"description": "Windows f44 and f45 are adjacent and both contain person and chair detections with the surveillance_event model producing an Arrest hypothesis, indicating persistence of compatible model output.", "evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f44", "anomaly/Arrest/Arrest039_x264.mp4:f45"], "type": "persistent_event"}
- correlations: {"description": "All ten windows belong to the same Phase 2D incident anomaly/Arrest/Arrest039_x264.mp4:i0.", "evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f14", "anomaly/Arrest/Arrest039_x264.mp4:f15", "anomaly/Arrest/Arrest039_x264.mp4:f16", "anomaly/Arrest/Arrest039_x264.mp4:f17", "anomaly/Arrest/Arrest039_x264.mp4:f25", "anomaly/Arrest/Arrest039_x264.mp4:f30", "anomaly/Arrest/Arrest039_x
- correlations: {"description": "Person object detections and Arrest surveillance_event hypotheses co-occur in the same time windows, showing source agreement only and not confirmation that detected persons were involved.", "evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f15", "anomaly/Arrest/Arrest039_x264.mp4:f30", "anomaly/Arrest/Arrest039_x264.mp4:f38"], "type": "cross_source_support"}
- correlations: {"description": "The window at 36.267-38.267s occurs before the window at 53.333-55.333s.", "evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f17", "anomaly/Arrest/Arrest039_x264.mp4:f25"], "type": "temporal_sequence"}
- inferences: {"evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f14", "anomaly/Arrest/Arrest039_x264.mp4:f15", "anomaly/Arrest/Arrest039_x264.mp4:f17", "anomaly/Arrest/Arrest039_x264.mp4:f25", "anomaly/Arrest/Arrest039_x264.mp4:f30", "anomaly/Arrest/Arrest039_x264.mp4:f38", "anomaly/Arrest/Arrest039_x264.mp4:f41", "anomaly/Arrest/Arrest039_x264.mp4:f44", "anomaly/Arrest/Arrest039_x264.mp4:f45"], "text": "The
- inferences: {"evidence_ids": ["anomaly/Arrest/Arrest039_x264.mp4:f16"], "text": "The evidence indicates a single RoadAccidents hypothesis window interspersed among Arrest hypotheses, suggesting divergent model output rather than a confirmed separate event."}
plan queries: [{"query": "Arrest", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Arrest/Arrest039_x264.mp4:f16, anomaly/Arrest/Arrest039_x264.mp4:f26, anomaly/Arrest/Arrest039_x264.mp4:f31, anomaly/Arrest/Arrest039_x264.mp4:f15, anomaly/Arrest/Arrest039_x264.mp4:f27, anomaly/Arrest/Arrest039_x264.mp4:f44, anomaly/Arrest/Arrest039_x264.mp4:f7, anomaly/Arrest/Arrest039_x264.mp4:f41, anomaly/Arrest/Arrest039_x264.mp4:f37, anomaly/Arrest/Arrest039_x264.mp4:f42

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I08 — Show Shoplifting evidence in anomaly/Shoplifting/Shoplifting044_x264.mp4 between 0 and 60 seconds.

Expected facts (locked FULL grade in brackets):
- [F01] Shoplifting surveillance-event label present in 23 evidence windows [locked full: Supported]
- [F02] windows span 0.0s to 61.7s [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shoplifting/Shoplifting044_x264.mp4:f10, anomaly/Shoplifting/Shoplifting044_x264.mp4:f8, anomaly/Shoplifting/Shoplifting044_x264.mp4:f13, anomaly/Shoplifting/Shoplifting044_x264.mp4:f21, anomaly/Shoplifting/Shoplifting044_x264.mp4:f22, anomaly/Shoplifting/Shoplifting044_x264.mp4:f20, anomaly/Shoplifting/Shoplifting044_x264.mp4:f11, anomaly/Shoplifting/Shoplifting044_x264.mp4:f15, anomaly/Shoplifting/Shoplifting044_x264.mp4:f7, anomaly/Shoplifting/Shoplifting044_x264.mp4:f17

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 48.933, "evidence_ids": ["anomaly/Shoplifting/Shoplifting044_x264.mp4:f7", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f8", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f10", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f11", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f13", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f15", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f17", "anomal
- correlations: {"description": "The available evidence suggests Shoplifting-labeled surveillance-event outputs persist across nearby windows from ~14.9s to ~48.9s.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting044_x264.mp4:f7", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f8", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f10", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f11", "anomaly/Shoplifting/Shoplifti
- correlations: {"description": "All cited evidence records belong to the same Phase 2D incident anomaly/Shoplifting/Shoplifting044_x264.mp4:i0.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting044_x264.mp4:f7", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f8", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f10", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f11", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f13",
- correlations: {"description": "Within the cited windows, object-source person detections temporally coincide with surveillance-event-source Shoplifting hypotheses, indicating source agreement in time only and not confirmation.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting044_x264.mp4:f7", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f8", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f10", "anomaly/Shoplift
- inferences: {"evidence_ids": ["anomaly/Shoplifting/Shoplifting044_x264.mp4:f7", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f8", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f10", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f11", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f13", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f15", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f17", "anomaly/Shoplifting/Shopli
- inferences: {"evidence_ids": ["anomaly/Shoplifting/Shoplifting044_x264.mp4:f8", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f15", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f21", "anomaly/Shoplifting/Shoplifting044_x264.mp4:f22"], "text": "The evidence indicates suitcase detections temporally coincided with Shoplifting hypotheses in those windows, but temporal co-occurrence does not imply involvement or ca
plan queries: [{"query": "Shoplifting", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shoplifting/Shoplifting044_x264.mp4:f10, anomaly/Shoplifting/Shoplifting044_x264.mp4:f8, anomaly/Shoplifting/Shoplifting044_x264.mp4:f13, anomaly/Shoplifting/Shoplifting044_x264.mp4:f21, anomaly/Shoplifting/Shoplifting044_x264.mp4:f19, anomaly/Shoplifting/Shoplifting044_x264.mp4:f9, anomaly/Shoplifting/Shoplifting044_x264.mp4:f27, anomaly/Shoplifting/Shoplifting044_x264.mp4:f15, anomaly/Shoplifting/Shoplifting044_x264.mp4:f4, anomaly/Shoplifting/Shoplifting044_x264.mp4:f14

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

### I09 — Show Burglary evidence in anomaly/Burglary/Burglary033_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] Burglary surveillance-event label present in 20 evidence windows [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Burglary/Burglary033_x264.mp4:f8, anomaly/Burglary/Burglary033_x264.mp4:f14, anomaly/Burglary/Burglary033_x264.mp4:f12, anomaly/Burglary/Burglary033_x264.mp4:f0, anomaly/Burglary/Burglary033_x264.mp4:f15, anomaly/Burglary/Burglary033_x264.mp4:f16, anomaly/Burglary/Burglary033_x264.mp4:f4, anomaly/Burglary/Burglary033_x264.mp4:f9, anomaly/Burglary/Burglary033_x264.mp4:f10, anomaly/Burglary/Burglary033_x264.mp4:f2

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 10.533, "evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f0", "anomaly/Burglary/Burglary033_x264.mp4:f2", "anomaly/Burglary/Burglary033_x264.mp4:f4"], "observation": {"evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f0", "anomaly/Burglary/Burglary033_x264.mp4:f2", "anomaly/Burglary/Burglary033_x264.mp4:f4"], "text": "The evidence indicates person detections (counts 3, 2,
- timeline: {"end_time": 23.334, "evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f8", "anomaly/Burglary/Burglary033_x264.mp4:f9", "anomaly/Burglary/Burglary033_x264.mp4:f10"], "observation": {"evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f8", "anomaly/Burglary/Burglary033_x264.mp4:f9", "anomaly/Burglary/Burglary033_x264.mp4:f10"], "text": "The evidence indicates a persistent Burglary model h
- timeline: {"end_time": 36.134, "evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f12", "anomaly/Burglary/Burglary033_x264.mp4:f14", "anomaly/Burglary/Burglary033_x264.mp4:f15", "anomaly/Burglary/Burglary033_x264.mp4:f16"], "observation": {"evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f12", "anomaly/Burglary/Burglary033_x264.mp4:f14", "anomaly/Burglary/Burglary033_x264.mp4:f15", "anomaly/Burg
- correlations: {"description": "All ten evidence records belong to the same Phase 2D incident anomaly/Burglary/Burglary033_x264.mp4:i0.", "evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f0", "anomaly/Burglary/Burglary033_x264.mp4:f2", "anomaly/Burglary/Burglary033_x264.mp4:f4", "anomaly/Burglary/Burglary033_x264.mp4:f8", "anomaly/Burglary/Burglary033_x264.mp4:f9", "anomaly/Burglary/Burglary033_x264.mp4:f
- correlations: {"description": "Compatible Burglary model hypotheses persist across nearby early windows from 0.0s to 10.533s.", "evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f0", "anomaly/Burglary/Burglary033_x264.mp4:f2", "anomaly/Burglary/Burglary033_x264.mp4:f4"], "type": "persistent_event"}
- correlations: {"description": "Compatible Burglary model hypotheses persist across adjacent windows from 17.067s to 23.334s.", "evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f8", "anomaly/Burglary/Burglary033_x264.mp4:f9", "anomaly/Burglary/Burglary033_x264.mp4:f10"], "type": "persistent_event"}
- correlations: {"description": "Compatible Burglary model hypotheses persist across nearby later windows from 25.6s to 36.134s.", "evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f12", "anomaly/Burglary/Burglary033_x264.mp4:f14", "anomaly/Burglary/Burglary033_x264.mp4:f15", "anomaly/Burglary/Burglary033_x264.mp4:f16"], "type": "persistent_event"}
- correlations: {"description": "Person object detections temporally overlap Burglary model hypotheses in the same intervals; this is source overlap only and does not indicate involvement or confirmation.", "evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f0", "anomaly/Burglary/Burglary033_x264.mp4:f2", "anomaly/Burglary/Burglary033_x264.mp4:f4"], "type": "cross_source_support"}
- correlations: {"description": "The early interval 8.533s-10.533s occurs before the middle interval 17.067s-19.067s, which occurs before the later interval 25.6s-27.6s.", "evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f4", "anomaly/Burglary/Burglary033_x264.mp4:f8", "anomaly/Burglary/Burglary033_x264.mp4:f12"], "type": "temporal_sequence"}
- inferences: {"evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f0", "anomaly/Burglary/Burglary033_x264.mp4:f2", "anomaly/Burglary/Burglary033_x264.mp4:f4", "anomaly/Burglary/Burglary033_x264.mp4:f8", "anomaly/Burglary/Burglary033_x264.mp4:f9", "anomaly/Burglary/Burglary033_x264.mp4:f10", "anomaly/Burglary/Burglary033_x264.mp4:f12", "anomaly/Burglary/Burglary033_x264.mp4:f14", "anomaly/Burglary/Burglary0
- inferences: {"evidence_ids": ["anomaly/Burglary/Burglary033_x264.mp4:f0", "anomaly/Burglary/Burglary033_x264.mp4:f2", "anomaly/Burglary/Burglary033_x264.mp4:f4", "anomaly/Burglary/Burglary033_x264.mp4:f8", "anomaly/Burglary/Burglary033_x264.mp4:f15"], "text": "The models produced low to moderate confidence generic-action hypotheses such as playing harp, doing laundry, and playing organ, which appear unrelated
plan queries: [{"query": "Burglary", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Burglary/Burglary033_x264.mp4:f4, anomaly/Burglary/Burglary033_x264.mp4:f3, anomaly/Burglary/Burglary033_x264.mp4:f2, anomaly/Burglary/Burglary033_x264.mp4:f5, anomaly/Burglary/Burglary033_x264.mp4:f8, anomaly/Burglary/Burglary033_x264.mp4:f11, anomaly/Burglary/Burglary033_x264.mp4:f13, anomaly/Burglary/Burglary033_x264.mp4:f10, anomaly/Burglary/Burglary033_x264.mp4:f18, anomaly/Burglary/Burglary033_x264.mp4:f1

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I10 — Reconstruct the event order in anomaly/Shooting/Shooting010_x264.mp4 between 36 and 42 seconds.

Expected facts (locked FULL grade in brackets):
- [F01] annotated Shooting interval is 36.5s to 42.0s (frames 1095-1260 at 30 fps) [locked full: Supported]
- [F02] evidence windows f17, f18, f19 overlap the annotated interval [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shooting/Shooting010_x264.mp4:f18, anomaly/Shooting/Shooting010_x264.mp4:f19, anomaly/Shooting/Shooting010_x264.mp4:f17, anomaly/Shooting/Shooting010_x264.mp4:f16

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 42.533, "evidence_ids": ["anomaly/Shooting/Shooting010_x264.mp4:f16", "anomaly/Shooting/Shooting010_x264.mp4:f17", "anomaly/Shooting/Shooting010_x264.mp4:f18", "anomaly/Shooting/Shooting010_x264.mp4:f19"], "observation": {"evidence_ids": ["anomaly/Shooting/Shooting010_x264.mp4:f16", "anomaly/Shooting/Shooting010_x264.mp4:f17", "anomaly/Shooting/Shooting010_x264.mp4:f18", "anomaly/Shoo
- correlations: {"description": "The evidence indicates RoadAccidents hypotheses persist across adjacent windows from ~34.1s to ~42.5s.", "evidence_ids": ["anomaly/Shooting/Shooting010_x264.mp4:f16", "anomaly/Shooting/Shooting010_x264.mp4:f17", "anomaly/Shooting/Shooting010_x264.mp4:f18", "anomaly/Shooting/Shooting010_x264.mp4:f19"], "type": "persistent_event"}
- correlations: {"description": "The evidence indicates the f17 window occurs after f16, f18 after f17, and f19 after f18, ordering the segment between 36 and 42 seconds.", "evidence_ids": ["anomaly/Shooting/Shooting010_x264.mp4:f16", "anomaly/Shooting/Shooting010_x264.mp4:f17", "anomaly/Shooting/Shooting010_x264.mp4:f18", "anomaly/Shooting/Shooting010_x264.mp4:f19"], "type": "temporal_sequence"}
- correlations: {"description": "All four evidence records belong to the same Phase 2D incident anomaly/Shooting/Shooting010_x264.mp4:i0.", "evidence_ids": ["anomaly/Shooting/Shooting010_x264.mp4:f16", "anomaly/Shooting/Shooting010_x264.mp4:f17", "anomaly/Shooting/Shooting010_x264.mp4:f18", "anomaly/Shooting/Shooting010_x264.mp4:f19"], "type": "same_incident"}
- correlations: {"description": "Object detections of cars, trucks and persons temporally co-occur with surveillance-event RoadAccidents hypotheses in the same windows; this indicates source co-occurrence only, not confirmation.", "evidence_ids": ["anomaly/Shooting/Shooting010_x264.mp4:f16", "anomaly/Shooting/Shooting010_x264.mp4:f17", "anomaly/Shooting/Shooting010_x264.mp4:f18", "anomaly/Shooting/Shooting010_x26
- inferences: {"evidence_ids": ["anomaly/Shooting/Shooting010_x264.mp4:f16", "anomaly/Shooting/Shooting010_x264.mp4:f17", "anomaly/Shooting/Shooting010_x264.mp4:f18", "anomaly/Shooting/Shooting010_x264.mp4:f19"], "text": "The available evidence suggests persistent vehicle presence with RoadAccidents model hypotheses between ~34.1s and ~42.5s, with varying person detections; the evidence is consistent with conti
plan queries: [{"query": "shooting", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shooting/Shooting010_x264.mp4:f17, anomaly/Shooting/Shooting010_x264.mp4:f18, anomaly/Shooting/Shooting010_x264.mp4:f19, anomaly/Shooting/Shooting010_x264.mp4:f16

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

### I11 — Reconstruct the event order in anomaly/Robbery/Robbery048_x264.mp4 between 14 and 32 seconds.

Expected facts (locked FULL grade in brackets):
- [F01] annotated Robbery interval is 15.0s to 31.0s (frames 450-930 at 30 fps) [locked full: Supported]
- [F02] evidence windows f7 through f14 overlap the annotated interval [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Robbery/Robbery048_x264.mp4:f6, anomaly/Robbery/Robbery048_x264.mp4:f15, anomaly/Robbery/Robbery048_x264.mp4:f14, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f13, anomaly/Robbery/Robbery048_x264.mp4:f9, anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f11, anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f12

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
FAILURE: {"error": "temporal_overlap contradicted by anomaly/Robbery/Robbery048_x264.mp4:f13 vs anomaly/Robbery/Robbery048_x264.mp4:f14", "stage": "3e", "type": "validation"}
plan queries: [{"query": "robbery", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Robbery/Robbery048_x264.mp4:f14, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f13, anomaly/Robbery/Robbery048_x264.mp4:f9, anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f11, anomaly/Robbery/Robbery048_x264.mp4:f6, anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f15, anomaly/Robbery/Robbery048_x264.mp4:f12

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

### I12 — Reconstruct the event order in anomaly/Explosion/Explosion036_x264.mp4 between 65 and 69 seconds.

Expected facts (locked FULL grade in brackets):
- [F01] annotated Explosion interval is 65.0s to 69.0s (frames 1950-2070 at 30 fps) [locked full: Supported]
- [F02] 3 evidence windows overlap the annotated interval [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Explosion/Explosion036_x264.mp4:f32, anomaly/Explosion/Explosion036_x264.mp4:f30, anomaly/Explosion/Explosion036_x264.mp4:f31

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 70.267, "evidence_ids": ["anomaly/Explosion/Explosion036_x264.mp4:f30", "anomaly/Explosion/Explosion036_x264.mp4:f31", "anomaly/Explosion/Explosion036_x264.mp4:f32"], "observation": {"evidence_ids": ["anomaly/Explosion/Explosion036_x264.mp4:f30", "anomaly/Explosion/Explosion036_x264.mp4:f31", "anomaly/Explosion/Explosion036_x264.mp4:f32"], "text": "The evidence indicates model-produce
- correlations: {"description": "The model-produced Explosion hypothesis in f30, f31 and f32 persists across adjacent windows from 64.0s to 70.267s, covering the 65-69s interval.", "evidence_ids": ["anomaly/Explosion/Explosion036_x264.mp4:f30", "anomaly/Explosion/Explosion036_x264.mp4:f31", "anomaly/Explosion/Explosion036_x264.mp4:f32"], "type": "persistent_event"}
- correlations: {"description": "f30 (64.0-66.0s) occurs before f31 (66.133-68.133s), which occurs before f32 (68.267-70.267s).", "evidence_ids": ["anomaly/Explosion/Explosion036_x264.mp4:f30", "anomaly/Explosion/Explosion036_x264.mp4:f31", "anomaly/Explosion/Explosion036_x264.mp4:f32"], "type": "temporal_sequence"}
- correlations: {"description": "f30, f31 and f32 belong to the same Phase 2D incident anomaly/Explosion/Explosion036_x264.mp4:i0.", "evidence_ids": ["anomaly/Explosion/Explosion036_x264.mp4:f30", "anomaly/Explosion/Explosion036_x264.mp4:f31", "anomaly/Explosion/Explosion036_x264.mp4:f32"], "type": "same_incident"}
- correlations: {"description": "In f30, person detections overlap in time with generic-action and surveillance-event outputs from different source types; this is source agreement only and does not confirm involvement or an event.", "evidence_ids": ["anomaly/Explosion/Explosion036_x264.mp4:f30"], "type": "cross_source_support"}
- inferences: {"evidence_ids": ["anomaly/Explosion/Explosion036_x264.mp4:f30", "anomaly/Explosion/Explosion036_x264.mp4:f31", "anomaly/Explosion/Explosion036_x264.mp4:f32"], "text": "The available evidence suggests model-indicated Explosion-related activity spanning the 65-69s period, with no gap in the hypothesis across the cited windows."}
plan queries: [{"query": "explosion", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Explosion/Explosion036_x264.mp4:f30, anomaly/Explosion/Explosion036_x264.mp4:f32, anomaly/Explosion/Explosion036_x264.mp4:f31

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

### I13 — Describe the Burglary to Shoplifting transition in anomaly/Shoplifting/Shoplifting034_x264.mp4 around 27 seconds.

Expected facts (locked FULL grade in brackets):
- [F01] window f12 carries the Burglary surveillance-event label [locked full: Supported]
- [F02] window f13 carries the Shoplifting surveillance-event label [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shoplifting/Shoplifting034_x264.mp4:f12, anomaly/Shoplifting/Shoplifting034_x264.mp4:f13, anomaly/Shoplifting/Shoplifting034_x264.mp4:f11, anomaly/Shoplifting/Shoplifting034_x264.mp4:f14

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 27.6, "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f11", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f12"], "observation": {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f11", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f12"], "text": "The evidence indicates the model produced Burglary hypotheses (confidence 0.9392 then 0.4729) with person detections
- timeline: {"end_time": 31.867, "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f13", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f14"], "observation": {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f13", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f14"], "text": "The evidence indicates the model produced Shoplifting hypotheses (confidence 0.8643 then 0.9309) with person detec
- correlations: {"description": "Burglary-hypothesis windows ending at 27.6s occur immediately before Shoplifting-hypothesis windows starting at 27.733s, marking the transition around 27 seconds.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f12", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f13"], "type": "temporal_sequence"}
- correlations: {"description": "Burglary surveillance-event hypothesis persists across adjacent windows from 23.467s to 27.6s with decreasing confidence.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f11", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f12"], "type": "persistent_event"}
- correlations: {"description": "Shoplifting surveillance-event hypothesis persists across adjacent windows from 27.733s to 31.867s.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f13", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f14"], "type": "persistent_event"}
- correlations: {"description": "All four evidence records belong to the same Phase 2D incident anomaly/Shoplifting/Shoplifting034_x264.mp4:i0.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f11", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f12", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f13", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f14"], "type": "same_incident"}
- correlations: {"description": "Object person detections and generic_action garbage collecting hypotheses co-occur temporally with surveillance-event Burglary/Shoplifting hypotheses, indicating source co-occurrence only and not confirmation.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f11", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f12", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f13", "
- inferences: {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f12", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f13"], "text": "The available evidence suggests a model-hypothesis transition from Burglary to Shoplifting between 27.6s and 27.733s, with 3 person detections in both windows; temporal proximity does not indicate involvement or causation."}
- inferences: {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f11", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f12", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f13", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f14"], "text": "The evidence is consistent with continuous person presence and persistent garbage collecting action hypotheses across the transition, but the evidence does not establis
plan queries: [{"query": "Burglary", "source": "surveillance_event"}, {"query": "Shoplifting", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shoplifting/Shoplifting034_x264.mp4:f12, anomaly/Shoplifting/Shoplifting034_x264.mp4:f13, anomaly/Shoplifting/Shoplifting034_x264.mp4:f11, anomaly/Shoplifting/Shoplifting034_x264.mp4:f14

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

### I14 — Describe the Shoplifting to Burglary transition in anomaly/Shoplifting/Shoplifting034_x264.mp4 around 166 seconds.

Expected facts (locked FULL grade in brackets):
- [F01] window f77 carries the Shoplifting surveillance-event label [locked full: Supported]
- [F02] window f78 carries the Burglary surveillance-event label [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shoplifting/Shoplifting034_x264.mp4:f76, anomaly/Shoplifting/Shoplifting034_x264.mp4:f78, anomaly/Shoplifting/Shoplifting034_x264.mp4:f77

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 166.267, "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f76", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f77"], "observation": {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f76", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f77"], "text": "The evidence indicates suitcase detections and person detections with 'garbage collecting' action hypotheses, whi
- timeline: {"end_time": 168.4, "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f78"], "observation": {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f78"], "text": "The evidence indicates 3 person detections with 'garbage collecting' action hypothesis, while the surveillance-event model produced a 'Burglary' hypothesis with confidence 0.6797."}, "start_time": 166.4}
- correlations: {"description": "The available evidence suggests a persistent Shoplifting hypothesis across adjacent windows 162.133s-166.267s.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f76", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f77"], "type": "persistent_event"}
- correlations: {"description": "The evidence indicates the Shoplifting-hypothesis interval ending at 166.267s occurs before the Burglary-hypothesis interval starting at 166.4s.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f77", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f78"], "type": "temporal_sequence"}
- correlations: {"description": "The evidence records belong to the same Phase 2D incident anomaly/Shoplifting/Shoplifting034_x264.mp4:i0.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f76", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f77", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f78"], "type": "same_incident"}
- inferences: {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f76", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f77", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f78"], "text": "The available evidence suggests a transition around 166 seconds from Shoplifting model hypotheses to a Burglary model hypothesis, with no temporal overlap between the cited intervals."}
plan queries: [{"query": "shoplifting", "source": "surveillance_event"}, {"query": "burglary", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shoplifting/Shoplifting034_x264.mp4:f76, anomaly/Shoplifting/Shoplifting034_x264.mp4:f78, anomaly/Shoplifting/Shoplifting034_x264.mp4:f77

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

### I15 — Describe the Vandalism to Assault transition in anomaly/Assault/Assault010_x264.mp4 around 60 to 76 seconds.

Expected facts (locked FULL grade in brackets):
- [F01] window f29 carries the Vandalism surveillance-event label [locked full: Supported]
- [F02] window f35 carries the Assault surveillance-event label [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Assault/Assault010_x264.mp4:f30, anomaly/Assault/Assault010_x264.mp4:f33, anomaly/Assault/Assault010_x264.mp4:f35, anomaly/Assault/Assault010_x264.mp4:f28, anomaly/Assault/Assault010_x264.mp4:f29, anomaly/Assault/Assault010_x264.mp4:f31, anomaly/Assault/Assault010_x264.mp4:f32, anomaly/Assault/Assault010_x264.mp4:f34

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 61.733, "evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f28"], "observation": {"evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f28"], "text": "The evidence indicates at 59.733s-61.733s the object model detected 2 persons and 2 suitcases, the generic-action model produced 'sweeping floor', and the surveillance-event model produced an 'Assault' hypothesis."}, "start_time": 5
- timeline: {"end_time": 72.4, "evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f29", "anomaly/Assault/Assault010_x264.mp4:f30", "anomaly/Assault/Assault010_x264.mp4:f31", "anomaly/Assault/Assault010_x264.mp4:f32", "anomaly/Assault/Assault010_x264.mp4:f33"], "observation": {"evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f29", "anomaly/Assault/Assault010_x264.mp4:f30", "anomaly/Assault/Assault010_x
- timeline: {"end_time": 74.533, "evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f34"], "observation": {"evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f34"], "text": "The evidence indicates at 72.533s-74.533s the surveillance-event model produced a 'RoadAccidents' hypothesis with 'bookbinding' generic action and no object detections."}, "start_time": 72.533}
- timeline: {"end_time": 76.667, "evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f35"], "observation": {"evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f35"], "text": "The evidence indicates at 74.667s-76.667s the surveillance-event model produced an 'Assault' hypothesis with 'unloading truck' generic action and no object detections."}, "start_time": 74.667}
- correlations: {"description": "Compatible 'Vandalism' hypotheses persist across adjacent windows from 61.867s to 72.4s.", "evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f29", "anomaly/Assault/Assault010_x264.mp4:f30", "anomaly/Assault/Assault010_x264.mp4:f31", "anomaly/Assault/Assault010_x264.mp4:f32", "anomaly/Assault/Assault010_x264.mp4:f33"], "type": "persistent_event"}
- correlations: {"description": "The interval with an 'Assault' hypothesis at 59.733s-61.733s occurs before the persistent 'Vandalism' interval starting at 61.867s.", "evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f28", "anomaly/Assault/Assault010_x264.mp4:f29"], "type": "temporal_sequence"}
- correlations: {"description": "The persistent 'Vandalism' interval ending at 72.4s occurs before the 'RoadAccidents' interval at 72.533s-74.533s, which occurs before the later 'Assault' interval starting at 74.667s.", "evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f33", "anomaly/Assault/Assault010_x264.mp4:f34", "anomaly/Assault/Assault010_x264.mp4:f35"], "type": "temporal_sequence"}
- correlations: {"description": "All cited evidence records belong to the same Phase 2D incident anomaly/Assault/Assault010_x264.mp4:i0.", "evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f28", "anomaly/Assault/Assault010_x264.mp4:f29", "anomaly/Assault/Assault010_x264.mp4:f30", "anomaly/Assault/Assault010_x264.mp4:f31", "anomaly/Assault/Assault010_x264.mp4:f32", "anomaly/Assault/Assault010_x264.mp4:f33", "a
- correlations: {"description": "In the same window, object detections, generic-action output, and surveillance-event hypothesis overlap in time; this is source co-occurrence only and does not confirm involvement.", "evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f28"], "type": "cross_source_support"}
- inferences: {"evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f28", "anomaly/Assault/Assault010_x264.mp4:f29", "anomaly/Assault/Assault010_x264.mp4:f30", "anomaly/Assault/Assault010_x264.mp4:f31", "anomaly/Assault/Assault010_x264.mp4:f32", "anomaly/Assault/Assault010_x264.mp4:f33", "anomaly/Assault/Assault010_x264.mp4:f34", "anomaly/Assault/Assault010_x264.mp4:f35"], "text": "The available evidence sugge
- inferences: {"evidence_ids": ["anomaly/Assault/Assault010_x264.mp4:f28", "anomaly/Assault/Assault010_x264.mp4:f29"], "text": "Person detections temporally overlap the early 'Assault' and 'Vandalism' hypotheses, but the evidence does not indicate the detected persons were involved in the hypothesized events."}
plan queries: [{"query": "vandalism", "source": "surveillance_event"}, {"query": "assault", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Assault/Assault010_x264.mp4:f30, anomaly/Assault/Assault010_x264.mp4:f33, anomaly/Assault/Assault010_x264.mp4:f31, anomaly/Assault/Assault010_x264.mp4:f35, anomaly/Assault/Assault010_x264.mp4:f34, anomaly/Assault/Assault010_x264.mp4:f28, anomaly/Assault/Assault010_x264.mp4:f29, anomaly/Assault/Assault010_x264.mp4:f32

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

### I16 — Show evidence around 100 seconds in anomaly/Burglary/Burglary032_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] 10 evidence windows overlap the 90s to 110s interval [locked full: Partial]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Burglary/Burglary032_x264.mp4:f50, anomaly/Burglary/Burglary032_x264.mp4:f42, anomaly/Burglary/Burglary032_x264.mp4:f46, anomaly/Burglary/Burglary032_x264.mp4:f48, anomaly/Burglary/Burglary032_x264.mp4:f49, anomaly/Burglary/Burglary032_x264.mp4:f47, anomaly/Burglary/Burglary032_x264.mp4:f51, anomaly/Burglary/Burglary032_x264.mp4:f43, anomaly/Burglary/Burglary032_x264.mp4:f44, anomaly/Burglary/Burglary032_x264.mp4:f45

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
plan queries: [{"query": "evidence", "source": null}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Burglary/Burglary032_x264.mp4:f50, anomaly/Burglary/Burglary032_x264.mp4:f42, anomaly/Burglary/Burglary032_x264.mp4:f46, anomaly/Burglary/Burglary032_x264.mp4:f48, anomaly/Burglary/Burglary032_x264.mp4:f49, anomaly/Burglary/Burglary032_x264.mp4:f47, anomaly/Burglary/Burglary032_x264.mp4:f51, anomaly/Burglary/Burglary032_x264.mp4:f44, anomaly/Burglary/Burglary032_x264.mp4:f43, anomaly/Burglary/Burglary032_x264.mp4:f45

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I17 — Show evidence between 400 and 440 seconds in anomaly/Explosion/Explosion007_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] 20 evidence windows overlap the 400s to 440s interval [locked full: Unsupported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Explosion/Explosion007_x264.mp4:f201, anomaly/Explosion/Explosion007_x264.mp4:f200, anomaly/Explosion/Explosion007_x264.mp4:f203, anomaly/Explosion/Explosion007_x264.mp4:f202, anomaly/Explosion/Explosion007_x264.mp4:f206, anomaly/Explosion/Explosion007_x264.mp4:f198, anomaly/Explosion/Explosion007_x264.mp4:f191, anomaly/Explosion/Explosion007_x264.mp4:f204, anomaly/Explosion/Explosion007_x264.mp4:f192, anomaly/Explosion/Explosion007_x264.mp4:f190

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
plan queries: [{"query": "evidence", "source": null}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Explosion/Explosion007_x264.mp4:f201, anomaly/Explosion/Explosion007_x264.mp4:f200, anomaly/Explosion/Explosion007_x264.mp4:f203, anomaly/Explosion/Explosion007_x264.mp4:f202, anomaly/Explosion/Explosion007_x264.mp4:f206, anomaly/Explosion/Explosion007_x264.mp4:f198, anomaly/Explosion/Explosion007_x264.mp4:f191, anomaly/Explosion/Explosion007_x264.mp4:f204, anomaly/Explosion/Explosion007_x264.mp4:f192, anomaly/Explosion/Explosion007_x264.mp4:f190

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I18 — Show evidence between 200 and 220 seconds in anomaly/Assault/Assault010_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] 11 evidence windows overlap the 200s to 220s interval [locked full: Partial]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Assault/Assault010_x264.mp4:f97, anomaly/Assault/Assault010_x264.mp4:f96, anomaly/Assault/Assault010_x264.mp4:f99, anomaly/Assault/Assault010_x264.mp4:f98, anomaly/Assault/Assault010_x264.mp4:f100, anomaly/Assault/Assault010_x264.mp4:f95, anomaly/Assault/Assault010_x264.mp4:f94, anomaly/Assault/Assault010_x264.mp4:f101, anomaly/Assault/Assault010_x264.mp4:f93, anomaly/Assault/Assault010_x264.mp4:f103

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
plan queries: [{"query": "evidence", "source": null}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Assault/Assault010_x264.mp4:f97, anomaly/Assault/Assault010_x264.mp4:f96, anomaly/Assault/Assault010_x264.mp4:f99, anomaly/Assault/Assault010_x264.mp4:f98, anomaly/Assault/Assault010_x264.mp4:f100, anomaly/Assault/Assault010_x264.mp4:f95, anomaly/Assault/Assault010_x264.mp4:f94, anomaly/Assault/Assault010_x264.mp4:f101, anomaly/Assault/Assault010_x264.mp4:f93, anomaly/Assault/Assault010_x264.mp4:f103

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I19 — Show person detections with RoadAccidents evidence in anomaly/RoadAccidents/RoadAccidents001_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] a single window f6 carries both a person detection and the RoadAccidents label [locked full: Supported]
- [F02] window f6 spans 12.8s to 14.8s [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f12, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f10, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f15, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f7, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f14

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 10.533, "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f4"], "observation": {"evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f4"], "text": "The evidence indicates model-produced RoadAccidents hypotheses in two nearby windows, each overlapping
- timeline: {"end_time": 23.333, "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f7", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f8", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f9", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f10"], "observation": {"evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6", "an
- timeline: {"end_time": 27.6, "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f12"], "observation": {"evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f12"], "text": "The model produced a RoadAccidents hypothesis overlapping a driving car hypothesis, with no person detections reported in this window."}, "start_time": 25.6}
- timeline: {"end_time": 34.0, "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f14", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f15"], "observation": {"evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f14", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f15"], "text": "The evidence indicates persistent model-produced RoadAccidents hypotheses across two nearby windows,
- correlations: {"description": "The evidence indicates all cited windows belong to the same Phase 2D incident anomaly/RoadAccidents/RoadAccidents001_x264.mp4:i0 in the same video.", "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f4", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f7", 
- correlations: {"description": "The evidence suggests compatible model-produced RoadAccidents hypotheses persist across nearby windows from 12.8s to 23.333s.", "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f7", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f8", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f9", "anomaly/RoadAccidents
- correlations: {"description": "The evidence suggests compatible model-produced RoadAccidents hypotheses persist across nearby windows 29.866s-31.866s and 32.0s-34.0s.", "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f14", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f15"], "type": "persistent_event"}
- correlations: {"description": "The available evidence suggests model-produced surveillance_event hypotheses overlap in time with generic_action hypotheses, with object detections also overlapping in one window; co-occurrence indicates source agreement only, not confirmation.", "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f7", "anomaly/Ro
- correlations: {"description": "The evidence indicates windows 6.4s-10.533s occur before the 12.8s-14.8s window in the same video.", "evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f4", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6"], "type": "temporal_sequence"}
- inferences: {"evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f15"], "text": "The available evidence suggests model-produced RoadAccidents hypotheses recur from 6.4s to 34.0s with gaps, while person detection is limited to the 12.8s-14.8s portion; overlap alone does not indicate involve
- inferences: {"evidence_ids": ["anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f10", "anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f12"], "text": "The evidence is consistent with vehicle-related action hypotheses overlapping RoadAccidents hypotheses, but the evidence is insufficient to determine role
plan queries: [{"query": "person", "source": "object"}, {"query": "RoadAccidents", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f12, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f15, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f10, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f16, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f17, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

### I20 — Show person detections with Burglary evidence in anomaly/Burglary/Burglary032_x264.mp4 between 27 and 49 seconds.

Expected facts (locked FULL grade in brackets):
- [F01] 9 evidence windows carry both a person detection and the Burglary label [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f14, anomaly/Burglary/Burglary032_x264.mp4:f22

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 48.933, "evidence_ids": ["anomaly/Burglary/Burglary032_x264.mp4:f13", "anomaly/Burglary/Burglary032_x264.mp4:f14", "anomaly/Burglary/Burglary032_x264.mp4:f15", "anomaly/Burglary/Burglary032_x264.mp4:f16", "anomaly/Burglary/Burglary032_x264.mp4:f17", "anomaly/Burglary/Burglary032_x264.mp4:f18", "anomaly/Burglary/Burglary032_x264.mp4:f19", "anomaly/Burglary/Burglary032_x264.mp4:f20", "a
- correlations: {"description": "Compatible Burglary model hypotheses persist across adjacent windows from ~27.7s to ~48.9s, consistent with a continuing hypothesis rather than isolated detections.", "evidence_ids": ["anomaly/Burglary/Burglary032_x264.mp4:f13", "anomaly/Burglary/Burglary032_x264.mp4:f14", "anomaly/Burglary/Burglary032_x264.mp4:f15", "anomaly/Burglary/Burglary032_x264.mp4:f16", "anomaly/Burglary/B
- correlations: {"description": "All ten evidence records belong to the same Phase 2D incident anomaly/Burglary/Burglary032_x264.mp4:i0.", "evidence_ids": ["anomaly/Burglary/Burglary032_x264.mp4:f13", "anomaly/Burglary/Burglary032_x264.mp4:f14", "anomaly/Burglary/Burglary032_x264.mp4:f15", "anomaly/Burglary/Burglary032_x264.mp4:f16", "anomaly/Burglary/Burglary032_x264.mp4:f17", "anomaly/Burglary/Burglary032_x264.
- correlations: {"description": "In these windows object-source person detections temporally coincide with surveillance-event Burglary hypotheses from a different source type; this is source co-occurrence only and does not indicate involvement or confirmation.", "evidence_ids": ["anomaly/Burglary/Burglary032_x264.mp4:f13", "anomaly/Burglary/Burglary032_x264.mp4:f15", "anomaly/Burglary/Burglary032_x264.mp4:f16", "
- inferences: {"evidence_ids": ["anomaly/Burglary/Burglary032_x264.mp4:f13", "anomaly/Burglary/Burglary032_x264.mp4:f14", "anomaly/Burglary/Burglary032_x264.mp4:f15", "anomaly/Burglary/Burglary032_x264.mp4:f16", "anomaly/Burglary/Burglary032_x264.mp4:f17", "anomaly/Burglary/Burglary032_x264.mp4:f18", "anomaly/Burglary/Burglary032_x264.mp4:f19", "anomaly/Burglary/Burglary032_x264.mp4:f20", "anomaly/Burglary/Burg
- inferences: {"evidence_ids": ["anomaly/Burglary/Burglary032_x264.mp4:f16", "anomaly/Burglary/Burglary032_x264.mp4:f17", "anomaly/Burglary/Burglary032_x264.mp4:f18", "anomaly/Burglary/Burglary032_x264.mp4:f19", "anomaly/Burglary/Burglary032_x264.mp4:f20", "anomaly/Burglary/Burglary032_x264.mp4:f21", "anomaly/Burglary/Burglary032_x264.mp4:f22"], "text": "The evidence indicates generic-action labels in the later
plan queries: [{"query": "person", "source": "object"}, {"query": "Burglary", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f14, anomaly/Burglary/Burglary032_x264.mp4:f22, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f20

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I21 — Show suitcase detections with Shoplifting evidence in anomaly/Shoplifting/Shoplifting034_x264.mp4 between 36 and 60 seconds.

Expected facts (locked FULL grade in brackets):
- [F01] 4 evidence windows carry both a suitcase detection and the Shoplifting label [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shoplifting/Shoplifting034_x264.mp4:f22, anomaly/Shoplifting/Shoplifting034_x264.mp4:f17, anomaly/Shoplifting/Shoplifting034_x264.mp4:f19, anomaly/Shoplifting/Shoplifting034_x264.mp4:f24, anomaly/Shoplifting/Shoplifting034_x264.mp4:f18, anomaly/Shoplifting/Shoplifting034_x264.mp4:f23, anomaly/Shoplifting/Shoplifting034_x264.mp4:f26, anomaly/Shoplifting/Shoplifting034_x264.mp4:f16, anomaly/Shoplifting/Shoplifting034_x264.mp4:f28, anomaly/Shoplifting/Shoplifting034_x264.mp4:f27

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 38.267, "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f16", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f17"], "observation": {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f16", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f17"], "text": "The evidence indicates person detections (3 persons, then 1 person plus 1 suitcase) overlapping model-produced Sho
- timeline: {"end_time": 42.533, "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f18", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f19"], "observation": {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f18", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f19"], "text": "The evidence indicates person detections (1-2 persons) plus suitcase detections (2, then 1) overlapping model-prod
- timeline: {"end_time": 48.933, "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f22"], "observation": {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f22"], "text": "The evidence indicates 1 suitcase detection with no person detection reported, overlapping a model-produced Burglary hypothesis (confidence 0.859) and 'garbage collecting' label."}, "start_time": 46.933}
- timeline: {"end_time": 53.2, "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f23", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f24"], "observation": {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f23", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f24"], "text": "The evidence indicates suitcase detections in both windows (plus 2 persons in the earlier window) overlapping model-
- timeline: {"end_time": 61.733, "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f26", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f27", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f28"], "observation": {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f26", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f27", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f28"], "text": "The evidence
- correlations: {"description": "All listed evidence records belong to the same Phase 2D incident anomaly/Shoplifting/Shoplifting034_x264.mp4:i0 in the same video.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f16", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f17", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f18", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f19", "anomaly/Shoplifting/Shoplift
- correlations: {"description": "Suitcase object detections and model-produced Shoplifting hypotheses co-occur in the same temporal windows. This is source agreement only and never confirmation of a crime or involvement.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f17", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f23", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f24", "anomaly/Shoplifting/Sh
- correlations: {"description": "Compatible model-produced Shoplifting hypotheses persist across adjacent and nearby windows from ~49.067s to ~61.733s.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f23", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f24", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f26", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f27", "anomaly/Shoplifting/Shoplifting034_x264.
- correlations: {"description": "The early windows 34.133s-42.533s occur before the later windows 49.067s-61.733s.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f16", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f17", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f18", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f19", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f23", "anomaly/Shoplifting/Shopli
- inferences: {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f17", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f23", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f24", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f26"], "text": "The available evidence suggests suitcase detections co-occurred with model-produced Shoplifting hypotheses between ~36.267s and ~57.467s. The evidence is consistent wit
- inferences: {"evidence_ids": ["anomaly/Shoplifting/Shoplifting034_x264.mp4:f16", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f17", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f18", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f19", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f22", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f23", "anomaly/Shoplifting/Shoplifting034_x264.mp4:f24", "anomaly/Shoplifting/Shop
plan queries: [{"query": "suitcase", "source": "object"}, {"query": "Shoplifting", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shoplifting/Shoplifting034_x264.mp4:f22, anomaly/Shoplifting/Shoplifting034_x264.mp4:f17, anomaly/Shoplifting/Shoplifting034_x264.mp4:f19, anomaly/Shoplifting/Shoplifting034_x264.mp4:f24, anomaly/Shoplifting/Shoplifting034_x264.mp4:f18, anomaly/Shoplifting/Shoplifting034_x264.mp4:f23, anomaly/Shoplifting/Shoplifting034_x264.mp4:f26, anomaly/Shoplifting/Shoplifting034_x264.mp4:f20, anomaly/Shoplifting/Shoplifting034_x264.mp4:f27, anomaly/Shoplifting/Shoplifting034_x264.mp4:f21

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I22 — Summarize the incident in anomaly/Robbery/Robbery048_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] 23 evidence windows span 0.0s to 46.9s [locked full: Supported]
- [F02] annotated Robbery interval is 15.0s to 31.0s [locked full: Supported]
- [F03] windows f7 through f14 overlap the annotated interval [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Robbery/Robbery048_x264.mp4:f17, anomaly/Robbery/Robbery048_x264.mp4:f18, anomaly/Robbery/Robbery048_x264.mp4:f15, anomaly/Robbery/Robbery048_x264.mp4:f16, anomaly/Robbery/Robbery048_x264.mp4:f6, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f2, anomaly/Robbery/Robbery048_x264.mp4:f9

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____
- F03: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 6.267, "evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f2"], "observation": {"evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f2"], "text": "The evidence indicates 1 person detection (max confidence 0.6548) co-occurring with model-produced hypotheses 'sweeping floor' (0.0669) and surveillance_event 'Shooting' (0.3359). The available evidence does not establish the person's 
- timeline: {"end_time": 23.333, "evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f6", "anomaly/Robbery/Robbery048_x264.mp4:f7", "anomaly/Robbery/Robbery048_x264.mp4:f8", "anomaly/Robbery/Robbery048_x264.mp4:f9", "anomaly/Robbery/Robbery048_x264.mp4:f10"], "observation": {"evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f6", "anomaly/Robbery/Robbery048_x264.mp4:f7", "anomaly/Robbery/Robbery048_x264.
- timeline: {"end_time": 40.4, "evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f15", "anomaly/Robbery/Robbery048_x264.mp4:f16", "anomaly/Robbery/Robbery048_x264.mp4:f17", "anomaly/Robbery/Robbery048_x264.mp4:f18"], "observation": {"evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f15", "anomaly/Robbery/Robbery048_x264.mp4:f16", "anomaly/Robbery/Robbery048_x264.mp4:f17", "anomaly/Robbery/Robbery048_x
- correlations: {"description": "The evidence records belong to the same Phase 2D incident anomaly/Robbery/Robbery048_x264.mp4:i0 in video anomaly/Robbery/Robbery048_x264.mp4.", "evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f2", "anomaly/Robbery/Robbery048_x264.mp4:f6", "anomaly/Robbery/Robbery048_x264.mp4:f7", "anomaly/Robbery/Robbery048_x264.mp4:f8", "anomaly/Robbery/Robbery048_x264.mp4:f9", "anomaly/Ro
- correlations: {"description": "The evidence interval 4.267s-6.267s occurs before 12.8s-14.8s.", "evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f2", "anomaly/Robbery/Robbery048_x264.mp4:f6"], "type": "temporal_sequence"}
- correlations: {"description": "The evidence interval 21.333s-23.333s occurs before 32.0s-34.0s.", "evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f10", "anomaly/Robbery/Robbery048_x264.mp4:f15"], "type": "temporal_sequence"}
- correlations: {"description": "Compatible surveillance_event hypothesis 'RoadAccidents' persists across adjacent windows 17.067s-19.067s and 19.2s-21.2s with continued person detections.", "evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f8", "anomaly/Robbery/Robbery048_x264.mp4:f9"], "type": "persistent_event"}
- correlations: {"description": "Compatible surveillance_event hypothesis 'RoadAccidents' persists across adjacent windows 36.267s-38.267s and 38.4s-40.4s with continued person detections.", "evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f17", "anomaly/Robbery/Robbery048_x264.mp4:f18"], "type": "persistent_event"}
- correlations: {"description": "Person detections (object source) co-occur in the same windows with surveillance_event hypotheses, indicating source overlap only and not confirmation or involvement.", "evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f15", "anomaly/Robbery/Robbery048_x264.mp4:f16", "anomaly/Robbery/Robbery048_x264.mp4:f17", "anomaly/Robbery/Robbery048_x264.mp4:f18"], "type": "cross_source_su
- inferences: {"evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f6", "anomaly/Robbery/Robbery048_x264.mp4:f7", "anomaly/Robbery/Robbery048_x264.mp4:f8", "anomaly/Robbery/Robbery048_x264.mp4:f9", "anomaly/Robbery/Robbery048_x264.mp4:f10", "anomaly/Robbery/Robbery048_x264.mp4:f15", "anomaly/Robbery/Robbery048_x264.mp4:f16", "anomaly/Robbery/Robbery048_x264.mp4:f17", "anomaly/Robbery/Robbery048_x264.mp4:f18"]
- inferences: {"evidence_ids": ["anomaly/Robbery/Robbery048_x264.mp4:f2", "anomaly/Robbery/Robbery048_x264.mp4:f6", "anomaly/Robbery/Robbery048_x264.mp4:f7", "anomaly/Robbery/Robbery048_x264.mp4:f8", "anomaly/Robbery/Robbery048_x264.mp4:f9", "anomaly/Robbery/Robbery048_x264.mp4:f10", "anomaly/Robbery/Robbery048_x264.mp4:f15", "anomaly/Robbery/Robbery048_x264.mp4:f16", "anomaly/Robbery/Robbery048_x264.mp4:f17", 
plan queries: [{"query": "robbery", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____
- F03: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Robbery/Robbery048_x264.mp4:f17, anomaly/Robbery/Robbery048_x264.mp4:f18, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f2, anomaly/Robbery/Robbery048_x264.mp4:f9, anomaly/Robbery/Robbery048_x264.mp4:f14, anomaly/Robbery/Robbery048_x264.mp4:f13, anomaly/Robbery/Robbery048_x264.mp4:f11

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____
- F03: Grade: ____ Reason: ____ Evidence reference: ____

### I23 — Summarize the incident in anomaly/RoadAccidents/RoadAccidents002_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] 6 evidence windows span 0.0s to 11.5s [locked full: Partial]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/RoadAccidents/RoadAccidents002_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents002_x264.mp4:f2, anomaly/RoadAccidents/RoadAccidents002_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents002_x264.mp4:f1, anomaly/RoadAccidents/RoadAccidents002_x264.mp4:f0, anomaly/RoadAccidents/RoadAccidents002_x264.mp4:f5

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
plan queries: [{"query": "road accident", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/RoadAccidents/RoadAccidents002_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents002_x264.mp4:f2, anomaly/RoadAccidents/RoadAccidents002_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents002_x264.mp4:f1, anomaly/RoadAccidents/RoadAccidents002_x264.mp4:f0, anomaly/RoadAccidents/RoadAccidents002_x264.mp4:f5

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I24 — Summarize the incident in anomaly/Shoplifting/Shoplifting031_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] 7 evidence windows span 0.0s to 14.8s [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shoplifting/Shoplifting031_x264.mp4:f0, anomaly/Shoplifting/Shoplifting031_x264.mp4:f6, anomaly/Shoplifting/Shoplifting031_x264.mp4:f5, anomaly/Shoplifting/Shoplifting031_x264.mp4:f1, anomaly/Shoplifting/Shoplifting031_x264.mp4:f4, anomaly/Shoplifting/Shoplifting031_x264.mp4:f2, anomaly/Shoplifting/Shoplifting031_x264.mp4:f3

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 14.8, "evidence_ids": ["anomaly/Shoplifting/Shoplifting031_x264.mp4:f0", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f1", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f2", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f3", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f4", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f5", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f6"], "observation"
- correlations: {"description": "Shoplifting surveillance-event hypotheses with high confidence persist across adjacent windows from 0.0s to 14.8s.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting031_x264.mp4:f0", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f1", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f2", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f3", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f4",
- correlations: {"description": "All seven windows are grouped under the same Phase 2D incident anomaly/Shoplifting/Shoplifting031_x264.mp4:i0.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting031_x264.mp4:f0", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f1", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f2", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f3", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f4", "an
- correlations: {"description": "Person object detections co-occur in the same windows as Shoplifting hypotheses; this is source agreement only and does not confirm involvement.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting031_x264.mp4:f0", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f1", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f2", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f3", "anomaly/Shopliftin
- correlations: {"description": "Window f0 at 0.0-2.0s occurs before window f6 at 12.8-14.8s.", "evidence_ids": ["anomaly/Shoplifting/Shoplifting031_x264.mp4:f0", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f6"], "type": "temporal_sequence"}
- inferences: {"evidence_ids": ["anomaly/Shoplifting/Shoplifting031_x264.mp4:f0", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f1", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f2", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f3", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f4", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f5", "anomaly/Shoplifting/Shoplifting031_x264.mp4:f6"], "text": "The available evidence
plan queries: [{"query": "shoplifting", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shoplifting/Shoplifting031_x264.mp4:f0, anomaly/Shoplifting/Shoplifting031_x264.mp4:f4, anomaly/Shoplifting/Shoplifting031_x264.mp4:f6, anomaly/Shoplifting/Shoplifting031_x264.mp4:f5, anomaly/Shoplifting/Shoplifting031_x264.mp4:f1, anomaly/Shoplifting/Shoplifting031_x264.mp4:f3, anomaly/Shoplifting/Shoplifting031_x264.mp4:f2

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I25 — Describe activity in normal/Normal_Videos_247_x264.mp4 between 100 and 150 seconds without confirming any crime.

Expected facts (locked FULL grade in brackets):
- [F01] 25 evidence windows overlap the interval [locked full: Supported]
- [F02] video carries no annotated anomaly interval [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: normal/Normal_Videos_247_x264.mp4:f49, normal/Normal_Videos_247_x264.mp4:f53, normal/Normal_Videos_247_x264.mp4:f46, normal/Normal_Videos_247_x264.mp4:f67, normal/Normal_Videos_247_x264.mp4:f66, normal/Normal_Videos_247_x264.mp4:f68, normal/Normal_Videos_247_x264.mp4:f47, normal/Normal_Videos_247_x264.mp4:f57, normal/Normal_Videos_247_x264.mp4:f65, normal/Normal_Videos_247_x264.mp4:f60

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
plan queries: [{"query": "activity", "source": "generic_action"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: normal/Normal_Videos_247_x264.mp4:f49, normal/Normal_Videos_247_x264.mp4:f53, normal/Normal_Videos_247_x264.mp4:f46, normal/Normal_Videos_247_x264.mp4:f67, normal/Normal_Videos_247_x264.mp4:f66, normal/Normal_Videos_247_x264.mp4:f68, normal/Normal_Videos_247_x264.mp4:f47, normal/Normal_Videos_247_x264.mp4:f57, normal/Normal_Videos_247_x264.mp4:f65, normal/Normal_Videos_247_x264.mp4:f60

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

### I26 — Describe activity in normal/Normal_Videos_310_x264.mp4 without confirming any crime.

Expected facts (locked FULL grade in brackets):
- [F01] 40 evidence windows in total [locked full: Partial]
- [F02] video carries no annotated anomaly interval [locked full: Partial]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: normal/Normal_Videos_310_x264.mp4:f0, normal/Normal_Videos_310_x264.mp4:f13, normal/Normal_Videos_310_x264.mp4:f19, normal/Normal_Videos_310_x264.mp4:f30, normal/Normal_Videos_310_x264.mp4:f16, normal/Normal_Videos_310_x264.mp4:f10, normal/Normal_Videos_310_x264.mp4:f33, normal/Normal_Videos_310_x264.mp4:f28, normal/Normal_Videos_310_x264.mp4:f34, normal/Normal_Videos_310_x264.mp4:f6

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
plan queries: [{"query": "activity", "source": "generic_action"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: normal/Normal_Videos_310_x264.mp4:f0, normal/Normal_Videos_310_x264.mp4:f13, normal/Normal_Videos_310_x264.mp4:f19, normal/Normal_Videos_310_x264.mp4:f30, normal/Normal_Videos_310_x264.mp4:f16, normal/Normal_Videos_310_x264.mp4:f10, normal/Normal_Videos_310_x264.mp4:f33, normal/Normal_Videos_310_x264.mp4:f28, normal/Normal_Videos_310_x264.mp4:f34, normal/Normal_Videos_310_x264.mp4:f6

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____
- F02: Grade: ____ Reason: ____ Evidence reference: ____

### I27 — Describe activity in normal/Normal_Videos_289_x264.mp4 between 5 and 10 seconds without confirming any crime.

Expected facts (locked FULL grade in brackets):
- [F01] video carries no annotated anomaly interval [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: normal/Normal_Videos_289_x264.mp4:f3, normal/Normal_Videos_289_x264.mp4:f4, normal/Normal_Videos_289_x264.mp4:f2

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
plan queries: [{"query": "activity", "source": "generic_action"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: normal/Normal_Videos_289_x264.mp4:f3, normal/Normal_Videos_289_x264.mp4:f4, normal/Normal_Videos_289_x264.mp4:f2

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I28 — Show evidence in anomaly/RoadAccidents/RoadAccidents021_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] only 3 evidence windows exist in total [locked full: Partial]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/RoadAccidents/RoadAccidents021_x264.mp4:f2, anomaly/RoadAccidents/RoadAccidents021_x264.mp4:f1, anomaly/RoadAccidents/RoadAccidents021_x264.mp4:f0

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
plan queries: [{"query": "road accident", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/RoadAccidents/RoadAccidents021_x264.mp4:f2, anomaly/RoadAccidents/RoadAccidents021_x264.mp4:f1, anomaly/RoadAccidents/RoadAccidents021_x264.mp4:f0

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I29 — Show evidence in anomaly/Shooting/Shooting037_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] only 5 evidence windows exist in total [locked full: Unsupported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shooting/Shooting037_x264.mp4:f1, anomaly/Shooting/Shooting037_x264.mp4:f3, anomaly/Shooting/Shooting037_x264.mp4:f2, anomaly/Shooting/Shooting037_x264.mp4:f4, anomaly/Shooting/Shooting037_x264.mp4:f0

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
- timeline: {"end_time": 10.134, "evidence_ids": ["anomaly/Shooting/Shooting037_x264.mp4:f0", "anomaly/Shooting/Shooting037_x264.mp4:f1", "anomaly/Shooting/Shooting037_x264.mp4:f2", "anomaly/Shooting/Shooting037_x264.mp4:f3", "anomaly/Shooting/Shooting037_x264.mp4:f4"], "observation": {"evidence_ids": ["anomaly/Shooting/Shooting037_x264.mp4:f0", "anomaly/Shooting/Shooting037_x264.mp4:f1", "anomaly/Shooting/Sh
- correlations: {"description": "All five records belong to the same Phase 2D incident anomaly/Shooting/Shooting037_x264.mp4:i0 in the same video.", "evidence_ids": ["anomaly/Shooting/Shooting037_x264.mp4:f0", "anomaly/Shooting/Shooting037_x264.mp4:f1", "anomaly/Shooting/Shooting037_x264.mp4:f2", "anomaly/Shooting/Shooting037_x264.mp4:f3", "anomaly/Shooting/Shooting037_x264.mp4:f4"], "type": "same_incident"}
- correlations: {"description": "The f0 interval occurs before f1, which occurs before f2, which occurs before f3, which occurs before f4, indicating temporal sequence.", "evidence_ids": ["anomaly/Shooting/Shooting037_x264.mp4:f0", "anomaly/Shooting/Shooting037_x264.mp4:f1", "anomaly/Shooting/Shooting037_x264.mp4:f2", "anomaly/Shooting/Shooting037_x264.mp4:f3", "anomaly/Shooting/Shooting037_x264.mp4:f4"], "type":
- correlations: {"description": "Compatible Shooting hypotheses persist across adjacent windows from 0.0s to 10.134s, suggesting a persistent event hypothesis only, not confirmation.", "evidence_ids": ["anomaly/Shooting/Shooting037_x264.mp4:f0", "anomaly/Shooting/Shooting037_x264.mp4:f1", "anomaly/Shooting/Shooting037_x264.mp4:f2", "anomaly/Shooting/Shooting037_x264.mp4:f3", "anomaly/Shooting/Shooting037_x264.mp4
- correlations: {"description": "Surveillance_event, object, and generic_action sources co-occur in the same windows, indicating source agreement only and never confirmation of a crime or behavior.", "evidence_ids": ["anomaly/Shooting/Shooting037_x264.mp4:f0", "anomaly/Shooting/Shooting037_x264.mp4:f1", "anomaly/Shooting/Shooting037_x264.mp4:f2", "anomaly/Shooting/Shooting037_x264.mp4:f3", "anomaly/Shooting/Shoot
- inferences: {"evidence_ids": ["anomaly/Shooting/Shooting037_x264.mp4:f0", "anomaly/Shooting/Shooting037_x264.mp4:f1", "anomaly/Shooting/Shooting037_x264.mp4:f2", "anomaly/Shooting/Shooting037_x264.mp4:f3", "anomaly/Shooting/Shooting037_x264.mp4:f4"], "text": "The available evidence suggests a persistent Shooting hypothesis co-occurring with car detections and driving car hypotheses throughout the video, but t
- inferences: {"evidence_ids": ["anomaly/Shooting/Shooting037_x264.mp4:f0", "anomaly/Shooting/Shooting037_x264.mp4:f1", "anomaly/Shooting/Shooting037_x264.mp4:f2", "anomaly/Shooting/Shooting037_x264.mp4:f3", "anomaly/Shooting/Shooting037_x264.mp4:f4"], "text": "The evidence indicates car counts of 3-4 in early to middle windows and 2 in the final window, but the available evidence is insufficient to explain the
plan queries: [{"query": "shooting", "source": "surveillance_event"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Shooting/Shooting037_x264.mp4:f1, anomaly/Shooting/Shooting037_x264.mp4:f2, anomaly/Shooting/Shooting037_x264.mp4:f3, anomaly/Shooting/Shooting037_x264.mp4:f4, anomaly/Shooting/Shooting037_x264.mp4:f0

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

### I30 — Show truck detections in anomaly/Arson/Arson009_x264.mp4.

Expected facts (locked FULL grade in brackets):
- [F01] no evidence window carries a truck detection [locked full: Supported]

#### no-temporal
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Arson/Arson009_x264.mp4:f5, anomaly/Arson/Arson009_x264.mp4:f7, anomaly/Arson/Arson009_x264.mp4:f9, anomaly/Arson/Arson009_x264.mp4:f4, anomaly/Arson/Arson009_x264.mp4:f1, anomaly/Arson/Arson009_x264.mp4:f6, anomaly/Arson/Arson009_x264.mp4:f8, anomaly/Arson/Arson009_x264.mp4:f10, anomaly/Arson/Arson009_x264.mp4:f2, anomaly/Arson/Arson009_x264.mp4:f3

Grades for no-temporal:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-verification
plan queries: [{"query": "truck", "source": "object"}]

Grades for no-verification:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

#### no-planning
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.
retrieved: anomaly/Arson/Arson009_x264.mp4:f5, anomaly/Arson/Arson009_x264.mp4:f7, anomaly/Arson/Arson009_x264.mp4:f9, anomaly/Arson/Arson009_x264.mp4:f4, anomaly/Arson/Arson009_x264.mp4:f1, anomaly/Arson/Arson009_x264.mp4:f6, anomaly/Arson/Arson009_x264.mp4:f8, anomaly/Arson/Arson009_x264.mp4:f10, anomaly/Arson/Arson009_x264.mp4:f2, anomaly/Arson/Arson009_x264.mp4:f3

Grades for no-planning:
- F01: Grade: ____ Reason: ____ Evidence reference: ____

## Aggregate fields (fill after grading)

No-temporal: Supported = ? Partial = ? Unsupported = ? Total = 46

No-verification: Supported = ? Partial = ? Unsupported = ? Total = 46

No-planning: Supported = ? Partial = ? Unsupported = ? Total = 46
