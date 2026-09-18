# Investigation Human Review Worksheet v1

## Grader instructions (read first)

1. Inspect the cited frozen evidence records for every grade; never grade from memory or prose fluency.
2. Grade each expected fact against the corresponding arm answer: does the answer adequately establish that fact?
3. Do not change the benchmark, the evidence, or any frozen file.
4. Do not use retrieval rankings, scores, or model internals as evidence of correctness.
5. `supported` means the cited evidence actually supports the claim.
6. `partial` means only part of the claim is supported.
7. `unsupported` means the evidence does not establish the claim.
8. For expected facts, grade whether the answer adequately establishes that fact (allowed: supported/partial/unsupported/not_applicable).
9. Do not reward plausible inference when the evidence does not support it.
10. Do not penalize appropriate abstention where evidence is insufficient (I30).
11. Mechanical `status` fields are context only and must not determine human grades.

## I01 — Show person detections in anomaly/Burglary/Burglary032_x264.mp4 between 27 and 49 seconds.

Pattern: direct-object | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] person detected in 9 evidence windows | baseline: ____ full: ____ notes: ____
- [F02] windows span 27.7s to 48.9s | baseline: ____ full: ____ notes: ____
- [F03] Burglary surveillance-event label present in all 9 windows | baseline: ____ full: ____ notes: ____

### Expected temporal relations
- before: anomaly/Burglary/Burglary032_x264.mp4:f13 -> anomaly/Burglary/Burglary032_x264.mp4:f22

### Baseline answer (templated, no LLM reasoning)
- anomaly/Burglary/Burglary032_x264.mp4:f13 | anomaly/Burglary/Burglary032_x264.mp4 | 27.733-29.733s
- anomaly/Burglary/Burglary032_x264.mp4:f14 | anomaly/Burglary/Burglary032_x264.mp4 | 29.867-31.867s
- anomaly/Burglary/Burglary032_x264.mp4:f15 | anomaly/Burglary/Burglary032_x264.mp4 | 32.0-34.0s
- anomaly/Burglary/Burglary032_x264.mp4:f16 | anomaly/Burglary/Burglary032_x264.mp4 | 34.133-36.133s
- anomaly/Burglary/Burglary032_x264.mp4:f17 | anomaly/Burglary/Burglary032_x264.mp4 | 36.267-38.267s
- anomaly/Burglary/Burglary032_x264.mp4:f18 | anomaly/Burglary/Burglary032_x264.mp4 | 38.4-40.4s
- anomaly/Burglary/Burglary032_x264.mp4:f19 | anomaly/Burglary/Burglary032_x264.mp4 | 40.533-42.533s
- anomaly/Burglary/Burglary032_x264.mp4:f20 | anomaly/Burglary/Burglary032_x264.mp4 | 42.667-44.667s
- anomaly/Burglary/Burglary032_x264.mp4:f21 | anomaly/Burglary/Burglary032_x264.mp4 | 44.8-46.8s
- anomaly/Burglary/Burglary032_x264.mp4:f22 | anomaly/Burglary/Burglary032_x264.mp4 | 46.933-48.933s

### Full-arm answer
Title: Person detections with Burglary hypotheses - Burglary032 27-49s
Summary: The retrieved evidence supports person detections in nine of ten windows between 27.733s and 48.933s with counts of 1 to 3, co-occurring with a persistent Burglary hypothesis, with limited generic-action characterization.
- timeline 27.733-29.733: Surveillance-event model produced Burglary hypothesis; object model reported 1 person; generic-action label with moderate confidence.
- timeline 29.867-31.867: Surveillance-event model produced Burglary hypothesis; object model reported no person detection.
- timeline 32.0-34.0: Surveillance-event model produced Burglary hypothesis; object model reported 1 person.
- timeline 34.133-36.133: Surveillance-event model produced Burglary hypothesis; object model reported 2 persons.
- timeline 36.267-38.267: Surveillance-event model produced Burglary hypothesis; object model reported 2 persons.
- timeline 38.4-40.4: Surveillance-event model produced Burglary hypothesis; object model reported 3 persons.
- timeline 40.533-42.533: Surveillance-event model produced Burglary hypothesis; object model reported 2 persons.
- timeline 42.667-44.667: Surveillance-event model produced Burglary hypothesis; object model reported 2 persons.
- timeline 44.8-46.8: Surveillance-event model produced Burglary hypothesis; object model reported 2 persons.
- timeline 46.933-48.933: Surveillance-event model produced Burglary hypothesis; object model reported 1 person.
- finding: The retrieved evidence supports intermittent person detections between 27.733s and 48.933s: 1 person in f13, f15 and f22, 2 persons in f16, f17, f19, f20 and f21, 3 persons in f18, and no person detection in f14.
- finding: The retrieved evidence supports that the surveillance-event model produced a Burglary hypothesis in each window from 27.733s to 48.933s, and that records f13 through f22 belong to the same incident anomaly/Burglary/Burglary032_x264.mp4:i0.
- finding: The available evidence is consistent with temporal co-occurrence of person detections and Burglary hypotheses in nine windows; the evidence indicates this is source agreement only and does not establish involvement or that a crime occurred.
- finding: The evidence indicates activity characterization is limited, as generic-action confidences were low to moderate across the segment.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f14, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f22, mechanical: supported) The available evidence suggests between 27.733s and 48.933s the surveillance-event model produced a Burglary hypothesis in each window, while the object model reported person detections in nine windows with counts of 1 to 3 and no person in one window, with low to moderate generic-action labels. A person detection overlapping a Burglary hypothesis does not mean the detected person was involved. | grade: ____ notes: ____
- [claim_002] (anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f14, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f22, mechanical: supported) persistent_event: The evidence indicates a compatible Burglary hypothesis produced by the surveillance-event model persisted across adjacent windows from 27.733s to 48.933s. | grade: ____ notes: ____
- [claim_003] (anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f14, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f22, mechanical: supported) same_incident: The evidence indicates records f13 through f22 belong to the same Phase 2D incident anomaly/Burglary/Burglary032_x264.mp4:i0. | grade: ____ notes: ____
- [claim_004] (anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f22, mechanical: supported) cross_source_support: The available evidence suggests person detections and Burglary hypotheses temporally co-occurred in the same windows; this co-occurrence is source agreement only and does not confirm involvement or that a crime occurred. | grade: ____ notes: ____
- [claim_005] (anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f14, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f22, mechanical: supported) The available evidence suggests intermittent person presence between 27.733s and 48.933s, with counts of 1 in f13, f15 and f22, 2 in f16, f17, f19, f20 and f21, 3 in f18, and no detection in f14; overlap with the Burglary hypothesis does not indicate participation. | grade: ____ notes: ____
- [claim_006] (anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f14, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f22, mechanical: supported) The available evidence suggests activity characterization is limited, as generic-action confidences were low to moderate across the segment. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 6, "unsupported": 0}
- citation: {"cited": 6, "total": 6}
- temporal_uncontained: 0
- failure: null

## I02 — Show car detections in anomaly/RoadAccidents/RoadAccidents011_x264.mp4.

Pattern: direct-object | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] car detected in 34 evidence windows | baseline: ____ full: ____ notes: ____
- [F02] windows span 0.0s to 71.9s | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)
- anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f1 | anomaly/RoadAccidents/RoadAccidents011_x264.mp4 | 2.133-4.133s
- anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f3 | anomaly/RoadAccidents/RoadAccidents011_x264.mp4 | 6.4-8.4s
- anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f4 | anomaly/RoadAccidents/RoadAccidents011_x264.mp4 | 8.533-10.533s
- anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f8 | anomaly/RoadAccidents/RoadAccidents011_x264.mp4 | 17.067-19.067s
- anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f15 | anomaly/RoadAccidents/RoadAccidents011_x264.mp4 | 32.0-34.0s
- anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f17 | anomaly/RoadAccidents/RoadAccidents011_x264.mp4 | 36.267-38.267s
- anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f21 | anomaly/RoadAccidents/RoadAccidents011_x264.mp4 | 44.8-46.8s
- anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f23 | anomaly/RoadAccidents/RoadAccidents011_x264.mp4 | 49.067-51.067s
- anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f26 | anomaly/RoadAccidents/RoadAccidents011_x264.mp4 | 55.467-57.467s
- anomaly/RoadAccidents/RoadAccidents011_x264.mp4:f30 | anomaly/RoadAccidents/RoadAccidents011_x264.mp4 | 64.0-66.0s

### Full-arm answer
Title: None
Summary: None

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: {"error": "persistent_event windows are not adjacent or nearby", "stage": "3e", "type": "validation"}

## I03 — Show person detections in normal/Normal_Videos_251_x264.mp4.

Pattern: direct-object | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] person detected in 7 evidence windows | baseline: ____ full: ____ notes: ____
- [F02] video carries no annotated anomaly interval | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)
- normal/Normal_Videos_251_x264.mp4:f0 | normal/Normal_Videos_251_x264.mp4 | 0.0-2.0s
- normal/Normal_Videos_251_x264.mp4:f1 | normal/Normal_Videos_251_x264.mp4 | 2.133-4.133s
- normal/Normal_Videos_251_x264.mp4:f2 | normal/Normal_Videos_251_x264.mp4 | 4.267-6.267s
- normal/Normal_Videos_251_x264.mp4:f3 | normal/Normal_Videos_251_x264.mp4 | 6.4-8.4s
- normal/Normal_Videos_251_x264.mp4:f4 | normal/Normal_Videos_251_x264.mp4 | 8.533-10.533s
- normal/Normal_Videos_251_x264.mp4:f5 | normal/Normal_Videos_251_x264.mp4 | 10.667-12.667s
- normal/Normal_Videos_251_x264.mp4:f6 | normal/Normal_Videos_251_x264.mp4 | 12.8-13.467s

### Full-arm answer
Title: Person detections in normal/Normal_Videos_251_x264.mp4 (0.0s-13.467s)
Summary: Retrieved evidence from 0.0s to 13.467s shows person detections in each window f0-f6 with vehicle detections and RoadAccidents model hypotheses co-occurring. Truck was not detected in one window and gaps between windows are uncovered. Identity, role, and whether any road accident occurred are not established.
- timeline 0.0-2.0: The retrieved evidence supports 1 person (max 0.4069), 7 car, 5 truck detections; the surveillance-event model produced a RoadAccidents hypothesis (0.9384).
- timeline 2.133-4.133: The retrieved evidence supports 1 person (max 0.8227), 4 car, 3 truck detections; the surveillance-event model produced a RoadAccidents hypothesis (0.8975).
- timeline 4.267-6.267: The retrieved evidence supports 2 persons (max 0.9315), 6 car detections with no truck detection; the surveillance-event model produced a RoadAccidents hypothesis (0.9017).
- timeline 6.4-8.4: The retrieved evidence supports 1 person (max 0.8074), 6 car, 1 truck detections; the surveillance-event model produced a RoadAccidents hypothesis (0.8049).
- timeline 8.533-10.533: The retrieved evidence supports 2 persons (max 0.9079), 6 car, 2 truck detections; the surveillance-event model produced a RoadAccidents hypothesis (0.827).
- timeline 10.667-12.667: The retrieved evidence supports 2 persons (max 0.8649), 4 car, 2 truck detections; the surveillance-event model produced a RoadAccidents hypothesis (0.8022).
- timeline 12.8-13.467: The retrieved evidence supports 2 persons (max 0.8445), 2 car, 1 truck detections; the surveillance-event model produced a RoadAccidents hypothesis (0.5804).
- finding: The retrieved evidence supports person detections in each cited window: 1 person in f0 (max 0.4069), f1 (0.8227), f3 (0.8074) and 2 persons in f2 (0.9315), f4 (0.9079), f5 (0.8649), f6 (0.8445). The available evidence is consistent with repeated person presence across windows but does not establish identity, role, or involvement in any event.
- finding: The retrieved evidence supports car detections in all windows f0-f6 and truck detections in f0, f1, f3, f4, f5, f6, with no truck detection in f2. The surveillance-event model produced a RoadAccidents hypothesis in each window (0.9384 to 0.5804). The available evidence is consistent with co-occurrence only and does not confirm that a road accident occurred.
- finding: The retrieved evidence supports that f0 through f6 belong to the same Phase 2D incident normal/Normal_Videos_251_x264.mp4:i0 spanning 0.0s to 13.467s with RoadAccidents event hypothesis.

### Full-arm claims (grade each)
- [claim_001] (normal/Normal_Videos_251_x264.mp4:f0, normal/Normal_Videos_251_x264.mp4:f1, normal/Normal_Videos_251_x264.mp4:f2, normal/Normal_Videos_251_x264.mp4:f3, normal/Normal_Videos_251_x264.mp4:f4, normal/Normal_Videos_251_x264.mp4:f5, normal/Normal_Videos_251_x264.mp4:f6, mechanical: partially_supported) The evidence indicates person detections in every window from 0.0s to 13.467s with 1-2 persons per window and max confidences 0.4069 to 0.9315; the model also produced car and truck detections and RoadAccidents hypotheses in the same windows. | grade: ____ notes: ____
- [claim_002] (normal/Normal_Videos_251_x264.mp4:f0, normal/Normal_Videos_251_x264.mp4:f1, normal/Normal_Videos_251_x264.mp4:f2, normal/Normal_Videos_251_x264.mp4:f3, normal/Normal_Videos_251_x264.mp4:f4, normal/Normal_Videos_251_x264.mp4:f5, normal/Normal_Videos_251_x264.mp4:f6, mechanical: partially_supported) persistent_event: The evidence indicates compatible person detections persist across adjacent windows from 0.0s to 13.467s. | grade: ____ notes: ____
- [claim_003] (normal/Normal_Videos_251_x264.mp4:f0, normal/Normal_Videos_251_x264.mp4:f1, normal/Normal_Videos_251_x264.mp4:f2, normal/Normal_Videos_251_x264.mp4:f3, normal/Normal_Videos_251_x264.mp4:f4, normal/Normal_Videos_251_x264.mp4:f5, normal/Normal_Videos_251_x264.mp4:f6, mechanical: supported) same_incident: The evidence indicates f0 through f6 belong to the same Phase 2D incident normal/Normal_Videos_251_x264.mp4:i0. | grade: ____ notes: ____
- [claim_004] (normal/Normal_Videos_251_x264.mp4:f0, normal/Normal_Videos_251_x264.mp4:f1, normal/Normal_Videos_251_x264.mp4:f2, normal/Normal_Videos_251_x264.mp4:f3, normal/Normal_Videos_251_x264.mp4:f4, normal/Normal_Videos_251_x264.mp4:f5, normal/Normal_Videos_251_x264.mp4:f6, mechanical: supported) cross_source_support: The evidence indicates object detections including person co-occur with surveillance_event RoadAccidents hypotheses in the same windows; this is source agreement only and does not confirm an event. | grade: ____ notes: ____
- [claim_005] (normal/Normal_Videos_251_x264.mp4:f0, normal/Normal_Videos_251_x264.mp4:f1, normal/Normal_Videos_251_x264.mp4:f2, normal/Normal_Videos_251_x264.mp4:f3, normal/Normal_Videos_251_x264.mp4:f4, normal/Normal_Videos_251_x264.mp4:f5, normal/Normal_Videos_251_x264.mp4:f6, mechanical: supported) The available evidence suggests person presence persisted throughout the segment, but the evidence does not indicate identity, role, or involvement in any event. | grade: ____ notes: ____
- [claim_006] (normal/Normal_Videos_251_x264.mp4:f0, normal/Normal_Videos_251_x264.mp4:f1, normal/Normal_Videos_251_x264.mp4:f2, normal/Normal_Videos_251_x264.mp4:f3, normal/Normal_Videos_251_x264.mp4:f4, normal/Normal_Videos_251_x264.mp4:f5, normal/Normal_Videos_251_x264.mp4:f6, mechanical: supported) The model produced RoadAccidents hypotheses alongside person and vehicle detections, but the evidence is consistent with co-occurrence only and does not confirm that a road accident occurred. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 2, "supported": 4, "unsupported": 0}
- citation: {"cited": 6, "total": 6}
- temporal_uncontained: 0
- failure: null

## I04 — Show driving-car activity in anomaly/RoadAccidents/RoadAccidents016_x264.mp4.

Pattern: activity | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] driving car activity present in 14 evidence windows | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)

### Full-arm answer
Title: Driving-car activity review - RoadAccidents016_x264.mp4
Summary: Requested driving-car activity was found as model-produced hypotheses co-occurring with car/person detections and RoadAccidents hypotheses in early segments, with a later motorcycling hypothesis and an isolated late driving-car hypothesis. The evidence does not establish that an accident occurred, causality, or involvement.
- timeline 0.0-4.133: The retrieved evidence supports car and person detections co-occurring with model-produced driving-car and RoadAccidents hypotheses.
- timeline 6.4-10.533: The retrieved evidence supports car and person detections co-occurring with model-produced driving-car and RoadAccidents hypotheses.
- timeline 17.067-25.467: The retrieved evidence supports car and person detections co-occurring with model-produced driving-car and RoadAccidents hypotheses across adjacent windows.
- timeline 25.6-27.6: The retrieved evidence supports car and person detections co-occurring with a model-produced motorcycling hypothesis and RoadAccidents hypothesis.
- timeline 72.534-72.934: The retrieved evidence supports model-produced driving-car and RoadAccidents hypotheses with no object detections reported.
- finding: The retrieved evidence supports repeated co-occurrence of car and person detections with model-produced driving-car hypotheses and RoadAccidents hypotheses across 0.0-25.467s. The available evidence is consistent with persistent traffic activity, but does not establish that an accident occurred or who was involved.
- finding: The evidence indicates the surveillance-event model produced a RoadAccidents hypothesis persisting from 17.067-27.6s, with driving-car hypotheses in earlier windows and a motorcycling hypothesis at 25.6-27.6s where car and person detections were also reported.
- finding: The evidence indicates an isolated window at 72.534-72.934s where the models produced driving-car and RoadAccidents hypotheses with no object detections reported, providing limited support for interpretation.
- finding: All cited windows belong to the same supplied incident anomaly/RoadAccidents/RoadAccidents016_x264.mp4:i0. Co-occurrence of object detections with generic-action and surveillance-event hypotheses from different source types indicates source agreement only, not confirmation.

### Full-arm claims (grade each)
- [claim_001] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1, mechanical: supported) The evidence indicates car and person detections with model-produced driving-car and RoadAccidents hypotheses persisting across adjacent windows. | grade: ____ notes: ____
- [claim_002] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4, mechanical: supported) The evidence indicates car and person detections with model-produced driving-car and RoadAccidents hypotheses persisting across adjacent windows. | grade: ____ notes: ____
- [claim_003] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f10, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f11, mechanical: supported) The evidence indicates car and person detections with model-produced driving-car and RoadAccidents hypotheses persisting across adjacent windows. | grade: ____ notes: ____
- [claim_004] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f12, mechanical: supported) The evidence indicates car and person detections with model-produced motorcycling and RoadAccidents hypotheses. | grade: ____ notes: ____
- [claim_005] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f34, mechanical: supported) The evidence indicates model-produced driving-car and RoadAccidents hypotheses with no object detections reported. | grade: ____ notes: ____
- [claim_006] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1, mechanical: supported) persistent_event: The model-produced RoadAccidents hypothesis with driving-car hypothesis persists across adjacent windows covering 0.0-4.133s. | grade: ____ notes: ____
- [claim_007] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4, mechanical: supported) persistent_event: The model-produced RoadAccidents hypothesis with driving-car hypothesis persists across adjacent windows covering 6.4-10.533s. | grade: ____ notes: ____
- [claim_008] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f10, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f11, mechanical: supported) persistent_event: The model-produced RoadAccidents hypothesis with driving-car hypothesis persists across adjacent windows covering 17.067-25.467s. | grade: ____ notes: ____
- [claim_009] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f10, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f11, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f12, mechanical: supported) persistent_event: The model-produced RoadAccidents hypothesis persists across adjacent windows covering 17.067-27.6s, with driving-car in earlier windows and motorcycling in the last window. | grade: ____ notes: ____
- [claim_010] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f10, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f11, mechanical: supported) cross_source_support: Within the cited windows, object car and person detections co-occur with driving-car and RoadAccidents hypotheses from different source types, indicating source agreement only, not confirmation. | grade: ____ notes: ____
- [claim_011] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f34, mechanical: supported) temporal_sequence: The evidence in 0.0-4.133s occurs before the evidence in 6.4-10.533s, which occurs before the evidence in 17.067-27.6s, which occurs before the evidence in 72.534-72.934s. | grade: ____ notes: ____
- [claim_012] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f10, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f11, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f12, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f34, mechanical: supported) same_incident: All cited evidence records belong to the same Phase 2D incident anomaly/RoadAccidents/RoadAccidents016_x264.mp4:i0. | grade: ____ notes: ____
- [claim_013] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f0, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f1, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f10, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f11, mechanical: supported) The available evidence suggests driving-car activity hypotheses repeatedly co-occur with car/person detections and RoadAccidents hypotheses from 0.0-25.467s, consistent with persistent traffic activity, but does not establish that an accident occurred or who was involved. | grade: ____ notes: ____
- [claim_014] (anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f12, anomaly/RoadAccidents/RoadAccidents016_x264.mp4:f34, mechanical: supported) The evidence indicates a motorcycling hypothesis at 25.6-27.6s and an isolated driving-car with RoadAccidents hypothesis at 72.534-72.934s without object detections, suggesting continued vehicle-related hypotheses but with limited support for interpretation. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 14, "unsupported": 0}
- citation: {"cited": 14, "total": 14}
- temporal_uncontained: 0
- failure: null

## I05 — Show garbage-collecting activity in anomaly/Shoplifting/Shoplifting020_x264.mp4 between 0 and 100 seconds.

Pattern: activity | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] garbage collecting activity present in 2 evidence windows | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)

### Full-arm answer
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: null

## I06 — Show extinguishing-fire activity in anomaly/Arson/Arson041_x264.mp4.

Pattern: activity | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] extinguishing fire activity present in 2 evidence windows | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)

### Full-arm answer
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: null

## I07 — Show Arrest evidence in anomaly/Arrest/Arrest039_x264.mp4 between 0 and 120 seconds.

Pattern: event | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] Arrest surveillance-event label present in 11 evidence windows | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)
- anomaly/Arrest/Arrest039_x264.mp4:f14 | anomaly/Arrest/Arrest039_x264.mp4 | 29.867-31.867s
- anomaly/Arrest/Arrest039_x264.mp4:f15 | anomaly/Arrest/Arrest039_x264.mp4 | 32.0-34.0s
- anomaly/Arrest/Arrest039_x264.mp4:f16 | anomaly/Arrest/Arrest039_x264.mp4 | 34.133-36.133s
- anomaly/Arrest/Arrest039_x264.mp4:f17 | anomaly/Arrest/Arrest039_x264.mp4 | 36.267-38.267s
- anomaly/Arrest/Arrest039_x264.mp4:f25 | anomaly/Arrest/Arrest039_x264.mp4 | 53.333-55.333s
- anomaly/Arrest/Arrest039_x264.mp4:f30 | anomaly/Arrest/Arrest039_x264.mp4 | 64.0-66.0s
- anomaly/Arrest/Arrest039_x264.mp4:f38 | anomaly/Arrest/Arrest039_x264.mp4 | 81.067-83.067s
- anomaly/Arrest/Arrest039_x264.mp4:f41 | anomaly/Arrest/Arrest039_x264.mp4 | 87.467-89.467s
- anomaly/Arrest/Arrest039_x264.mp4:f44 | anomaly/Arrest/Arrest039_x264.mp4 | 93.867-95.867s
- anomaly/Arrest/Arrest039_x264.mp4:f45 | anomaly/Arrest/Arrest039_x264.mp4 | 96.0-98.0s

### Full-arm answer
Title: Arrest Hypotheses in Arrest039_x264.mp4 (0-120s) - Verification Report
Summary: Between 0-120s in anomaly/Arrest/Arrest039_x264.mp4, retrieved evidence shows person (1-3) and chair (5-12) detections overlapping repeated surveillance-event model Arrest hypotheses (9 windows, confidence 0.3581-0.5051) plus one RoadAccidents hypothesis, with low-confidence generic actions. The evidence does not establish that an arrest occurred, causality, or involvement.
- timeline 29.867-31.867: The evidence indicates 1 person (max 0.6882) and 8 chairs with an Arrest hypothesis (0.4906) and low-confidence unloading truck (0.1344).
- timeline 32.0-34.0: The evidence indicates 3 persons (max 0.8699) and 9 chairs with an Arrest hypothesis (0.4457) and low-confidence unloading truck (0.1307).
- timeline 34.133-36.133: The evidence indicates 2 persons (max 0.8467) and 5 chairs with a RoadAccidents hypothesis (0.4991) and low-confidence headbutting (0.0836).
- timeline 36.267-38.267: The evidence indicates 2 persons (max 0.9106) and 6 chairs with an Arrest hypothesis (0.3581) and low-confidence building cabinet (0.1012).
- timeline 53.333-55.333: The evidence indicates 2 persons (max 0.9097) and 5 chairs with an Arrest hypothesis (0.3735) and low-confidence high kick (0.1103).
- timeline 64.0-66.0: The evidence indicates 3 persons (max 0.8994) and 12 chairs with an Arrest hypothesis (0.4844) and low-confidence side kick (0.1297).
- timeline 81.067-83.067: The evidence indicates 3 persons (max 0.7596) and 6 chairs with an Arrest hypothesis (0.5051) and low-confidence headbutting (0.0586).
- timeline 87.467-89.467: The evidence indicates 2 persons (max 0.8823) and 6 chairs with an Arrest hypothesis (0.49) and low-confidence drop kicking (0.1356).
- timeline 93.867-95.867: The evidence indicates 2 persons (max 0.8673) and 6 chairs with an Arrest hypothesis (0.4638) and low-confidence side kick (0.0907).
- timeline 96.0-98.0: The evidence indicates 3 persons (max 0.8588) and 9 chairs with an Arrest hypothesis (0.4232) and low-confidence unloading truck (0.0939).
- finding: The retrieved evidence supports Arrest hypotheses in three early windows between 29.867s and 38.267s (confidence 0.3581-0.4906) with 1-3 person detections and 6-9 chair detections. The surveillance-event model produced a hypothesis only; the available evidence is consistent with monitored activity but does not confirm that an arrest occurred or who was involved.
- finding: The retrieved evidence supports a RoadAccidents hypothesis (confidence 0.4991) in the 34.133s-36.133s window with 2 person and 5 chair detections. The surveillance-event model produced a hypothesis only and the evidence does not establish that a crime occurred.
- finding: The retrieved evidence supports Arrest hypotheses at 53.333s-55.333s (confidence 0.3735) and 64.0s-66.0s (confidence 0.4844) with 2-3 person detections and 5-12 chair detections. The surveillance-event model produced hypotheses only.
- finding: The retrieved evidence supports Arrest hypotheses at 81.067s-83.067s (confidence 0.5051) and 87.467s-89.467s (confidence 0.49) with 2-3 person detections and 6 chair detections. The surveillance-event model produced hypotheses only.
- finding: The retrieved evidence supports Arrest hypotheses at 93.867s-95.867s (confidence 0.4638) and 96.0s-98.0s (confidence 0.4232) with 2-3 person detections and 6-9 chair detections. Compatible model output persists across nearby windows, which suggests continued model output only, not confirmation.
- finding: The evidence indicates person and chair detections temporally overlap surveillance-event hypotheses within the same windows. This is source agreement only and does not confirm involvement or that a crime occurred. All records belong to the same incident anomaly/Arrest/Arrest039_x264.mp4:i0 in the same video.
- finding: The available evidence suggests generic-action labels remain low-confidence (0.0586-0.1344) and variable (e.g., unloading truck, headbutting, building cabinet, high kick, side kick, drop kicking), providing limited support for characterizing behavior.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Arrest/Arrest039_x264.mp4:f14, anomaly/Arrest/Arrest039_x264.mp4:f15, anomaly/Arrest/Arrest039_x264.mp4:f16, anomaly/Arrest/Arrest039_x264.mp4:f17, mechanical: supported) The evidence indicates person detections (1-3, max confidence 0.6882-0.9106) with chair detections (5-9) from 29.867s to 38.267s. The model produced Arrest hypotheses in three windows (confidence 0.3581-0.4906) and a RoadAccidents hypothesis in one window (confidence 0.4991), with low-confidence generic actions. | grade: ____ notes: ____
- [claim_002] (anomaly/Arrest/Arrest039_x264.mp4:f25, mechanical: supported) The evidence indicates 2 person detections (max confidence 0.9097) with 5 chair detections from 53.333s to 55.333s. The model produced an Arrest hypothesis (confidence 0.3735) with low-confidence high kick. | grade: ____ notes: ____
- [claim_003] (anomaly/Arrest/Arrest039_x264.mp4:f30, mechanical: supported) The evidence indicates 3 person detections (max confidence 0.8994) with 12 chair detections from 64.0s to 66.0s. The model produced an Arrest hypothesis (confidence 0.4844) with low-confidence side kick. | grade: ____ notes: ____
- [claim_004] (anomaly/Arrest/Arrest039_x264.mp4:f38, mechanical: supported) The evidence indicates 3 person detections (max confidence 0.7596) with 6 chair detections from 81.067s to 83.067s. The model produced an Arrest hypothesis (confidence 0.5051) with low-confidence headbutting. | grade: ____ notes: ____
- [claim_005] (anomaly/Arrest/Arrest039_x264.mp4:f41, mechanical: supported) The evidence indicates 2 person detections (max confidence 0.8823) with 6 chair detections from 87.467s to 89.467s. The model produced an Arrest hypothesis (confidence 0.49) with low-confidence drop kicking. | grade: ____ notes: ____
- [claim_006] (anomaly/Arrest/Arrest039_x264.mp4:f44, anomaly/Arrest/Arrest039_x264.mp4:f45, mechanical: supported) The evidence indicates person detections (2-3, max confidence 0.8588-0.8673) with chair detections (6-9) from 93.867s to 98.0s. The model produced Arrest hypotheses (confidence 0.4232-0.4638) with low-confidence side kick and unloading truck. | grade: ____ notes: ____
- [claim_007] (anomaly/Arrest/Arrest039_x264.mp4:f14, anomaly/Arrest/Arrest039_x264.mp4:f15, anomaly/Arrest/Arrest039_x264.mp4:f16, anomaly/Arrest/Arrest039_x264.mp4:f17, anomaly/Arrest/Arrest039_x264.mp4:f25, anomaly/Arrest/Arrest039_x264.mp4:f30, anomaly/Arrest/Arrest039_x264.mp4:f38, anomaly/Arrest/Arrest039_x264.mp4:f41, anomaly/Arrest/Arrest039_x264.mp4:f44, anomaly/Arrest/Arrest039_x264.mp4:f45, mechanical: supported) same_incident: The evidence records belong to the same Phase 2D incident anomaly/Arrest/Arrest039_x264.mp4:i0 in the same video. | grade: ____ notes: ____
- [claim_008] (anomaly/Arrest/Arrest039_x264.mp4:f14, anomaly/Arrest/Arrest039_x264.mp4:f15, mechanical: supported) persistent_event: The evidence indicates compatible Arrest hypotheses persist across adjacent windows from 29.867s to 34.0s; this suggests continued model output only, not confirmation. | grade: ____ notes: ____
- [claim_009] (anomaly/Arrest/Arrest039_x264.mp4:f44, anomaly/Arrest/Arrest039_x264.mp4:f45, mechanical: supported) persistent_event: The evidence indicates compatible Arrest hypotheses persist across nearby windows from 93.867s to 98.0s; this suggests continued model output only, not confirmation. | grade: ____ notes: ____
- [claim_010] (anomaly/Arrest/Arrest039_x264.mp4:f14, anomaly/Arrest/Arrest039_x264.mp4:f15, anomaly/Arrest/Arrest039_x264.mp4:f16, anomaly/Arrest/Arrest039_x264.mp4:f17, anomaly/Arrest/Arrest039_x264.mp4:f25, anomaly/Arrest/Arrest039_x264.mp4:f30, anomaly/Arrest/Arrest039_x264.mp4:f38, anomaly/Arrest/Arrest039_x264.mp4:f41, anomaly/Arrest/Arrest039_x264.mp4:f44, anomaly/Arrest/Arrest039_x264.mp4:f45, mechanical: supported) cross_source_support: The evidence indicates person and chair detections temporally overlap surveillance-event hypotheses within the same windows; this is source agreement only and does not confirm involvement or that a crime occurred. | grade: ____ notes: ____
- [claim_011] (anomaly/Arrest/Arrest039_x264.mp4:f17, anomaly/Arrest/Arrest039_x264.mp4:f25, mechanical: supported) temporal_sequence: The evidence interval 36.267s-38.267s occurs before the evidence interval 53.333s-55.333s. | grade: ____ notes: ____
- [claim_012] (anomaly/Arrest/Arrest039_x264.mp4:f14, anomaly/Arrest/Arrest039_x264.mp4:f15, anomaly/Arrest/Arrest039_x264.mp4:f17, anomaly/Arrest/Arrest039_x264.mp4:f25, anomaly/Arrest/Arrest039_x264.mp4:f30, anomaly/Arrest/Arrest039_x264.mp4:f38, anomaly/Arrest/Arrest039_x264.mp4:f41, anomaly/Arrest/Arrest039_x264.mp4:f44, anomaly/Arrest/Arrest039_x264.mp4:f45, mechanical: supported) The available evidence suggests repeated Arrest model hypotheses between 29.867s and 98.0s with persistent person and chair detections, which is consistent with ongoing monitored activity but does not confirm that an arrest occurred or who was involved. | grade: ____ notes: ____
- [claim_013] (anomaly/Arrest/Arrest039_x264.mp4:f14, anomaly/Arrest/Arrest039_x264.mp4:f15, anomaly/Arrest/Arrest039_x264.mp4:f16, anomaly/Arrest/Arrest039_x264.mp4:f17, anomaly/Arrest/Arrest039_x264.mp4:f25, anomaly/Arrest/Arrest039_x264.mp4:f30, anomaly/Arrest/Arrest039_x264.mp4:f38, anomaly/Arrest/Arrest039_x264.mp4:f41, anomaly/Arrest/Arrest039_x264.mp4:f44, anomaly/Arrest/Arrest039_x264.mp4:f45, mechanical: supported) The available evidence suggests generic-action labels remain low-confidence and variable, providing limited support for characterizing behavior. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 13, "unsupported": 0}
- citation: {"cited": 13, "total": 13}
- temporal_uncontained: 0
- failure: null

## I08 — Show Shoplifting evidence in anomaly/Shoplifting/Shoplifting044_x264.mp4 between 0 and 60 seconds.

Pattern: event | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] Shoplifting surveillance-event label present in 23 evidence windows | baseline: ____ full: ____ notes: ____
- [F02] windows span 0.0s to 61.7s | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)
- anomaly/Shoplifting/Shoplifting044_x264.mp4:f7 | anomaly/Shoplifting/Shoplifting044_x264.mp4 | 14.933-16.933s
- anomaly/Shoplifting/Shoplifting044_x264.mp4:f8 | anomaly/Shoplifting/Shoplifting044_x264.mp4 | 17.067-19.067s
- anomaly/Shoplifting/Shoplifting044_x264.mp4:f10 | anomaly/Shoplifting/Shoplifting044_x264.mp4 | 21.333-23.333s
- anomaly/Shoplifting/Shoplifting044_x264.mp4:f11 | anomaly/Shoplifting/Shoplifting044_x264.mp4 | 23.467-25.467s
- anomaly/Shoplifting/Shoplifting044_x264.mp4:f13 | anomaly/Shoplifting/Shoplifting044_x264.mp4 | 27.733-29.733s
- anomaly/Shoplifting/Shoplifting044_x264.mp4:f15 | anomaly/Shoplifting/Shoplifting044_x264.mp4 | 32.0-34.0s
- anomaly/Shoplifting/Shoplifting044_x264.mp4:f17 | anomaly/Shoplifting/Shoplifting044_x264.mp4 | 36.267-38.267s
- anomaly/Shoplifting/Shoplifting044_x264.mp4:f20 | anomaly/Shoplifting/Shoplifting044_x264.mp4 | 42.667-44.667s
- anomaly/Shoplifting/Shoplifting044_x264.mp4:f21 | anomaly/Shoplifting/Shoplifting044_x264.mp4 | 44.8-46.8s
- anomaly/Shoplifting/Shoplifting044_x264.mp4:f22 | anomaly/Shoplifting/Shoplifting044_x264.mp4 | 46.933-48.933s

### Full-arm answer
Title: Shoplifting model hypotheses in Shoplifting044_x264.mp4 14.9-48.9s
Summary: For anomaly/Shoplifting/Shoplifting044_x264.mp4 0-60s, retrieved evidence shows ten windows from 14.933s to 48.933s with Shoplifting model hypotheses co-located with person detections, and suitcase detections in four windows. The evidence does not establish that shoplifting occurred or that any person was involved.
- timeline 14.933-25.467: The evidence indicates 2 person detections in each window with Shoplifting hypotheses at 0.72-0.93 confidence and low-confidence generic actions. One window includes 1 suitcase detection. Consistent with co-location only.
- timeline 27.733-38.267: The evidence indicates 1 to 3 person detections with Shoplifting hypotheses at 0.86-0.93 confidence and low-confidence generic actions. One window includes 3 suitcase detections. Consistent with co-location only.
- timeline 42.667-48.933: The evidence indicates 2 person detections in each window with Shoplifting hypotheses at 0.96-0.98 confidence and low-confidence generic actions. Two windows include 1-2 suitcase detections. Consistent with co-location only.
- finding: The retrieved evidence supports persistent Shoplifting surveillance-event model hypotheses co-located with person detections from about 14.9s to about 48.9s. The surveillance-event model produced Shoplifting hypotheses ranging from 0.72 to 0.98 confidence across the ten windows. The available evidence is consistent with a persistent model event only and does not establish that any crime occurred or that any detected person was involved.
- finding: The evidence indicates suitcase detections in four windows alongside person detections and Shoplifting hypotheses: 1 suitcase in two windows, 2 suitcases in one window, and 3 suitcases in one window. The available evidence is consistent with co-location only and does not indicate use or involvement.
- finding: The retrieved evidence supports that all ten windows belong to the same video and same Phase 2D incident, with object detections of person co-occurring with Shoplifting hypotheses indicating source agreement only and not confirmation. The model produced only very low-confidence generic action labels (0.038-0.129), suggesting limited interpretive value from that source type.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Shoplifting/Shoplifting044_x264.mp4:f7, anomaly/Shoplifting/Shoplifting044_x264.mp4:f8, anomaly/Shoplifting/Shoplifting044_x264.mp4:f10, anomaly/Shoplifting/Shoplifting044_x264.mp4:f11, mechanical: supported) The evidence indicates 2 person detections in each window with Shoplifting model hypotheses at 0.72-0.93 confidence. One window includes 1 suitcase detection. Generic action hypotheses were low confidence. The evidence is consistent with co-location only and does not show involvement. | grade: ____ notes: ____
- [claim_002] (anomaly/Shoplifting/Shoplifting044_x264.mp4:f13, anomaly/Shoplifting/Shoplifting044_x264.mp4:f15, anomaly/Shoplifting/Shoplifting044_x264.mp4:f17, mechanical: supported) The evidence indicates 1 to 3 person detections with Shoplifting model hypotheses at 0.86-0.93 confidence. One window includes 3 suitcase detections. Generic action hypotheses were low confidence. The evidence is consistent with co-location only. | grade: ____ notes: ____
- [claim_003] (anomaly/Shoplifting/Shoplifting044_x264.mp4:f20, anomaly/Shoplifting/Shoplifting044_x264.mp4:f21, anomaly/Shoplifting/Shoplifting044_x264.mp4:f22, mechanical: supported) The evidence indicates 2 person detections in each window with Shoplifting model hypotheses at 0.96-0.98 confidence. Two windows include 1-2 suitcase detections. Generic action hypotheses were low confidence. The evidence is consistent with co-location only. | grade: ____ notes: ____
- [claim_004] (anomaly/Shoplifting/Shoplifting044_x264.mp4:f7, anomaly/Shoplifting/Shoplifting044_x264.mp4:f8, anomaly/Shoplifting/Shoplifting044_x264.mp4:f10, anomaly/Shoplifting/Shoplifting044_x264.mp4:f11, anomaly/Shoplifting/Shoplifting044_x264.mp4:f13, anomaly/Shoplifting/Shoplifting044_x264.mp4:f15, anomaly/Shoplifting/Shoplifting044_x264.mp4:f17, anomaly/Shoplifting/Shoplifting044_x264.mp4:f20, anomaly/Shoplifting/Shoplifting044_x264.mp4:f21, anomaly/Shoplifting/Shoplifting044_x264.mp4:f22, mechanical: supported) same_incident: All ten evidence records belong to the same Phase 2D incident anomaly/Shoplifting/Shoplifting044_x264.mp4:i0 in the same video. | grade: ____ notes: ____
- [claim_005] (anomaly/Shoplifting/Shoplifting044_x264.mp4:f7, anomaly/Shoplifting/Shoplifting044_x264.mp4:f8, anomaly/Shoplifting/Shoplifting044_x264.mp4:f10, anomaly/Shoplifting/Shoplifting044_x264.mp4:f11, anomaly/Shoplifting/Shoplifting044_x264.mp4:f13, anomaly/Shoplifting/Shoplifting044_x264.mp4:f15, anomaly/Shoplifting/Shoplifting044_x264.mp4:f17, anomaly/Shoplifting/Shoplifting044_x264.mp4:f20, anomaly/Shoplifting/Shoplifting044_x264.mp4:f21, anomaly/Shoplifting/Shoplifting044_x264.mp4:f22, mechanical: supported) persistent_event: Compatible Shoplifting model hypotheses with person detections persist across adjacent and nearby windows from about 14.9s to about 48.9s, consistent with a persistent model event only. | grade: ____ notes: ____
- [claim_006] (anomaly/Shoplifting/Shoplifting044_x264.mp4:f7, anomaly/Shoplifting/Shoplifting044_x264.mp4:f22, mechanical: supported) temporal_sequence: The evidence window at 14.933s-16.933s occurs before the evidence window at 46.933s-48.933s. | grade: ____ notes: ____
- [claim_007] (anomaly/Shoplifting/Shoplifting044_x264.mp4:f8, anomaly/Shoplifting/Shoplifting044_x264.mp4:f15, anomaly/Shoplifting/Shoplifting044_x264.mp4:f21, anomaly/Shoplifting/Shoplifting044_x264.mp4:f22, mechanical: supported) cross_source_support: Object detections of person and suitcase co-occur in the same windows as Shoplifting model hypotheses, indicating source agreement only and not confirmation, and not showing person involvement. | grade: ____ notes: ____
- [claim_008] (anomaly/Shoplifting/Shoplifting044_x264.mp4:f7, anomaly/Shoplifting/Shoplifting044_x264.mp4:f8, anomaly/Shoplifting/Shoplifting044_x264.mp4:f10, anomaly/Shoplifting/Shoplifting044_x264.mp4:f11, anomaly/Shoplifting/Shoplifting044_x264.mp4:f13, anomaly/Shoplifting/Shoplifting044_x264.mp4:f15, anomaly/Shoplifting/Shoplifting044_x264.mp4:f17, anomaly/Shoplifting/Shoplifting044_x264.mp4:f20, anomaly/Shoplifting/Shoplifting044_x264.mp4:f21, anomaly/Shoplifting/Shoplifting044_x264.mp4:f22, mechanical: supported) The available evidence suggests persistent Shoplifting model hypotheses co-located with person detections between about 14.9s and 48.9s, but does not establish that any crime occurred or that any detected person was involved. | grade: ____ notes: ____
- [claim_009] (anomaly/Shoplifting/Shoplifting044_x264.mp4:f8, anomaly/Shoplifting/Shoplifting044_x264.mp4:f15, anomaly/Shoplifting/Shoplifting044_x264.mp4:f21, anomaly/Shoplifting/Shoplifting044_x264.mp4:f22, mechanical: supported) The evidence indicates suitcase detections in some windows alongside person detections and Shoplifting hypotheses, which is consistent with co-location only and does not indicate use or involvement. | grade: ____ notes: ____
- [claim_010] (anomaly/Shoplifting/Shoplifting044_x264.mp4:f7, anomaly/Shoplifting/Shoplifting044_x264.mp4:f8, anomaly/Shoplifting/Shoplifting044_x264.mp4:f10, anomaly/Shoplifting/Shoplifting044_x264.mp4:f11, anomaly/Shoplifting/Shoplifting044_x264.mp4:f13, anomaly/Shoplifting/Shoplifting044_x264.mp4:f15, anomaly/Shoplifting/Shoplifting044_x264.mp4:f17, anomaly/Shoplifting/Shoplifting044_x264.mp4:f20, anomaly/Shoplifting/Shoplifting044_x264.mp4:f21, anomaly/Shoplifting/Shoplifting044_x264.mp4:f22, mechanical: supported) The model produced only very low-confidence generic action labels, suggesting limited interpretive value from that source type for these windows. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 10, "unsupported": 0}
- citation: {"cited": 10, "total": 10}
- temporal_uncontained: 0
- failure: null

## I09 — Show Burglary evidence in anomaly/Burglary/Burglary033_x264.mp4.

Pattern: event | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] Burglary surveillance-event label present in 20 evidence windows | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)
- anomaly/Burglary/Burglary033_x264.mp4:f0 | anomaly/Burglary/Burglary033_x264.mp4 | 0.0-2.0s
- anomaly/Burglary/Burglary033_x264.mp4:f2 | anomaly/Burglary/Burglary033_x264.mp4 | 4.267-6.267s
- anomaly/Burglary/Burglary033_x264.mp4:f4 | anomaly/Burglary/Burglary033_x264.mp4 | 8.533-10.533s
- anomaly/Burglary/Burglary033_x264.mp4:f8 | anomaly/Burglary/Burglary033_x264.mp4 | 17.067-19.067s
- anomaly/Burglary/Burglary033_x264.mp4:f9 | anomaly/Burglary/Burglary033_x264.mp4 | 19.2-21.2s
- anomaly/Burglary/Burglary033_x264.mp4:f10 | anomaly/Burglary/Burglary033_x264.mp4 | 21.334-23.334s
- anomaly/Burglary/Burglary033_x264.mp4:f12 | anomaly/Burglary/Burglary033_x264.mp4 | 25.6-27.6s
- anomaly/Burglary/Burglary033_x264.mp4:f14 | anomaly/Burglary/Burglary033_x264.mp4 | 29.867-31.867s
- anomaly/Burglary/Burglary033_x264.mp4:f15 | anomaly/Burglary/Burglary033_x264.mp4 | 32.0-34.0s
- anomaly/Burglary/Burglary033_x264.mp4:f16 | anomaly/Burglary/Burglary033_x264.mp4 | 34.134-36.134s

### Full-arm answer
Title: Burglary Model Hypotheses in Burglary033_x264.mp4 – Verification Report
Summary: The retrieved evidence supports recurring Burglary surveillance-event hypotheses across 0.0s-36.134s in anomaly/Burglary/Burglary033_x264.mp4, with early person detections, middle windows with no object detections, and later potted-plant detections. The evidence does not establish that a burglary occurred or that detected persons were involved.
- timeline 0.0-10.533: Early windows show person detections (counts 3, 2, 2) co-occurring with Burglary hypotheses (0.9781, 0.9655, 0.9694) and low-confidence generic actions; overlap does not indicate involvement.
- timeline 17.067-23.334: Middle windows show persistent Burglary hypotheses (0.9804, 0.9766, 0.9756) with no object detections and generic playing organ labels.
- timeline 25.6-36.134: Later windows show persistent Burglary hypotheses (0.9793, 0.9797, 0.9779, 0.9768) co-occurring with potted plant detections and generic playing organ labels.
- finding: The retrieved evidence supports recurring Burglary surveillance-event model hypotheses across 0.0s-36.134s with confidence 0.9655-0.9804. The available evidence is consistent with a persistent model hypothesis but the evidence does not establish that a burglary occurred.
- finding: The evidence indicates person detections (counts 2-3) overlapping in time with Burglary hypotheses in early windows. Source agreement only; the evidence does not establish involvement of detected persons.
- finding: The evidence indicates Burglary hypotheses in 17.067s-23.334s with no object detections and generic playing organ labels, limiting association to persons or objects in that interval.
- finding: The evidence indicates Burglary hypotheses in 25.6s-36.134s co-occurring with potted plant detections and generic playing organ labels. The surveillance-event model produced a Burglary hypothesis; co-occurrence does not establish relevance or causality.
- finding: The retrieved evidence supports that all cited windows belong to the same incident anomaly/Burglary/Burglary033_x264.mp4:i0, with early interval 0.0s-2.0s occurring before late interval 34.134s-36.134s in the same video.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Burglary/Burglary033_x264.mp4:f0, anomaly/Burglary/Burglary033_x264.mp4:f2, anomaly/Burglary/Burglary033_x264.mp4:f4, mechanical: supported) The evidence indicates person detections (counts 2-3) co-occurring with Burglary model hypotheses (confidence 0.9655-0.9781) and low-confidence generic actions; overlap does not indicate involvement. | grade: ____ notes: ____
- [claim_002] (anomaly/Burglary/Burglary033_x264.mp4:f8, anomaly/Burglary/Burglary033_x264.mp4:f9, anomaly/Burglary/Burglary033_x264.mp4:f10, mechanical: supported) The evidence indicates persistent Burglary model hypotheses (confidence 0.9756-0.9804) with no object detections and generic playing organ labels. | grade: ____ notes: ____
- [claim_003] (anomaly/Burglary/Burglary033_x264.mp4:f12, anomaly/Burglary/Burglary033_x264.mp4:f14, anomaly/Burglary/Burglary033_x264.mp4:f15, anomaly/Burglary/Burglary033_x264.mp4:f16, mechanical: supported) The evidence indicates persistent Burglary model hypotheses (confidence 0.9768-0.9797) co-occurring with potted plant detections and generic playing organ labels. | grade: ____ notes: ____
- [claim_004] (anomaly/Burglary/Burglary033_x264.mp4:f0, anomaly/Burglary/Burglary033_x264.mp4:f2, anomaly/Burglary/Burglary033_x264.mp4:f4, mechanical: supported) persistent_event: The evidence indicates compatible Burglary hypotheses persist across early windows 0.0s-10.533s. | grade: ____ notes: ____
- [claim_005] (anomaly/Burglary/Burglary033_x264.mp4:f8, anomaly/Burglary/Burglary033_x264.mp4:f9, anomaly/Burglary/Burglary033_x264.mp4:f10, mechanical: supported) persistent_event: The evidence indicates compatible Burglary hypotheses persist across adjacent windows 17.067s-23.334s. | grade: ____ notes: ____
- [claim_006] (anomaly/Burglary/Burglary033_x264.mp4:f12, anomaly/Burglary/Burglary033_x264.mp4:f14, anomaly/Burglary/Burglary033_x264.mp4:f15, anomaly/Burglary/Burglary033_x264.mp4:f16, mechanical: supported) persistent_event: The evidence indicates compatible Burglary hypotheses persist across nearby windows 25.6s-36.134s. | grade: ____ notes: ____
- [claim_007] (anomaly/Burglary/Burglary033_x264.mp4:f0, anomaly/Burglary/Burglary033_x264.mp4:f2, anomaly/Burglary/Burglary033_x264.mp4:f4, mechanical: supported) cross_source_support: Person object detections and Burglary surveillance-event hypotheses overlap in time; source agreement only, never confirmation of involvement. | grade: ____ notes: ____
- [claim_008] (anomaly/Burglary/Burglary033_x264.mp4:f0, anomaly/Burglary/Burglary033_x264.mp4:f2, anomaly/Burglary/Burglary033_x264.mp4:f4, anomaly/Burglary/Burglary033_x264.mp4:f8, anomaly/Burglary/Burglary033_x264.mp4:f9, anomaly/Burglary/Burglary033_x264.mp4:f10, anomaly/Burglary/Burglary033_x264.mp4:f12, anomaly/Burglary/Burglary033_x264.mp4:f14, anomaly/Burglary/Burglary033_x264.mp4:f15, anomaly/Burglary/Burglary033_x264.mp4:f16, mechanical: supported) same_incident: All cited evidence records belong to the same Phase 2D incident anomaly/Burglary/Burglary033_x264.mp4:i0. | grade: ____ notes: ____
- [claim_009] (anomaly/Burglary/Burglary033_x264.mp4:f0, anomaly/Burglary/Burglary033_x264.mp4:f16, mechanical: supported) temporal_sequence: The early interval 0.0s-2.0s occurs before the late interval 34.134s-36.134s in the same video. | grade: ____ notes: ____
- [claim_010] (anomaly/Burglary/Burglary033_x264.mp4:f0, anomaly/Burglary/Burglary033_x264.mp4:f2, anomaly/Burglary/Burglary033_x264.mp4:f4, anomaly/Burglary/Burglary033_x264.mp4:f8, anomaly/Burglary/Burglary033_x264.mp4:f9, anomaly/Burglary/Burglary033_x264.mp4:f10, anomaly/Burglary/Burglary033_x264.mp4:f12, anomaly/Burglary/Burglary033_x264.mp4:f14, anomaly/Burglary/Burglary033_x264.mp4:f15, anomaly/Burglary/Burglary033_x264.mp4:f16, mechanical: supported) The available evidence suggests the model produced recurring Burglary hypotheses across 0.0s-36.134s, which is consistent with a persistent model hypothesis but does not confirm that a burglary occurred. | grade: ____ notes: ____
- [claim_011] (anomaly/Burglary/Burglary033_x264.mp4:f0, anomaly/Burglary/Burglary033_x264.mp4:f2, anomaly/Burglary/Burglary033_x264.mp4:f4, mechanical: supported) The evidence indicates person detections overlapping Burglary hypotheses in early windows; temporal overlap does not mean the detected persons were involved. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 11, "unsupported": 0}
- citation: {"cited": 11, "total": 11}
- temporal_uncontained: 0
- failure: null

## I10 — Reconstruct the event order in anomaly/Shooting/Shooting010_x264.mp4 between 36 and 42 seconds.

Pattern: temporal | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] annotated Shooting interval is 36.5s to 42.0s (frames 1095-1260 at 30 fps) | baseline: ____ full: ____ notes: ____
- [F02] evidence windows f17, f18, f19 overlap the annotated interval | baseline: ____ full: ____ notes: ____

### Expected temporal relations
- before: anomaly/Shooting/Shooting010_x264.mp4:f17 -> anomaly/Shooting/Shooting010_x264.mp4:f18
- before: anomaly/Shooting/Shooting010_x264.mp4:f18 -> anomaly/Shooting/Shooting010_x264.mp4:f19

### Baseline answer (templated, no LLM reasoning)
- anomaly/Shooting/Shooting010_x264.mp4:f16 | anomaly/Shooting/Shooting010_x264.mp4 | 34.133-36.133s
- anomaly/Shooting/Shooting010_x264.mp4:f17 | anomaly/Shooting/Shooting010_x264.mp4 | 36.267-38.267s
- anomaly/Shooting/Shooting010_x264.mp4:f18 | anomaly/Shooting/Shooting010_x264.mp4 | 38.4-40.4s
- anomaly/Shooting/Shooting010_x264.mp4:f19 | anomaly/Shooting/Shooting010_x264.mp4 | 40.533-42.533s

### Full-arm answer
Title: Event Order Reconstruction: Shooting010 36-42s
Summary: Retrieved evidence for 36-42 seconds shows three sequential windows (36.267s-38.267s, 38.4s-40.4s, 40.533s-42.533s) each with a surveillance-event model-produced RoadAccidents hypothesis and consistent 4-car detections, with varying truck and person detections and low-confidence generic actions.
- timeline 36.267-38.267: 36.267s-38.267s: surveillance-event model produced RoadAccidents hypothesis (0.9896) with 4 cars, 1 truck, 1 person and low-confidence pumping gas (0.102).
- timeline 38.4-40.4: 38.4s-40.4s: surveillance-event model produced RoadAccidents hypothesis (0.9826) with 4 cars, 1 truck, 2 persons and low-confidence pushing car (0.1311).
- timeline 40.533-42.533: 40.533s-42.533s: surveillance-event model produced RoadAccidents hypothesis (0.9527) with 4 cars, 2 trucks, no person detection and low-confidence driving car (0.3658).
- finding: The retrieved evidence supports a persistent surveillance-event model-produced RoadAccidents hypothesis across 34.133s-42.533s, with confidences 0.9954 (34.133s-36.133s), 0.9896 (36.267s-38.267s), 0.9826 (38.4s-40.4s), and 0.9527 (40.533s-42.533s).
- finding: The available evidence is consistent with continued presence of 4 cars in each window and trucks in each window (2, 1, 1, 2) temporally coinciding with the RoadAccidents hypotheses, indicating source agreement only and not confirmation.
- finding: The evidence indicates person detections overlapping the RoadAccidents hypothesis in 34.133s-40.4s (2 persons, 1 person, 2 persons) and no person detection in 40.533s-42.533s; person overlap with a hypothesis does not mean the persons were involved.
- finding: The retrieved evidence supports that generic action hypotheses are low-confidence (driving car 0.2479, pumping gas 0.102, pushing car 0.1311, driving car 0.3658) and are insufficient to determine actions.
- finding: The evidence indicates all four windows belong to the same incident anomaly/Shooting/Shooting010_x264.mp4:i0 and establish order between 36 and 42 seconds as 36.267s-38.267s, then 38.4s-40.4s, then 40.533s-42.533s.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Shooting/Shooting010_x264.mp4:f16, anomaly/Shooting/Shooting010_x264.mp4:f17, anomaly/Shooting/Shooting010_x264.mp4:f18, anomaly/Shooting/Shooting010_x264.mp4:f19, mechanical: supported) The available evidence suggests a persistent RoadAccidents model hypothesis (confidences 0.9954 to 0.9527) from 34.133s to 42.533s with 4 cars in each window, trucks in each window (2,1,1,2), persons detected in 34.133s-40.4s (2,1,2 persons) and no person detection in 40.533s-42.533s, with varying low-confidence generic actions (driving car, pumping gas, pushing car). | grade: ____ notes: ____
- [claim_002] (anomaly/Shooting/Shooting010_x264.mp4:f16, anomaly/Shooting/Shooting010_x264.mp4:f17, anomaly/Shooting/Shooting010_x264.mp4:f18, anomaly/Shooting/Shooting010_x264.mp4:f19, mechanical: supported) persistent_event: The model-produced RoadAccidents hypothesis persists across adjacent windows from 34.133s to 42.533s with 4 cars detected in each window, consistent with a persistent event. | grade: ____ notes: ____
- [claim_003] (anomaly/Shooting/Shooting010_x264.mp4:f16, anomaly/Shooting/Shooting010_x264.mp4:f17, anomaly/Shooting/Shooting010_x264.mp4:f18, anomaly/Shooting/Shooting010_x264.mp4:f19, mechanical: supported) same_incident: All four records belong to the same Phase 2D incident anomaly/Shooting/Shooting010_x264.mp4:i0. | grade: ____ notes: ____
- [claim_004] (anomaly/Shooting/Shooting010_x264.mp4:f17, anomaly/Shooting/Shooting010_x264.mp4:f18, anomaly/Shooting/Shooting010_x264.mp4:f19, mechanical: supported) temporal_sequence: The f17 interval 36.267s-38.267s occurs before f18 38.4s-40.4s which occurs before f19 40.533s-42.533s, establishing order between 36 and 42 seconds. | grade: ____ notes: ____
- [claim_005] (anomaly/Shooting/Shooting010_x264.mp4:f16, anomaly/Shooting/Shooting010_x264.mp4:f17, anomaly/Shooting/Shooting010_x264.mp4:f18, anomaly/Shooting/Shooting010_x264.mp4:f19, mechanical: supported) cross_source_support: Object detections of cars and trucks temporally coincide with RoadAccidents hypotheses in the same windows, indicating source agreement only and not confirmation. | grade: ____ notes: ____
- [claim_006] (anomaly/Shooting/Shooting010_x264.mp4:f17, anomaly/Shooting/Shooting010_x264.mp4:f18, anomaly/Shooting/Shooting010_x264.mp4:f19, mechanical: supported) The available evidence suggests the order between 36 and 42 seconds was f17 (36.267s-38.267s) then f18 (38.4s-40.4s) then f19 (40.533s-42.533s). | grade: ____ notes: ____
- [claim_007] (anomaly/Shooting/Shooting010_x264.mp4:f16, anomaly/Shooting/Shooting010_x264.mp4:f17, anomaly/Shooting/Shooting010_x264.mp4:f18, anomaly/Shooting/Shooting010_x264.mp4:f19, mechanical: supported) The evidence indicates continued presence of 4 cars and 1-2 trucks across the period, with person detections in 34.133s-40.4s and no person detection in 40.533s-42.533s; person overlap with a RoadAccidents hypothesis does not mean the persons were involved. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 7, "unsupported": 0}
- citation: {"cited": 7, "total": 7}
- temporal_uncontained: 0
- failure: null

## I11 — Reconstruct the event order in anomaly/Robbery/Robbery048_x264.mp4 between 14 and 32 seconds.

Pattern: temporal | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] annotated Robbery interval is 15.0s to 31.0s (frames 450-930 at 30 fps) | baseline: ____ full: ____ notes: ____
- [F02] evidence windows f7 through f14 overlap the annotated interval | baseline: ____ full: ____ notes: ____

### Expected temporal relations
- before: anomaly/Robbery/Robbery048_x264.mp4:f7 -> anomaly/Robbery/Robbery048_x264.mp4:f14

### Baseline answer (templated, no LLM reasoning)
- anomaly/Robbery/Robbery048_x264.mp4:f6 | anomaly/Robbery/Robbery048_x264.mp4 | 12.8-14.8s
- anomaly/Robbery/Robbery048_x264.mp4:f7 | anomaly/Robbery/Robbery048_x264.mp4 | 14.933-16.933s
- anomaly/Robbery/Robbery048_x264.mp4:f8 | anomaly/Robbery/Robbery048_x264.mp4 | 17.067-19.067s
- anomaly/Robbery/Robbery048_x264.mp4:f9 | anomaly/Robbery/Robbery048_x264.mp4 | 19.2-21.2s
- anomaly/Robbery/Robbery048_x264.mp4:f10 | anomaly/Robbery/Robbery048_x264.mp4 | 21.333-23.333s
- anomaly/Robbery/Robbery048_x264.mp4:f11 | anomaly/Robbery/Robbery048_x264.mp4 | 23.467-25.467s
- anomaly/Robbery/Robbery048_x264.mp4:f12 | anomaly/Robbery/Robbery048_x264.mp4 | 25.6-27.6s
- anomaly/Robbery/Robbery048_x264.mp4:f13 | anomaly/Robbery/Robbery048_x264.mp4 | 27.734-29.734s
- anomaly/Robbery/Robbery048_x264.mp4:f14 | anomaly/Robbery/Robbery048_x264.mp4 | 29.867-31.867s
- anomaly/Robbery/Robbery048_x264.mp4:f15 | anomaly/Robbery/Robbery048_x264.mp4 | 32.0-34.0s

### Full-arm answer
Title: Event order reconstruction – anomaly/Robbery/Robbery048_x264.mp4 14-32s
Summary: Between the 14-32 second interval, the retrieved evidence supports alternating Shooting and RoadAccidents model hypotheses with varying person counts and low-confidence generic actions, ending with an increase in person detections at the 32s boundary. All labels are model hypotheses and do not establish crimes, roles, or causality.
- timeline 14.933-16.933: The retrieved evidence supports 3 person detections (max 0.8628) overlapping a Shooting hypothesis (0.3823) and eating chips (0.0682).
- timeline 17.067-19.067: The retrieved evidence supports 1 person detection overlapping a RoadAccidents hypothesis (0.4406) and eating chips (0.0427).
- timeline 19.2-21.2: The retrieved evidence supports 1 person detection overlapping a RoadAccidents hypothesis (0.3065), with suitcase (0.4758), toilet (0.768) and cleaning floor (0.0356) detections.
- timeline 21.333-23.333: The retrieved evidence supports 1 person detection and toilet detection (0.7174) overlapping a Shooting hypothesis (0.4221) and cleaning floor (0.1873).
- timeline 23.467-25.467: The retrieved evidence supports 2 person detections overlapping a Shooting hypothesis (0.4181) and cleaning floor (0.2508).
- timeline 25.6-27.6: The retrieved evidence supports a Shooting hypothesis (0.4087) with cleaning floor (0.1688) and no object detections in this window.
- timeline 27.734-29.734: The retrieved evidence supports 2 person detections overlapping a RoadAccidents hypothesis (0.4728) and cleaning floor (0.1656).
- timeline 29.867-31.867: The retrieved evidence supports 3 person detections overlapping a RoadAccidents hypothesis (0.5184) and cleaning floor (0.051).
- timeline 32.0-34.0: The retrieved evidence supports 9 person detections (max 0.9125) overlapping a RoadAccidents hypothesis (0.4158) and slapping (0.0305) at the 32s boundary.
- finding: The retrieved evidence supports the following model-produced order: Shooting hypothesis with 3 persons, then RoadAccidents hypotheses with 1 person, then Shooting hypotheses with 1 to 2 to 0 persons, then RoadAccidents hypotheses with 2 to 3 persons. The surveillance-event model produced these hypotheses; the available evidence is consistent with this sequence but does not establish crimes, involvement, or causality.
- finding: The retrieved evidence supports persistent 1-person detections overlapping RoadAccidents hypotheses (0.4406 then 0.3065) and persistent 2- then 3-person detections overlapping RoadAccidents hypotheses (0.4728 then 0.5184). In the 19.2s-21.2s window the evidence indicates suitcase (0.4758), toilet (0.768) and cleaning floor (0.0356) detections; eating chips (0.0427) is indicated only in the earlier 17.067s-19.067s window, not in the later window.
- finding: The retrieved evidence supports persistent Shooting hypotheses (0.4221, 0.4181, 0.4087) with cleaning floor at low confidence, while person detections change from 1 to 2 to 0 and a toilet detection (0.7174) appears in the first window of this group.
- finding: Person detections from the object source temporally overlap Shooting hypotheses from the surveillance-event source in the same windows. The available evidence indicates source co-occurrence only and does not establish involvement or a crime.
- finding: The retrieved evidence supports an increase from 3 person detections to 9 person detections (max 0.9125) at the 32s boundary overlapping a continued RoadAccidents hypothesis (0.5184 then 0.4158) with slapping at low confidence (0.0305). The available evidence is consistent with a change in scene density but is insufficient to determine cause or roles.
- finding: All cited windows belong to the same incident anomaly/Robbery/Robbery048_x264.mp4:i0 in the same video, and their intervals occur in the order f7 before f8-f9 before f10-f12 before f13-f14 before f15.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Robbery/Robbery048_x264.mp4:f6, mechanical: supported) The evidence indicates 2 person detections (max 0.7491) overlapping a RoadAccidents hypothesis (0.4036) and cleaning floor (0.0781). | grade: ____ notes: ____
- [claim_002] (anomaly/Robbery/Robbery048_x264.mp4:f7, mechanical: supported) The evidence indicates 3 person detections (max 0.8628) overlapping a Shooting hypothesis (0.3823) and eating chips (0.0682). | grade: ____ notes: ____
- [claim_003] (anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f9, mechanical: partially_supported) The evidence indicates persistent 1-person detections overlapping RoadAccidents hypotheses (0.4406 then 0.3065), with suitcase (0.4758) and toilet (0.768) detections and cleaning floor/eating chips at low confidence in the later window. | grade: ____ notes: ____
- [claim_004] (anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f11, anomaly/Robbery/Robbery048_x264.mp4:f12, mechanical: supported) The evidence indicates persistent Shooting hypotheses (0.4221, 0.4181, 0.4087) with cleaning floor at low confidence, while person detections change from 1 to 2 to 0 and a toilet detection appears in the first window. | grade: ____ notes: ____
- [claim_005] (anomaly/Robbery/Robbery048_x264.mp4:f13, anomaly/Robbery/Robbery048_x264.mp4:f14, mechanical: supported) The evidence indicates persistent RoadAccidents hypotheses (0.4728 then 0.5184) overlapping 2 then 3 person detections and cleaning floor at low confidence. | grade: ____ notes: ____
- [claim_006] (anomaly/Robbery/Robbery048_x264.mp4:f15, mechanical: supported) The evidence indicates 9 person detections (max 0.9125) overlapping a RoadAccidents hypothesis (0.4158) and slapping (0.0305) at the 32s boundary. | grade: ____ notes: ____
- [claim_007] (anomaly/Robbery/Robbery048_x264.mp4:f6, anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f9, anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f11, anomaly/Robbery/Robbery048_x264.mp4:f12, anomaly/Robbery/Robbery048_x264.mp4:f13, anomaly/Robbery/Robbery048_x264.mp4:f14, anomaly/Robbery/Robbery048_x264.mp4:f15, mechanical: supported) same_incident: All cited windows belong to the same Phase 2D incident anomaly/Robbery/Robbery048_x264.mp4:i0 in the same video. | grade: ____ notes: ____
- [claim_008] (anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f9, anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f11, anomaly/Robbery/Robbery048_x264.mp4:f12, anomaly/Robbery/Robbery048_x264.mp4:f13, anomaly/Robbery/Robbery048_x264.mp4:f14, anomaly/Robbery/Robbery048_x264.mp4:f15, mechanical: supported) temporal_sequence: The interval for f7 occurs before f8-f9, which occur before f10-f12, which occur before f13-f14, which occur before f15. | grade: ____ notes: ____
- [claim_009] (anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f9, mechanical: supported) persistent_event: Compatible RoadAccidents hypotheses persist across adjacent windows f8 to f9. | grade: ____ notes: ____
- [claim_010] (anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f11, anomaly/Robbery/Robbery048_x264.mp4:f12, mechanical: supported) persistent_event: Compatible Shooting hypotheses persist across adjacent windows f10 to f12. | grade: ____ notes: ____
- [claim_011] (anomaly/Robbery/Robbery048_x264.mp4:f13, anomaly/Robbery/Robbery048_x264.mp4:f14, mechanical: supported) persistent_event: Compatible RoadAccidents hypotheses persist across adjacent windows f13 to f14. | grade: ____ notes: ____
- [claim_012] (anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f11, mechanical: supported) cross_source_support: Person detections from the object source temporally overlap Shooting hypotheses from the surveillance_event source in the same windows; this indicates source co-occurrence only and does not confirm involvement or a crime. | grade: ____ notes: ____
- [claim_013] (anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f9, anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f11, anomaly/Robbery/Robbery048_x264.mp4:f12, anomaly/Robbery/Robbery048_x264.mp4:f13, anomaly/Robbery/Robbery048_x264.mp4:f14, mechanical: supported) The available evidence suggests the model-produced order between ~14.9s and ~31.9s was: Shooting hypothesis with 3 persons, then RoadAccidents hypothesis with 1 person, then Shooting hypothesis with 1 to 2 to 0 persons, then RoadAccidents hypothesis with 2 to 3 persons. | grade: ____ notes: ____
- [claim_014] (anomaly/Robbery/Robbery048_x264.mp4:f14, anomaly/Robbery/Robbery048_x264.mp4:f15, mechanical: supported) The evidence indicates an increase from 3 person detections to 9 person detections at ~32s overlapping a continued RoadAccidents hypothesis, which is consistent with a change in scene density but insufficient to determine cause or roles. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 1, "supported": 13, "unsupported": 0}
- citation: {"cited": 14, "total": 14}
- temporal_uncontained: 0
- failure: null

## I12 — Reconstruct the event order in anomaly/Explosion/Explosion036_x264.mp4 between 65 and 69 seconds.

Pattern: temporal | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] annotated Explosion interval is 65.0s to 69.0s (frames 1950-2070 at 30 fps) | baseline: ____ full: ____ notes: ____
- [F02] 3 evidence windows overlap the annotated interval | baseline: ____ full: ____ notes: ____

### Expected temporal relations
- before: anomaly/Explosion/Explosion036_x264.mp4:f30 -> anomaly/Explosion/Explosion036_x264.mp4:f32

### Baseline answer (templated, no LLM reasoning)
- anomaly/Explosion/Explosion036_x264.mp4:f30 | anomaly/Explosion/Explosion036_x264.mp4 | 64.0-66.0s
- anomaly/Explosion/Explosion036_x264.mp4:f31 | anomaly/Explosion/Explosion036_x264.mp4 | 66.133-68.133s
- anomaly/Explosion/Explosion036_x264.mp4:f32 | anomaly/Explosion/Explosion036_x264.mp4 | 68.267-70.267s

### Full-arm answer
Title: Event Order Reconstruction: anomaly/Explosion/Explosion036_x264.mp4 65-69s
Summary: The retrieved evidence supports that the queried 65-69s interval falls within a persistent period of Explosion hypotheses spanning 64.0-70.267s. Person detections are limited to the earliest portion and generic-action labels show low-confidence extinguishing fire followed by spraying. The evidence does not establish that an explosion occurred or the roles of any persons.
- timeline 64.0-66.0: 64.0-66.0s: The surveillance-event model produced a Explosion hypothesis. The evidence indicates 22 person detections and a low-confidence generic-action label of extinguishing fire in the same window.
- timeline 66.133-68.133: 66.133-68.133s: The surveillance-event model produced a Explosion hypothesis with a low-confidence generic-action label of extinguishing fire and no person detections reported.
- timeline 68.267-70.267: 68.267-70.267s: The surveillance-event model produced a Explosion hypothesis with a low-confidence generic-action label of spraying and no person detections reported.
- finding: The retrieved evidence supports persistent surveillance-event hypotheses labeled Explosion across three adjacent windows spanning 64.0s to 70.267s, which covers the queried 65-69s interval. The surveillance-event model produced a Explosion hypothesis in each window.
- finding: The evidence indicates person detections are limited to the earliest window (22 persons) with no object detections in the later two windows. The available evidence is consistent with presence only and does not establish involvement in the hypothesized event.
- finding: The retrieved evidence supports a window sequence of low-confidence generic-action labels: extinguishing fire followed by extinguishing fire followed by spraying. The low confidence values preclude firm interpretation beyond window sequence.
- finding: The evidence indicates temporal order 64.0-66.0s before 66.133-68.133s before 68.267-70.267s, and all three records belong to the same incident anomaly/Explosion/Explosion036_x264.mp4:i0, providing order for the queried interval.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Explosion/Explosion036_x264.mp4:f30, anomaly/Explosion/Explosion036_x264.mp4:f31, anomaly/Explosion/Explosion036_x264.mp4:f32, mechanical: supported) The evidence indicates persistent surveillance-event hypotheses labeled Explosion across three adjacent windows from 64.0s to 70.267s, covering the queried 65-69s interval. The earliest window includes an object detection of 22 persons and a low-confidence generic-action label of extinguishing fire, followed by extinguishing fire at low confidence and then spraying at low confidence. | grade: ____ notes: ____
- [claim_002] (anomaly/Explosion/Explosion036_x264.mp4:f30, anomaly/Explosion/Explosion036_x264.mp4:f31, anomaly/Explosion/Explosion036_x264.mp4:f32, mechanical: supported) persistent_event: Compatible surveillance-event hypotheses labeled Explosion persist across three adjacent windows from 64.0s to 70.267s. | grade: ____ notes: ____
- [claim_003] (anomaly/Explosion/Explosion036_x264.mp4:f30, anomaly/Explosion/Explosion036_x264.mp4:f31, anomaly/Explosion/Explosion036_x264.mp4:f32, mechanical: supported) temporal_sequence: Evidence window 64.0-66.0s occurs before 66.133-68.133s, which occurs before 68.267-70.267s, providing order for the queried 65-69s interval. | grade: ____ notes: ____
- [claim_004] (anomaly/Explosion/Explosion036_x264.mp4:f30, anomaly/Explosion/Explosion036_x264.mp4:f31, anomaly/Explosion/Explosion036_x264.mp4:f32, mechanical: supported) same_incident: All three evidence records belong to the same Phase 2D incident anomaly/Explosion/Explosion036_x264.mp4:i0. | grade: ____ notes: ____
- [claim_005] (anomaly/Explosion/Explosion036_x264.mp4:f30, anomaly/Explosion/Explosion036_x264.mp4:f31, anomaly/Explosion/Explosion036_x264.mp4:f32, mechanical: supported) cross_source_support: Object source in the earliest window overlaps temporally with surveillance-event and generic-action sources across the interval, indicating source co-occurrence only and not confirmation of involvement. | grade: ____ notes: ____
- [claim_006] (anomaly/Explosion/Explosion036_x264.mp4:f30, anomaly/Explosion/Explosion036_x264.mp4:f31, anomaly/Explosion/Explosion036_x264.mp4:f32, mechanical: supported) The available evidence suggests the queried 65-69s interval falls within a persistent period of Explosion hypotheses spanning 64.0-70.267s, with person detections limited to the earliest portion and not indicating involvement in the hypothesized event. | grade: ____ notes: ____
- [claim_007] (anomaly/Explosion/Explosion036_x264.mp4:f30, anomaly/Explosion/Explosion036_x264.mp4:f31, anomaly/Explosion/Explosion036_x264.mp4:f32, mechanical: supported) The model produced low-confidence generic-action labels of extinguishing fire followed by spraying, which is consistent with fire-related activity but the low confidence values preclude firm interpretation beyond window sequence. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 7, "unsupported": 0}
- citation: {"cited": 7, "total": 7}
- temporal_uncontained: 0
- failure: null

## I13 — Describe the Burglary to Shoplifting transition in anomaly/Shoplifting/Shoplifting034_x264.mp4 around 27 seconds.

Pattern: sequence | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] window f12 carries the Burglary surveillance-event label | baseline: ____ full: ____ notes: ____
- [F02] window f13 carries the Shoplifting surveillance-event label | baseline: ____ full: ____ notes: ____

### Expected temporal relations
- before: anomaly/Shoplifting/Shoplifting034_x264.mp4:f12 -> anomaly/Shoplifting/Shoplifting034_x264.mp4:f13

### Baseline answer (templated, no LLM reasoning)
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f11 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 23.467-25.467s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f12 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 25.6-27.6s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f13 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 27.733-29.733s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f14 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 29.867-31.867s

### Full-arm answer
Title: Burglary to Shoplifting Hypothesis Transition in Shoplifting034_x264.mp4 around 27s
Summary: The retrieved evidence from anomaly/Shoplifting/Shoplifting034_x264.mp4 supports a change in surveillance-event model output from Burglary hypotheses in 23.467-27.6s to Shoplifting hypotheses in 27.733-31.867s, with continued person detections and garbage collecting action hypotheses throughout. Model labels remain hypotheses only.
- timeline 23.467-27.6: The retrieved evidence supports person detections overlapping with surveillance-event model Burglary hypotheses (confidence 0.9392 then 0.4729) and garbage collecting action hypotheses. The available evidence indicates persistence of compatible Burglary hypotheses across these adjacent windows.
- timeline 27.733-31.867: The retrieved evidence supports person detections overlapping with surveillance-event model Shoplifting hypotheses (confidence 0.8643 then 0.9309) and garbage collecting action hypotheses. Compared with the prior interval, the available evidence suggests a transition in model hypotheses from Burglary to Shoplifting.
- finding: The retrieved evidence supports person detections overlapping with surveillance-event model Burglary hypotheses and garbage collecting action hypotheses in the earlier interval. The surveillance-event model produced a Burglary hypothesis in both windows, indicating persistence across adjacent windows.
- finding: The retrieved evidence supports person detections overlapping with surveillance-event model Shoplifting hypotheses and garbage collecting action hypotheses in the later interval. The surveillance-event model produced a Shoplifting hypothesis in both windows, indicating persistence across adjacent windows.
- finding: The available evidence is consistent with a transition in model hypotheses from Burglary to Shoplifting between the earlier and later intervals. Burglary-hypothesis evidence ends at 27.6s and Shoplifting-hypothesis evidence begins at 27.733s.
- finding: All four records belong to the same incident anomaly/Shoplifting/Shoplifting034_x264.mp4:i0. Person object detections overlap in time with Burglary and Shoplifting hypotheses from a different source type, indicating source co-occurrence only. The evidence is consistent with continued person detections across the transition, but the evidence does not establish roles or involvement.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f11, anomaly/Shoplifting/Shoplifting034_x264.mp4:f12, mechanical: supported) The evidence indicates person detections with model-produced Burglary hypotheses and garbage collecting action hypotheses in this segment. | grade: ____ notes: ____
- [claim_002] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f13, anomaly/Shoplifting/Shoplifting034_x264.mp4:f14, mechanical: supported) The evidence indicates person detections with model-produced Shoplifting hypotheses and garbage collecting action hypotheses in this segment. | grade: ____ notes: ____
- [claim_003] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f11, anomaly/Shoplifting/Shoplifting034_x264.mp4:f12, anomaly/Shoplifting/Shoplifting034_x264.mp4:f13, anomaly/Shoplifting/Shoplifting034_x264.mp4:f14, mechanical: supported) same_incident: All four records belong to the same Phase 2D incident anomaly/Shoplifting/Shoplifting034_x264.mp4:i0. | grade: ____ notes: ____
- [claim_004] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f12, anomaly/Shoplifting/Shoplifting034_x264.mp4:f13, mechanical: supported) temporal_sequence: The Burglary-hypothesis evidence occurs before the Shoplifting-hypothesis evidence. | grade: ____ notes: ____
- [claim_005] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f11, anomaly/Shoplifting/Shoplifting034_x264.mp4:f12, mechanical: supported) persistent_event: Compatible Burglary hypotheses persist across adjacent windows. | grade: ____ notes: ____
- [claim_006] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f13, anomaly/Shoplifting/Shoplifting034_x264.mp4:f14, mechanical: supported) persistent_event: Compatible Shoplifting hypotheses persist across adjacent windows. | grade: ____ notes: ____
- [claim_007] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f11, anomaly/Shoplifting/Shoplifting034_x264.mp4:f12, anomaly/Shoplifting/Shoplifting034_x264.mp4:f13, anomaly/Shoplifting/Shoplifting034_x264.mp4:f14, mechanical: supported) cross_source_support: Person object detections overlap in time with Burglary and Shoplifting hypotheses from a different source type, indicating source co-occurrence only. | grade: ____ notes: ____
- [claim_008] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f12, anomaly/Shoplifting/Shoplifting034_x264.mp4:f13, mechanical: supported) The available evidence suggests a transition in model hypotheses from Burglary to Shoplifting between the earlier and later intervals. | grade: ____ notes: ____
- [claim_009] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f11, anomaly/Shoplifting/Shoplifting034_x264.mp4:f12, anomaly/Shoplifting/Shoplifting034_x264.mp4:f13, anomaly/Shoplifting/Shoplifting034_x264.mp4:f14, mechanical: supported) The evidence is consistent with continued person detections across the transition, but does not indicate roles or involvement. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 9, "unsupported": 0}
- citation: {"cited": 9, "total": 9}
- temporal_uncontained: 0
- failure: null

## I14 — Describe the Shoplifting to Burglary transition in anomaly/Shoplifting/Shoplifting034_x264.mp4 around 166 seconds.

Pattern: sequence | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] window f77 carries the Shoplifting surveillance-event label | baseline: ____ full: ____ notes: ____
- [F02] window f78 carries the Burglary surveillance-event label | baseline: ____ full: ____ notes: ____

### Expected temporal relations
- before: anomaly/Shoplifting/Shoplifting034_x264.mp4:f77 -> anomaly/Shoplifting/Shoplifting034_x264.mp4:f78

### Baseline answer (templated, no LLM reasoning)
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f76 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 162.133-164.133s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f77 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 164.267-166.267s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f78 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 166.4-168.4s

### Full-arm answer
Title: Shoplifting to Burglary model-hypothesis transition around 166s in Shoplifting034
Summary: The retrieved evidence supports a change in surveillance-event model output from Shoplifting hypotheses in 162.133s-166.267s to a Burglary hypothesis in 166.4s-168.4s, consistent with a transition in hypotheses around 166 seconds. All windows share garbage collecting labels and co-occurring person or suitcase detections within the same incident, without establishing that crimes occurred or that detected persons were involved.
- timeline 162.133-164.133: The surveillance-event model produced a Shoplifting hypothesis (confidence 0.9701) with generic-action label garbage collecting (confidence 0.3742) and object detections for 2 persons (max 0.7349) and 1 suitcase (0.4089).
- timeline 164.267-166.267: The surveillance-event model produced a Shoplifting hypothesis (confidence 0.9039) with generic-action label garbage collecting (confidence 0.6237) and object detection for 1 suitcase (0.5861).
- timeline 166.4-168.4: The surveillance-event model produced a Burglary hypothesis (confidence 0.6797) with generic-action label garbage collecting (confidence 0.8296) and object detections for 3 persons (max 0.872).
- finding: The retrieved evidence supports persistent Shoplifting hypotheses across 162.133s-164.133s (confidence 0.9701) and 164.267s-166.267s (confidence 0.9039), with garbage collecting labels in both windows and suitcase detections in both windows plus 2 person detections in the earlier window. The surveillance-event model produced a hypothesis only; the available evidence is consistent with persistence but does not establish that a crime occurred.
- finding: The retrieved evidence supports a surveillance-event model produced Burglary hypothesis (confidence 0.6797) in 166.4s-168.4s, with generic-action label garbage collecting (confidence 0.8296) and 3 person detections (max confidence 0.872). The evidence indicates model output only.
- finding: The available evidence is consistent with a change in model output from Shoplifting hypotheses ending at 166.267s to a Burglary hypothesis starting at 166.4s, within the same incident anomaly/Shoplifting/Shoplifting034_x264.mp4:i0. The evidence indicates temporal sequence and source co-occurrence of object detections with hypotheses, which does not establish involvement, identity, or that crimes occurred.
- finding: The evidence indicates garbage collecting labels across the interval with confidence increasing from 0.3742 to 0.6237 to 0.8296. The retrieved evidence supports label persistence, but model agreement does not confirm the nature of the activity.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f76, anomaly/Shoplifting/Shoplifting034_x264.mp4:f77, mechanical: supported) The evidence indicates model-produced Shoplifting hypotheses (confidence 0.9701 and 0.9039) with generic action labeled garbage collecting and object detections including suitcase in both windows and 2 persons in the earlier window. | grade: ____ notes: ____
- [claim_002] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f78, mechanical: supported) The evidence indicates a model-produced Burglary hypothesis (confidence 0.6797) with generic action labeled garbage collecting (confidence 0.8296) and 3 person detections (max confidence 0.872). | grade: ____ notes: ____
- [claim_003] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f76, anomaly/Shoplifting/Shoplifting034_x264.mp4:f77, mechanical: supported) persistent_event: Compatible Shoplifting hypotheses persist across adjacent windows from 162.133s-164.133s to 164.267s-166.267s with co-occurring suitcase detections and garbage collecting labels. | grade: ____ notes: ____
- [claim_004] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f77, anomaly/Shoplifting/Shoplifting034_x264.mp4:f78, mechanical: supported) temporal_sequence: The Shoplifting hypothesis window ending at 166.267s occurs before the Burglary hypothesis window starting at 166.4s. | grade: ____ notes: ____
- [claim_005] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f76, anomaly/Shoplifting/Shoplifting034_x264.mp4:f77, anomaly/Shoplifting/Shoplifting034_x264.mp4:f78, mechanical: supported) same_incident: All three evidence records belong to the same Phase 2D incident anomaly/Shoplifting/Shoplifting034_x264.mp4:i0. | grade: ____ notes: ____
- [claim_006] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f76, anomaly/Shoplifting/Shoplifting034_x264.mp4:f77, anomaly/Shoplifting/Shoplifting034_x264.mp4:f78, mechanical: supported) cross_source_support: Object detections for person and suitcase co-occur in the same windows as surveillance-event hypotheses and generic-action labels, indicating source co-occurrence only and not confirmation of involvement. | grade: ____ notes: ____
- [claim_007] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f76, anomaly/Shoplifting/Shoplifting034_x264.mp4:f77, anomaly/Shoplifting/Shoplifting034_x264.mp4:f78, mechanical: supported) The available evidence suggests a change in model output from Shoplifting hypotheses before 166.267s to a Burglary hypothesis starting at 166.4s, consistent with a transition in hypotheses around 166 seconds, without establishing that crimes occurred or that detected persons were involved. | grade: ____ notes: ____
- [claim_008] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f76, anomaly/Shoplifting/Shoplifting034_x264.mp4:f77, anomaly/Shoplifting/Shoplifting034_x264.mp4:f78, mechanical: supported) The evidence is consistent with persistent activity labeled as garbage collecting across the interval with confidence increasing from 0.3742 to 0.8296, but model agreement does not confirm the nature of the activity. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 8, "unsupported": 0}
- citation: {"cited": 8, "total": 8}
- temporal_uncontained: 0
- failure: null

## I15 — Describe the Vandalism to Assault transition in anomaly/Assault/Assault010_x264.mp4 around 60 to 76 seconds.

Pattern: sequence | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] window f29 carries the Vandalism surveillance-event label | baseline: ____ full: ____ notes: ____
- [F02] window f35 carries the Assault surveillance-event label | baseline: ____ full: ____ notes: ____

### Expected temporal relations
- before: anomaly/Assault/Assault010_x264.mp4:f29 -> anomaly/Assault/Assault010_x264.mp4:f35

### Baseline answer (templated, no LLM reasoning)
- anomaly/Assault/Assault010_x264.mp4:f28 | anomaly/Assault/Assault010_x264.mp4 | 59.733-61.733s
- anomaly/Assault/Assault010_x264.mp4:f29 | anomaly/Assault/Assault010_x264.mp4 | 61.867-63.867s
- anomaly/Assault/Assault010_x264.mp4:f30 | anomaly/Assault/Assault010_x264.mp4 | 64.0-66.0s
- anomaly/Assault/Assault010_x264.mp4:f31 | anomaly/Assault/Assault010_x264.mp4 | 66.133-68.133s
- anomaly/Assault/Assault010_x264.mp4:f32 | anomaly/Assault/Assault010_x264.mp4 | 68.267-70.267s
- anomaly/Assault/Assault010_x264.mp4:f33 | anomaly/Assault/Assault010_x264.mp4 | 70.4-72.4s
- anomaly/Assault/Assault010_x264.mp4:f34 | anomaly/Assault/Assault010_x264.mp4 | 72.533-74.533s
- anomaly/Assault/Assault010_x264.mp4:f35 | anomaly/Assault/Assault010_x264.mp4 | 74.667-76.667s

### Full-arm answer
Title: Vandalism to Assault Transition in Assault010_x264.mp4 Around 60-76s - Hypothesis Sequence Review
Summary: Around 59.7s-76.7s the surveillance-event model produced an Assault hypothesis, then five adjacent Vandalism hypotheses, then RoadAccidents and Assault hypotheses. Generic actions and intermittent person/suitcase detections overlapped hypotheses. The evidence supports the hypothesis sequence only and is insufficient to confirm that vandalism or assault occurred.
- timeline 59.733-61.733: The surveillance-event model produced an Assault hypothesis with confidence 0.4572, with generic action sweeping floor and overlapping person (2) and suitcase (2) detections.
- timeline 61.867-72.4: The surveillance-event model produced persistent Vandalism hypotheses (0.4952, 0.5445, 0.4054, 0.3645, 0.5753) with generic action bookbinding throughout; person in earliest window and suitcase in 61.867s-63.867s, 64.0s-66.0s and 68.267s-70.267s windows.
- timeline 72.533-74.533: The surveillance-event model produced a RoadAccidents hypothesis with confidence 0.426 and generic action bookbinding, with no object detections reported.
- timeline 74.667-76.667: The surveillance-event model produced an Assault hypothesis with confidence 0.376 and generic action unloading truck, with no object detections reported.
- finding: The retrieved evidence supports an initial Assault hypothesis window at 59.733s-61.733s: the surveillance-event model produced an Assault hypothesis with confidence 0.4572, with generic action sweeping floor and overlapping person (count 2) and suitcase (count 2) detections.
- finding: The retrieved evidence supports persistent Vandalism hypotheses across 61.867s-72.4s with confidences 0.4952, 0.5445, 0.4054, 0.3645 and 0.5753 and generic action bookbinding throughout. Person detection occurred in the 61.867s-63.867s window, and suitcase detections occurred in 61.867s-63.867s, 64.0s-66.0s and 68.267s-70.267s windows, with no object detections in the 66.133s-68.133s and 70.4s-72.4s windows.
- finding: The retrieved evidence supports a subsequent RoadAccidents hypothesis at 72.533s-74.533s with confidence 0.426 and generic action bookbinding and no object detections, followed by an Assault hypothesis at 74.667s-76.667s with confidence 0.376 and generic action unloading truck and no object detections.
- finding: The available evidence is consistent with a hypothesis sequence from Assault to persistent Vandalism to RoadAccidents to Assault around 59.7s-76.7s. The surveillance-event model produced hypotheses only, and the evidence does not establish that vandalism or assault occurred. All windows belong to the same incident anomaly/Assault/Assault010_x264.mp4:i0.
- finding: The evidence indicates person detections temporally overlapped early Assault and Vandalism hypotheses, and object detections temporally overlapped surveillance-event hypotheses and generic-action labels within the same windows. This represents source agreement only and does not mean detected persons were involved in the hypothesized events.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Assault/Assault010_x264.mp4:f28, mechanical: supported) The evidence indicates the model produced an Assault hypothesis with confidence 0.4572, with 2 person detections, 2 suitcase detections, and generic action sweeping floor. | grade: ____ notes: ____
- [claim_002] (anomaly/Assault/Assault010_x264.mp4:f29, anomaly/Assault/Assault010_x264.mp4:f30, anomaly/Assault/Assault010_x264.mp4:f31, anomaly/Assault/Assault010_x264.mp4:f32, anomaly/Assault/Assault010_x264.mp4:f33, mechanical: partially_supported) The evidence indicates the model produced persistent Vandalism hypotheses with confidences 0.4952, 0.5445, 0.4054, 0.3645, and 0.5753, with generic action bookbinding throughout and person and suitcase detections only in the earlier part of the segment. | grade: ____ notes: ____
- [claim_003] (anomaly/Assault/Assault010_x264.mp4:f34, mechanical: supported) The evidence indicates the model produced a RoadAccidents hypothesis with confidence 0.426 and generic action bookbinding, with no object detections reported. | grade: ____ notes: ____
- [claim_004] (anomaly/Assault/Assault010_x264.mp4:f35, mechanical: supported) The evidence indicates the model produced an Assault hypothesis with confidence 0.376 and generic action unloading truck, with no object detections reported. | grade: ____ notes: ____
- [claim_005] (anomaly/Assault/Assault010_x264.mp4:f29, anomaly/Assault/Assault010_x264.mp4:f30, anomaly/Assault/Assault010_x264.mp4:f31, anomaly/Assault/Assault010_x264.mp4:f32, anomaly/Assault/Assault010_x264.mp4:f33, mechanical: supported) persistent_event: The evidence indicates compatible Vandalism hypotheses persist across adjacent windows from 61.867s to 72.4s. | grade: ____ notes: ____
- [claim_006] (anomaly/Assault/Assault010_x264.mp4:f28, anomaly/Assault/Assault010_x264.mp4:f29, anomaly/Assault/Assault010_x264.mp4:f33, anomaly/Assault/Assault010_x264.mp4:f34, anomaly/Assault/Assault010_x264.mp4:f35, mechanical: supported) temporal_sequence: The evidence indicates an Assault hypothesis window precedes the persistent Vandalism segment, which precedes RoadAccidents and later Assault hypothesis windows in the same video. | grade: ____ notes: ____
- [claim_007] (anomaly/Assault/Assault010_x264.mp4:f28, anomaly/Assault/Assault010_x264.mp4:f29, anomaly/Assault/Assault010_x264.mp4:f30, anomaly/Assault/Assault010_x264.mp4:f31, anomaly/Assault/Assault010_x264.mp4:f32, anomaly/Assault/Assault010_x264.mp4:f33, anomaly/Assault/Assault010_x264.mp4:f34, anomaly/Assault/Assault010_x264.mp4:f35, mechanical: supported) same_incident: The evidence records belong to the same Phase 2D incident anomaly/Assault/Assault010_x264.mp4:i0. | grade: ____ notes: ____
- [claim_008] (anomaly/Assault/Assault010_x264.mp4:f28, anomaly/Assault/Assault010_x264.mp4:f29, anomaly/Assault/Assault010_x264.mp4:f30, anomaly/Assault/Assault010_x264.mp4:f32, mechanical: supported) cross_source_support: The evidence indicates object detections temporally overlap surveillance-event hypotheses and generic-action labels within the same windows, representing source agreement only and not confirmation. | grade: ____ notes: ____
- [claim_009] (anomaly/Assault/Assault010_x264.mp4:f28, anomaly/Assault/Assault010_x264.mp4:f29, anomaly/Assault/Assault010_x264.mp4:f30, anomaly/Assault/Assault010_x264.mp4:f31, anomaly/Assault/Assault010_x264.mp4:f32, anomaly/Assault/Assault010_x264.mp4:f33, anomaly/Assault/Assault010_x264.mp4:f34, anomaly/Assault/Assault010_x264.mp4:f35, mechanical: supported) The available evidence suggests a hypothesis sequence around 60-76s from Assault to persistent Vandalism to RoadAccidents to Assault, but the model produced hypotheses only and the evidence is insufficient to confirm that vandalism or assault occurred. | grade: ____ notes: ____
- [claim_010] (anomaly/Assault/Assault010_x264.mp4:f28, anomaly/Assault/Assault010_x264.mp4:f29, mechanical: supported) The evidence indicates person detections temporally overlapped early Assault and Vandalism hypotheses, which does not mean the detected persons were involved in the hypothesized events. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 1, "supported": 9, "unsupported": 0}
- citation: {"cited": 10, "total": 10}
- temporal_uncontained: 0
- failure: null

## I16 — Show evidence around 100 seconds in anomaly/Burglary/Burglary032_x264.mp4.

Pattern: contextual | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] 10 evidence windows overlap the 90s to 110s interval | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)
- anomaly/Burglary/Burglary032_x264.mp4:f42 | anomaly/Burglary/Burglary032_x264.mp4 | 89.6-91.6s
- anomaly/Burglary/Burglary032_x264.mp4:f43 | anomaly/Burglary/Burglary032_x264.mp4 | 91.733-93.733s
- anomaly/Burglary/Burglary032_x264.mp4:f44 | anomaly/Burglary/Burglary032_x264.mp4 | 93.867-95.867s
- anomaly/Burglary/Burglary032_x264.mp4:f45 | anomaly/Burglary/Burglary032_x264.mp4 | 96.0-98.0s
- anomaly/Burglary/Burglary032_x264.mp4:f46 | anomaly/Burglary/Burglary032_x264.mp4 | 98.133-100.133s
- anomaly/Burglary/Burglary032_x264.mp4:f47 | anomaly/Burglary/Burglary032_x264.mp4 | 100.267-102.267s
- anomaly/Burglary/Burglary032_x264.mp4:f48 | anomaly/Burglary/Burglary032_x264.mp4 | 102.4-104.4s
- anomaly/Burglary/Burglary032_x264.mp4:f49 | anomaly/Burglary/Burglary032_x264.mp4 | 104.533-106.533s
- anomaly/Burglary/Burglary032_x264.mp4:f50 | anomaly/Burglary/Burglary032_x264.mp4 | 106.667-108.667s
- anomaly/Burglary/Burglary032_x264.mp4:f51 | anomaly/Burglary/Burglary032_x264.mp4 | 108.8-110.8s

### Full-arm answer
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: null

## I17 — Show evidence between 400 and 440 seconds in anomaly/Explosion/Explosion007_x264.mp4.

Pattern: contextual | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] 20 evidence windows overlap the 400s to 440s interval | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)

### Full-arm answer
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: null

## I18 — Show evidence between 200 and 220 seconds in anomaly/Assault/Assault010_x264.mp4.

Pattern: contextual | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] 11 evidence windows overlap the 200s to 220s interval | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)

### Full-arm answer
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: null

## I19 — Show person detections with RoadAccidents evidence in anomaly/RoadAccidents/RoadAccidents001_x264.mp4.

Pattern: multi-source | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] a single window f6 carries both a person detection and the RoadAccidents label | baseline: ____ full: ____ notes: ____
- [F02] window f6 spans 12.8s to 14.8s | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)
- anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3 | anomaly/RoadAccidents/RoadAccidents001_x264.mp4 | 6.4-8.4s
- anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f4 | anomaly/RoadAccidents/RoadAccidents001_x264.mp4 | 8.533-10.533s
- anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6 | anomaly/RoadAccidents/RoadAccidents001_x264.mp4 | 12.8-14.8s
- anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f7 | anomaly/RoadAccidents/RoadAccidents001_x264.mp4 | 14.933-16.933s
- anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f8 | anomaly/RoadAccidents/RoadAccidents001_x264.mp4 | 17.067-19.067s
- anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f9 | anomaly/RoadAccidents/RoadAccidents001_x264.mp4 | 19.2-21.2s
- anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f10 | anomaly/RoadAccidents/RoadAccidents001_x264.mp4 | 21.333-23.333s
- anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f12 | anomaly/RoadAccidents/RoadAccidents001_x264.mp4 | 25.6-27.6s
- anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f14 | anomaly/RoadAccidents/RoadAccidents001_x264.mp4 | 29.866-31.866s
- anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f15 | anomaly/RoadAccidents/RoadAccidents001_x264.mp4 | 32.0-34.0s

### Full-arm answer
Title: Person Detections with RoadAccidents Hypotheses in RoadAccidents001_x264.mp4
Summary: Person detection with RoadAccidents evidence was found only in 12.8-14.8s in anomaly/RoadAccidents/RoadAccidents001_x264.mp4. The retrieved evidence supports RoadAccidents hypotheses with overlapping driving car/motorcycling hypotheses across 6.4-34.0s, but the evidence is insufficient to confirm that a road accident occurred and does not establish involvement of the detected person.
- timeline 6.4-10.533: The surveillance-event model produced RoadAccidents hypotheses overlapping driving car hypotheses in 6.4-8.4s and 8.533-10.533s, with no object detections reported.
- timeline 12.8-14.8: The surveillance-event model produced a RoadAccidents hypothesis overlapping a driving car hypothesis in 12.8-14.8s, with person count 1 and backpack count 1 reported.
- timeline 14.933-21.2: The surveillance-event model produced RoadAccidents hypotheses overlapping driving car hypotheses in 14.933-16.933s, 17.067-19.067s and 19.2-21.2s, with no object detections reported. Window 8.533-10.533 occurs before 12.8-14.8s.
- timeline 21.333-23.333: The surveillance-event model produced a RoadAccidents hypothesis overlapping a motorcycling hypothesis in 21.333-23.333s, with no object detections reported.
- timeline 25.6-34.0: The surveillance-event model produced RoadAccidents hypotheses overlapping driving car hypotheses in 25.6-27.6s, 29.866-31.866s and 32.0-34.0s, with no object detections reported.
- finding: The retrieved evidence supports compatible RoadAccidents hypotheses with overlapping vehicle-related hypotheses (driving car in nine windows, motorcycling in one window) across 6.4-34.0s. The surveillance-event model produced a RoadAccidents hypothesis in each cited window. The available evidence is consistent with the RoadAccidents label but does not establish that a road accident occurred.
- finding: The evidence indicates all ten cited windows belong to the same incident anomaly/RoadAccidents/RoadAccidents001_x264.mp4:i0, with compatible RoadAccidents hypotheses persisting across adjacent windows 6.4-10.533s and 12.8-23.333s and across nearby windows 25.6-34.0s.
- finding: The evidence indicates a person detection (count 1) and backpack detection (count 1) were reported only in 12.8-14.8s overlapping a RoadAccidents hypothesis and driving car hypothesis. Other cited windows report no object detections. Temporal overlap does not indicate the detected person was involved, and the evidence does not establish role or causation.
- finding: The retrieved evidence supports temporal co-occurrence only in 12.8-14.8s between person/backpack object detections and RoadAccidents and driving car hypotheses from different source types.

### Full-arm claims (grade each)
- [claim_001] (anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f4, mechanical: supported) The evidence indicates the models produced RoadAccidents hypotheses overlapping with driving car hypotheses in 6.4-10.533s, with no person or other object detections reported. | grade: ____ notes: ____
- [claim_002] (anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f7, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f10, mechanical: supported) The evidence indicates persistent RoadAccidents hypotheses overlapping driving car and one motorcycling hypothesis in 12.8-23.333s; a person detection (count 1) and backpack detection (count 1) were reported only in the 12.8-14.8s portion. | grade: ____ notes: ____
- [claim_003] (anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f12, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f14, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f15, mechanical: supported) The evidence indicates persistent RoadAccidents hypotheses overlapping driving car hypotheses in 25.6-34.0s, with no person or other object detections reported. | grade: ____ notes: ____
- [claim_004] (anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f7, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f10, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f12, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f14, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f15, mechanical: supported) same_incident: All ten windows belong to the same Phase 2D incident anomaly/RoadAccidents/RoadAccidents001_x264.mp4:i0. | grade: ____ notes: ____
- [claim_005] (anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f4, mechanical: supported) persistent_event: Compatible RoadAccidents model hypotheses persist across adjacent windows 6.4-10.533. | grade: ____ notes: ____
- [claim_006] (anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f7, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f10, mechanical: supported) persistent_event: Compatible RoadAccidents model hypotheses persist across adjacent windows 12.8-23.333 with overlapping driving car and motorcycling hypotheses. | grade: ____ notes: ____
- [claim_007] (anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f12, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f14, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f15, mechanical: supported) persistent_event: Compatible RoadAccidents model hypotheses persist across nearby windows 25.6-34.0 with overlapping driving car hypotheses. | grade: ____ notes: ____
- [claim_008] (anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6, mechanical: supported) cross_source_support: In 12.8-14.8, person and backpack object detections overlap in time with RoadAccidents and driving car hypotheses from different source types, indicating temporal co-occurrence only. | grade: ____ notes: ____
- [claim_009] (anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6, mechanical: supported) temporal_sequence: Window 8.533-10.533 occurs before window 12.8-14.8. | grade: ____ notes: ____
- [claim_010] (anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f3, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f4, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f7, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f8, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f9, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f10, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f12, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f14, anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f15, mechanical: supported) The available evidence suggests persistent vehicle-related model hypotheses consistent with the RoadAccidents label across 6.4-34.0s, but the evidence is insufficient to confirm that a road accident occurred. | grade: ____ notes: ____
- [claim_011] (anomaly/RoadAccidents/RoadAccidents001_x264.mp4:f6, mechanical: supported) The available evidence suggests a person detection occurred only in 12.8-14.8s overlapping a RoadAccidents hypothesis; temporal overlap does not indicate the detected person was involved. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 11, "unsupported": 0}
- citation: {"cited": 11, "total": 11}
- temporal_uncontained: 0
- failure: null

## I20 — Show person detections with Burglary evidence in anomaly/Burglary/Burglary032_x264.mp4 between 27 and 49 seconds.

Pattern: multi-source | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] 9 evidence windows carry both a person detection and the Burglary label | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)
- anomaly/Burglary/Burglary032_x264.mp4:f13 | anomaly/Burglary/Burglary032_x264.mp4 | 27.733-29.733s
- anomaly/Burglary/Burglary032_x264.mp4:f14 | anomaly/Burglary/Burglary032_x264.mp4 | 29.867-31.867s
- anomaly/Burglary/Burglary032_x264.mp4:f15 | anomaly/Burglary/Burglary032_x264.mp4 | 32.0-34.0s
- anomaly/Burglary/Burglary032_x264.mp4:f16 | anomaly/Burglary/Burglary032_x264.mp4 | 34.133-36.133s
- anomaly/Burglary/Burglary032_x264.mp4:f17 | anomaly/Burglary/Burglary032_x264.mp4 | 36.267-38.267s
- anomaly/Burglary/Burglary032_x264.mp4:f18 | anomaly/Burglary/Burglary032_x264.mp4 | 38.4-40.4s
- anomaly/Burglary/Burglary032_x264.mp4:f19 | anomaly/Burglary/Burglary032_x264.mp4 | 40.533-42.533s
- anomaly/Burglary/Burglary032_x264.mp4:f20 | anomaly/Burglary/Burglary032_x264.mp4 | 42.667-44.667s
- anomaly/Burglary/Burglary032_x264.mp4:f21 | anomaly/Burglary/Burglary032_x264.mp4 | 44.8-46.8s
- anomaly/Burglary/Burglary032_x264.mp4:f22 | anomaly/Burglary/Burglary032_x264.mp4 | 46.933-48.933s

### Full-arm answer
Title: Person detections with Burglary-model hypotheses in Burglary032_x264.mp4 27-49s
Summary: The retrieved evidence supports persistent surveillance-event Burglary hypotheses from 27.733s to 48.933s with frequent person-detection overlap in 9 of 10 windows and one gap without person detection. The available evidence is consistent with co-occurrence only and does not establish involvement.
- timeline 27.733-29.733: The surveillance-event model produced a Burglary hypothesis with object-model detection of 1 person; generic-action label pumping gas at moderate confidence.
- timeline 29.867-31.867: The surveillance-event model produced a Burglary hypothesis with no object-model person detection; generic-action label pumping gas.
- timeline 32.0-34.0: The surveillance-event model produced a Burglary hypothesis with object-model detection of 1 person; generic-action label pumping gas.
- timeline 34.133-36.133: The surveillance-event model produced a Burglary hypothesis with object-model detection of 2 persons; generic-action label pumping gas at low confidence.
- timeline 36.267-38.267: The surveillance-event model produced a Burglary hypothesis with object-model detection of 2 persons; generic-action label dancing macarena at low confidence.
- timeline 38.4-40.4: The surveillance-event model produced a Burglary hypothesis with object-model detection of 3 persons; generic-action label high kick at low confidence.
- timeline 40.533-42.533: The surveillance-event model produced a Burglary hypothesis with object-model detection of 2 persons; generic-action label pumping gas at low confidence.
- timeline 42.667-44.667: The surveillance-event model produced a Burglary hypothesis with object-model detection of 2 persons; generic-action label digging at low confidence.
- timeline 44.8-46.8: The surveillance-event model produced a Burglary hypothesis with object-model detection of 2 persons; generic-action label pumping gas at low confidence.
- timeline 46.933-48.933: The surveillance-event model produced a Burglary hypothesis with object-model detection of 1 person; generic-action label pumping gas at low confidence.
- finding: The retrieved evidence supports persistent surveillance-event Burglary hypotheses across 27.733s to 48.933s. The surveillance-event model produced a Burglary hypothesis in all 10 windows with confidence 0.9976-0.9992.
- finding: The retrieved evidence supports object-model person detections temporally overlapping Burglary hypotheses in 9 windows, with counts of 1 to 3. This is source agreement only and the available evidence is consistent with co-occurrence only and does not establish that any detected person was involved.
- finding: The retrieved evidence supports a Burglary hypothesis during 29.867s to 31.867s without a person detection, indicating person presence was not continuous across the segment.
- finding: The evidence indicates all listed windows belong to the same incident anomaly/Burglary/Burglary032_x264.mp4:i0, supporting persistence assessment. Generic-action labels varied at low to moderate confidence and do not explain the Burglary hypotheses.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f14, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f22, mechanical: supported) The evidence indicates the surveillance-event model produced Burglary hypotheses across 27.733s to 48.933s, with object-model person detections overlapping in 9 windows with counts of 1 to 3 and one window with no person detection; generic-action labels varied at low to moderate confidence. | grade: ____ notes: ____
- [claim_002] (anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f14, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f22, mechanical: supported) persistent_event: The evidence indicates compatible Burglary-model hypotheses persisted across adjacent windows from 27.733s to 48.933s. | grade: ____ notes: ____
- [claim_003] (anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f14, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f22, mechanical: supported) same_incident: The evidence indicates all listed windows belong to the same Phase 2D incident anomaly/Burglary/Burglary032_x264.mp4:i0. | grade: ____ notes: ____
- [claim_004] (anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f22, mechanical: supported) cross_source_support: The evidence indicates object-source person detections temporally overlapped surveillance-event Burglary hypotheses in the same windows; this is source agreement only and does not confirm involvement. | grade: ____ notes: ____
- [claim_005] (anomaly/Burglary/Burglary032_x264.mp4:f13, anomaly/Burglary/Burglary032_x264.mp4:f14, anomaly/Burglary/Burglary032_x264.mp4:f15, anomaly/Burglary/Burglary032_x264.mp4:f16, anomaly/Burglary/Burglary032_x264.mp4:f17, anomaly/Burglary/Burglary032_x264.mp4:f18, anomaly/Burglary/Burglary032_x264.mp4:f19, anomaly/Burglary/Burglary032_x264.mp4:f20, anomaly/Burglary/Burglary032_x264.mp4:f21, anomaly/Burglary/Burglary032_x264.mp4:f22, mechanical: supported) The available evidence suggests persistent Burglary-model activity from 27.733s to 48.933s with frequent person-detection overlap, but the evidence is consistent with co-occurrence only and does not establish that any detected person was involved. | grade: ____ notes: ____
- [claim_006] (anomaly/Burglary/Burglary032_x264.mp4:f14, mechanical: supported) The evidence indicates the model produced a Burglary hypothesis during 29.867s to 31.867s without a person detection, suggesting person presence was not continuous across the segment. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 6, "unsupported": 0}
- citation: {"cited": 6, "total": 6}
- temporal_uncontained: 0
- failure: null

## I21 — Show suitcase detections with Shoplifting evidence in anomaly/Shoplifting/Shoplifting034_x264.mp4 between 36 and 60 seconds.

Pattern: multi-source | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] 4 evidence windows carry both a suitcase detection and the Shoplifting label | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f16 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 34.133-36.133s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f17 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 36.267-38.267s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f18 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 38.4-40.4s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f19 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 40.533-42.533s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f22 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 46.933-48.933s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f23 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 49.067-51.067s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f24 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 51.2-53.2s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f26 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 55.467-57.467s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f27 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 57.6-59.6s
- anomaly/Shoplifting/Shoplifting034_x264.mp4:f28 | anomaly/Shoplifting/Shoplifting034_x264.mp4 | 59.733-61.733s

### Full-arm answer
Title: Suitcase with Shoplifting hypotheses 36-60s - Shoplifting034
Summary: In anomaly/Shoplifting/Shoplifting034_x264.mp4 between 36 and 60s, the retrieved evidence supports four windows with suitcase detections overlapping Shoplifting model hypotheses at 36.267-38.267s, 49.067-51.067s, 51.2-53.2s and 55.467-57.467s. Other supplied windows show either suitcase with Burglary hypotheses or Shoplifting without suitcase. All event labels remain hypotheses.
- timeline 34.133-36.133: The retrieved evidence supports a person detection with garbage collecting and Shoplifting hypotheses, without suitcase detection. This window starts before the requested 36s boundary.
- timeline 36.267-38.267: The retrieved evidence supports suitcase and person detections with garbage collecting and Shoplifting hypotheses. The surveillance-event model produced a Shoplifting hypothesis at low confidence.
- timeline 38.4-42.533: The retrieved evidence supports person and suitcase detections with garbage collecting and Burglary hypotheses. The evidence does not establish Shoplifting in this interval.
- timeline 46.933-48.933: The retrieved evidence supports a suitcase detection with garbage collecting and Burglary hypotheses, with no person detection reported.
- timeline 49.067-53.2: The retrieved evidence supports suitcase detections with garbage collecting and Shoplifting hypotheses persisting across adjacent windows, with person detection in the first window (49.067s-51.067s).
- timeline 55.467-57.467: The retrieved evidence supports suitcase and 4-person detections with garbage collecting and Shoplifting hypotheses.
- timeline 57.6-61.733: The retrieved evidence supports 4-person detections with garbage collecting and Shoplifting hypotheses without suitcase detection. This sequence extends beyond the requested 60s boundary to 61.733s.
- finding: The retrieved evidence supports suitcase detections temporally overlapping Shoplifting hypotheses in four windows: 36.267s-38.267s, 49.067s-51.067s, 51.2s-53.2s, and 55.467s-57.467s. The surveillance-event model produced a Shoplifting hypothesis in each, with co-occurring garbage collecting hypotheses. This is source agreement only and does not confirm an event or involvement.
- finding: The available evidence indicates other supplied windows do not meet both criteria: f16, f27 and f28 show Shoplifting hypotheses without suitcase detection; f18, f19 and f22 show suitcase detections with Burglary hypotheses rather than Shoplifting.
- finding: The retrieved evidence supports persistence of compatible hypotheses across adjacent windows: Shoplifting with suitcase and garbage collecting from 49.067s to 53.2s, and Shoplifting with person detections from 55.467s to 61.733s with suitcase only in the first window of that sequence.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f16, anomaly/Shoplifting/Shoplifting034_x264.mp4:f17, anomaly/Shoplifting/Shoplifting034_x264.mp4:f18, anomaly/Shoplifting/Shoplifting034_x264.mp4:f19, mechanical: supported) The evidence indicates person detections with garbage collecting hypotheses persisting from 34.133s to 42.533s. The models produced Shoplifting hypotheses in the first two windows and Burglary hypotheses in the later two, with suitcase detections in the windows starting at 36.267s, 38.4s and 40.533s. | grade: ____ notes: ____
- [claim_002] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f22, mechanical: supported) The evidence indicates a suitcase detection with garbage collecting and Burglary model hypotheses from 46.933s to 48.933s, with no person detection reported. | grade: ____ notes: ____
- [claim_003] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f23, anomaly/Shoplifting/Shoplifting034_x264.mp4:f24, mechanical: supported) The evidence indicates suitcase detections with Shoplifting and garbage collecting model hypotheses persisting from 49.067s to 53.2s, with person detection in the first window. | grade: ____ notes: ____
- [claim_004] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f26, anomaly/Shoplifting/Shoplifting034_x264.mp4:f27, anomaly/Shoplifting/Shoplifting034_x264.mp4:f28, mechanical: supported) The evidence indicates Shoplifting and garbage collecting hypotheses with 4-person detections persisting from 55.467s to 61.733s, with suitcase detection only in the window starting at 55.467s. | grade: ____ notes: ____
- [claim_005] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f17, anomaly/Shoplifting/Shoplifting034_x264.mp4:f23, anomaly/Shoplifting/Shoplifting034_x264.mp4:f24, anomaly/Shoplifting/Shoplifting034_x264.mp4:f26, mechanical: supported) cross_source_support: The available evidence suggests suitcase object detections temporally overlap Shoplifting model hypotheses in these windows between ~36s and ~57s; this is source agreement only and does not confirm an event or involvement. | grade: ____ notes: ____
- [claim_006] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f23, anomaly/Shoplifting/Shoplifting034_x264.mp4:f24, mechanical: supported) persistent_event: Compatible Shoplifting hypotheses with suitcase detections and garbage collecting hypotheses persist across adjacent windows from 49.067s to 53.2s. | grade: ____ notes: ____
- [claim_007] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f26, anomaly/Shoplifting/Shoplifting034_x264.mp4:f27, anomaly/Shoplifting/Shoplifting034_x264.mp4:f28, mechanical: supported) persistent_event: Compatible Shoplifting hypotheses with person detections persist across adjacent windows from 55.467s to 61.733s, with suitcase detection only in the first window. | grade: ____ notes: ____
- [claim_008] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f17, anomaly/Shoplifting/Shoplifting034_x264.mp4:f23, anomaly/Shoplifting/Shoplifting034_x264.mp4:f24, anomaly/Shoplifting/Shoplifting034_x264.mp4:f26, mechanical: supported) temporal_sequence: The window at 36.267s-38.267s occurs before the windows at 49.067s-53.2s and 55.467s-57.467s in the same video. | grade: ____ notes: ____
- [claim_009] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f17, anomaly/Shoplifting/Shoplifting034_x264.mp4:f23, anomaly/Shoplifting/Shoplifting034_x264.mp4:f24, anomaly/Shoplifting/Shoplifting034_x264.mp4:f26, mechanical: supported) The available evidence suggests suitcase detections with co-occurring Shoplifting model hypotheses between 36 and 60 seconds are indicated in these four windows. | grade: ____ notes: ____
- [claim_010] (anomaly/Shoplifting/Shoplifting034_x264.mp4:f16, anomaly/Shoplifting/Shoplifting034_x264.mp4:f18, anomaly/Shoplifting/Shoplifting034_x264.mp4:f19, anomaly/Shoplifting/Shoplifting034_x264.mp4:f22, anomaly/Shoplifting/Shoplifting034_x264.mp4:f27, anomaly/Shoplifting/Shoplifting034_x264.mp4:f28, mechanical: supported) The evidence indicates other supplied windows do not meet both criteria: suitcase with Burglary hypothesis, or Shoplifting hypothesis without suitcase detection. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 10, "unsupported": 0}
- citation: {"cited": 10, "total": 10}
- temporal_uncontained: 0
- failure: null

## I22 — Summarize the incident in anomaly/Robbery/Robbery048_x264.mp4.

Pattern: incident | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] 23 evidence windows span 0.0s to 46.9s | baseline: ____ full: ____ notes: ____
- [F02] annotated Robbery interval is 15.0s to 31.0s | baseline: ____ full: ____ notes: ____
- [F03] windows f7 through f14 overlap the annotated interval | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)
- anomaly/Robbery/Robbery048_x264.mp4:f2 | anomaly/Robbery/Robbery048_x264.mp4 | 4.267-6.267s
- anomaly/Robbery/Robbery048_x264.mp4:f6 | anomaly/Robbery/Robbery048_x264.mp4 | 12.8-14.8s
- anomaly/Robbery/Robbery048_x264.mp4:f7 | anomaly/Robbery/Robbery048_x264.mp4 | 14.933-16.933s
- anomaly/Robbery/Robbery048_x264.mp4:f8 | anomaly/Robbery/Robbery048_x264.mp4 | 17.067-19.067s
- anomaly/Robbery/Robbery048_x264.mp4:f9 | anomaly/Robbery/Robbery048_x264.mp4 | 19.2-21.2s
- anomaly/Robbery/Robbery048_x264.mp4:f10 | anomaly/Robbery/Robbery048_x264.mp4 | 21.333-23.333s
- anomaly/Robbery/Robbery048_x264.mp4:f15 | anomaly/Robbery/Robbery048_x264.mp4 | 32.0-34.0s
- anomaly/Robbery/Robbery048_x264.mp4:f16 | anomaly/Robbery/Robbery048_x264.mp4 | 34.134-36.134s
- anomaly/Robbery/Robbery048_x264.mp4:f17 | anomaly/Robbery/Robbery048_x264.mp4 | 36.267-38.267s
- anomaly/Robbery/Robbery048_x264.mp4:f18 | anomaly/Robbery/Robbery048_x264.mp4 | 38.4-40.4s

### Full-arm answer
Title: Summary of retrieved model outputs for anomaly/Robbery/Robbery048_x264.mp4
Summary: The retrieved evidence for anomaly/Robbery/Robbery048_x264.mp4 indicates an early single-person detection, followed by two main periods of persistent person presence from 12.8-23.333s and 32.0-40.4s, with alternating RoadAccidents and Shooting model hypotheses at modest confidence and very low-confidence generic-action hypotheses. The available evidence is consistent with continued presence and unstable model hypotheses, and does not establish a crime, involvement, or identity.
- timeline 4.267-6.267: The retrieved evidence supports 1 person detection (max 0.6548) co-occurring with a sweeping floor hypothesis (0.0669) and a Shooting hypothesis (0.3359). The surveillance-event model produced a Shooting hypothesis; the evidence does not confirm a crime or involvement.
- timeline 12.8-23.333: The retrieved evidence supports persistent person detections (2, 3, 1, 1, 1 persons, max 0.6819-0.8628) with suitcase and toilet objects in later windows. The model produced cleaning floor and eating chips hypotheses (0.0356-0.1873) and alternating RoadAccidents (0.3065-0.4406) and Shooting (0.3823-0.4221) hypotheses. The evidence is consistent with continued presence only.
- timeline 32.0-40.4: The retrieved evidence supports persistent person detections (9, 5, 4, 3 persons, max 0.9007-0.9194) with slapping, cleaning floor, tai chi and counting money hypotheses (0.0305-0.1049) and RoadAccidents (0.2554-0.4295) and Shooting (0.4559) hypotheses. The evidence is consistent with continued presence only.
- finding: The retrieved evidence supports persistent person detections from 12.8s to 23.333s (2, 3, 1, 1, 1 persons, max 0.6819-0.8628), with suitcase and toilet objects in later windows. The evidence is consistent with continued presence; the evidence does not establish involvement or a crime.
- finding: The retrieved evidence supports persistent person detections from 32.0s to 40.4s (9, 5, 4, 3 persons, max 0.9007-0.9194). The evidence is consistent with continued presence; the evidence does not establish involvement or a crime.
- finding: The surveillance-event model produced alternating RoadAccidents (0.2554-0.4406) and Shooting (0.3359-0.4559) hypotheses at modest confidences. The available evidence is consistent with unstable model hypotheses rather than confirmation of any crime.
- finding: The model produced generic-action hypotheses varying across windows (sweeping floor, cleaning floor, eating chips, slapping, tai chi, counting money) at very low to low confidence (0.0305-0.1873), which limits reliable interpretation of activities.
- finding: The retrieved evidence supports that all cited records are assigned to the same Phase 2D incident anomaly/Robbery/Robbery048_x264.mp4:i0, with object-source person detections temporally co-occurring with different-source surveillance-event hypotheses in the same windows. This is source co-occurrence only and does not confirm involvement or a crime.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Robbery/Robbery048_x264.mp4:f2, mechanical: supported) The evidence indicates 1 person detection (max confidence 0.6548) co-occurring with a low-confidence generic-action hypothesis of sweeping floor (0.0669) and a surveillance-event hypothesis of Shooting (0.3359). The evidence is consistent with model outputs only and does not confirm any crime or involvement of the detected person. | grade: ____ notes: ____
- [claim_002] (anomaly/Robbery/Robbery048_x264.mp4:f6, anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f9, anomaly/Robbery/Robbery048_x264.mp4:f10, mechanical: supported) The evidence indicates persistent person detections across adjacent windows (2, 3, 1, 1, 1 persons, max confidences 0.6819-0.8628) with suitcase and toilet objects in later windows. The model produced generic-action hypotheses of cleaning floor and eating chips at very low to low confidence (0.0356-0.1873) and alternating surveillance-event hypotheses of RoadAccidents (0.3065-0.4406) and Shooting (0.3823-0.4221). The evidence is consistent with continued presence but does not confirm any crime or link detections to hypotheses. | grade: ____ notes: ____
- [claim_003] (anomaly/Robbery/Robbery048_x264.mp4:f15, anomaly/Robbery/Robbery048_x264.mp4:f16, anomaly/Robbery/Robbery048_x264.mp4:f17, anomaly/Robbery/Robbery048_x264.mp4:f18, mechanical: supported) The evidence indicates persistent person detections across adjacent windows (9, 5, 4, 3 persons, max confidences 0.9007-0.9194). The model produced generic-action hypotheses of slapping, cleaning floor, tai chi and counting money at very low confidence (0.0305-0.1049) and surveillance-event hypotheses of RoadAccidents (0.2554-0.4295) and Shooting (0.4559). The evidence is consistent with continued presence but does not confirm any crime or involvement of detected persons. | grade: ____ notes: ____
- [claim_004] (anomaly/Robbery/Robbery048_x264.mp4:f2, anomaly/Robbery/Robbery048_x264.mp4:f6, anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f9, anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f15, anomaly/Robbery/Robbery048_x264.mp4:f16, anomaly/Robbery/Robbery048_x264.mp4:f17, anomaly/Robbery/Robbery048_x264.mp4:f18, mechanical: supported) same_incident: The evidence indicates all cited records are assigned to the same Phase 2D incident anomaly/Robbery/Robbery048_x264.mp4:i0 in the same video. | grade: ____ notes: ____
- [claim_005] (anomaly/Robbery/Robbery048_x264.mp4:f6, anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f9, anomaly/Robbery/Robbery048_x264.mp4:f10, mechanical: supported) persistent_event: The evidence indicates person detections persist across adjacent windows from 12.8s to 23.333s with recurring surveillance-event hypotheses, consistent with continued presence rather than isolated detections. | grade: ____ notes: ____
- [claim_006] (anomaly/Robbery/Robbery048_x264.mp4:f15, anomaly/Robbery/Robbery048_x264.mp4:f16, anomaly/Robbery/Robbery048_x264.mp4:f17, anomaly/Robbery/Robbery048_x264.mp4:f18, mechanical: supported) persistent_event: The evidence indicates person detections persist across adjacent windows from 32.0s to 40.4s with recurring RoadAccidents hypotheses and one Shooting hypothesis, consistent with continued presence. | grade: ____ notes: ____
- [claim_007] (anomaly/Robbery/Robbery048_x264.mp4:f2, anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f15, mechanical: supported) temporal_sequence: The available evidence suggests the f2 interval (4.267-6.267s) occurs before the mid-interval ending with f10 (21.333-23.333s), which occurs before the late-interval starting with f15 (32.0-34.0s). | grade: ____ notes: ____
- [claim_008] (anomaly/Robbery/Robbery048_x264.mp4:f15, anomaly/Robbery/Robbery048_x264.mp4:f16, anomaly/Robbery/Robbery048_x264.mp4:f17, anomaly/Robbery/Robbery048_x264.mp4:f18, mechanical: supported) cross_source_support: The evidence indicates object-source person detections temporally co-occur with different-source surveillance-event hypotheses in the same windows; this is source co-occurrence only and does not confirm involvement or a crime. | grade: ____ notes: ____
- [claim_009] (anomaly/Robbery/Robbery048_x264.mp4:f6, anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f9, anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f15, anomaly/Robbery/Robbery048_x264.mp4:f16, anomaly/Robbery/Robbery048_x264.mp4:f17, anomaly/Robbery/Robbery048_x264.mp4:f18, mechanical: supported) The available evidence suggests two main periods of persistent person presence from 12.8s to 23.333s and from 32.0s to 40.4s, separated by a gap with no supplied evidence. | grade: ____ notes: ____
- [claim_010] (anomaly/Robbery/Robbery048_x264.mp4:f2, anomaly/Robbery/Robbery048_x264.mp4:f6, anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f9, anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f15, anomaly/Robbery/Robbery048_x264.mp4:f16, anomaly/Robbery/Robbery048_x264.mp4:f17, anomaly/Robbery/Robbery048_x264.mp4:f18, mechanical: supported) The model produced alternating RoadAccidents (0.2554-0.4406) and Shooting (0.3359-0.4559) hypotheses at modest confidences; the evidence is consistent with unstable hypotheses rather than confirmation of any crime. | grade: ____ notes: ____
- [claim_011] (anomaly/Robbery/Robbery048_x264.mp4:f2, anomaly/Robbery/Robbery048_x264.mp4:f6, anomaly/Robbery/Robbery048_x264.mp4:f7, anomaly/Robbery/Robbery048_x264.mp4:f8, anomaly/Robbery/Robbery048_x264.mp4:f9, anomaly/Robbery/Robbery048_x264.mp4:f10, anomaly/Robbery/Robbery048_x264.mp4:f15, anomaly/Robbery/Robbery048_x264.mp4:f16, anomaly/Robbery/Robbery048_x264.mp4:f17, anomaly/Robbery/Robbery048_x264.mp4:f18, mechanical: supported) The available evidence suggests generic-action labels vary and remain at very low to low confidence (0.0305-0.1873), which limits reliable interpretation of activities. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 11, "unsupported": 0}
- citation: {"cited": 11, "total": 11}
- temporal_uncontained: 0
- failure: null

## I23 — Summarize the incident in anomaly/RoadAccidents/RoadAccidents002_x264.mp4.

Pattern: incident | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] 6 evidence windows span 0.0s to 11.5s | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)

### Full-arm answer
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: null

## I24 — Summarize the incident in anomaly/Shoplifting/Shoplifting031_x264.mp4.

Pattern: incident | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] 7 evidence windows span 0.0s to 14.8s | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)
- anomaly/Shoplifting/Shoplifting031_x264.mp4:f0 | anomaly/Shoplifting/Shoplifting031_x264.mp4 | 0.0-2.0s
- anomaly/Shoplifting/Shoplifting031_x264.mp4:f1 | anomaly/Shoplifting/Shoplifting031_x264.mp4 | 2.133-4.133s
- anomaly/Shoplifting/Shoplifting031_x264.mp4:f2 | anomaly/Shoplifting/Shoplifting031_x264.mp4 | 4.267-6.267s
- anomaly/Shoplifting/Shoplifting031_x264.mp4:f3 | anomaly/Shoplifting/Shoplifting031_x264.mp4 | 6.4-8.4s
- anomaly/Shoplifting/Shoplifting031_x264.mp4:f4 | anomaly/Shoplifting/Shoplifting031_x264.mp4 | 8.533-10.533s
- anomaly/Shoplifting/Shoplifting031_x264.mp4:f5 | anomaly/Shoplifting/Shoplifting031_x264.mp4 | 10.667-12.667s
- anomaly/Shoplifting/Shoplifting031_x264.mp4:f6 | anomaly/Shoplifting/Shoplifting031_x264.mp4 | 12.8-14.8s

### Full-arm answer
Title: Incident Summary: anomaly/Shoplifting/Shoplifting031_x264.mp4
Summary: The retrieved evidence supports a persistent Shoplifting surveillance-event hypothesis from 0.0s to 14.8s coinciding with person detections, with limited low-confidence generic-action context. The evidence does not establish involvement, activity, or identity.
- timeline 0.0-4.133: The evidence indicates person count 1 overlapped with Shoplifting hypotheses (confidence 0.9959-0.9976) and low-confidence 'garbage collecting' labels. The model produced these hypotheses.
- timeline 4.267-10.533: The evidence indicates person counts 2 to 3 overlapped with Shoplifting hypotheses (confidence 0.9908-0.9963) and low-confidence 'garbage collecting' labels. The model produced these hypotheses.
- timeline 10.667-14.8: The evidence indicates person counts 2 to 1 overlapped with Shoplifting hypotheses (confidence 0.9978-0.9988) and low-confidence 'garbage collecting' labels. The model produced these hypotheses.
- finding: The retrieved evidence supports a persistent Shoplifting surveillance-event hypothesis across the segment. The surveillance-event model produced a Shoplifting hypothesis in each window with confidence 0.9908-0.9988. The evidence does not establish a confirmed crime.
- finding: The evidence indicates person detections co-occurred with the Shoplifting hypotheses in the same windows, with counts of 1 to 3. This is source agreement only and the evidence does not establish involvement, role, or identity.
- finding: The available evidence is consistent with person presence throughout the segment, but generic-action labels of 'garbage collecting' were low-confidence and provide limited context for determining activity. All records belong to the same incident anomaly/Shoplifting/Shoplifting031_x264.mp4:i0.

### Full-arm claims (grade each)
- [claim_001] (anomaly/Shoplifting/Shoplifting031_x264.mp4:f0, anomaly/Shoplifting/Shoplifting031_x264.mp4:f1, anomaly/Shoplifting/Shoplifting031_x264.mp4:f2, anomaly/Shoplifting/Shoplifting031_x264.mp4:f3, anomaly/Shoplifting/Shoplifting031_x264.mp4:f4, anomaly/Shoplifting/Shoplifting031_x264.mp4:f5, anomaly/Shoplifting/Shoplifting031_x264.mp4:f6, mechanical: supported) The evidence indicates person detections (counts 1 to 3) temporally overlapped with Shoplifting surveillance-event hypotheses (confidence 0.9908-0.9988) and low-confidence 'garbage collecting' generic-action labels from 0.0s to 14.8s; the model produced these hypotheses and the evidence does not establish involvement. | grade: ____ notes: ____
- [claim_002] (anomaly/Shoplifting/Shoplifting031_x264.mp4:f0, anomaly/Shoplifting/Shoplifting031_x264.mp4:f1, anomaly/Shoplifting/Shoplifting031_x264.mp4:f2, anomaly/Shoplifting/Shoplifting031_x264.mp4:f3, anomaly/Shoplifting/Shoplifting031_x264.mp4:f4, anomaly/Shoplifting/Shoplifting031_x264.mp4:f5, anomaly/Shoplifting/Shoplifting031_x264.mp4:f6, mechanical: supported) same_incident: The evidence indicates all seven records belong to the same Phase 2D incident anomaly/Shoplifting/Shoplifting031_x264.mp4:i0. | grade: ____ notes: ____
- [claim_003] (anomaly/Shoplifting/Shoplifting031_x264.mp4:f0, anomaly/Shoplifting/Shoplifting031_x264.mp4:f1, anomaly/Shoplifting/Shoplifting031_x264.mp4:f2, anomaly/Shoplifting/Shoplifting031_x264.mp4:f3, anomaly/Shoplifting/Shoplifting031_x264.mp4:f4, anomaly/Shoplifting/Shoplifting031_x264.mp4:f5, anomaly/Shoplifting/Shoplifting031_x264.mp4:f6, mechanical: supported) persistent_event: The available evidence suggests compatible Shoplifting hypotheses persisted across adjacent windows from 0.0s to 14.8s. | grade: ____ notes: ____
- [claim_004] (anomaly/Shoplifting/Shoplifting031_x264.mp4:f0, anomaly/Shoplifting/Shoplifting031_x264.mp4:f1, anomaly/Shoplifting/Shoplifting031_x264.mp4:f2, anomaly/Shoplifting/Shoplifting031_x264.mp4:f3, anomaly/Shoplifting/Shoplifting031_x264.mp4:f4, anomaly/Shoplifting/Shoplifting031_x264.mp4:f5, anomaly/Shoplifting/Shoplifting031_x264.mp4:f6, mechanical: supported) cross_source_support: The evidence indicates person object detections and Shoplifting surveillance-event hypotheses co-occurred in the same windows; this is source agreement only and does not confirm involvement. | grade: ____ notes: ____
- [claim_005] (anomaly/Shoplifting/Shoplifting031_x264.mp4:f0, anomaly/Shoplifting/Shoplifting031_x264.mp4:f1, anomaly/Shoplifting/Shoplifting031_x264.mp4:f2, anomaly/Shoplifting/Shoplifting031_x264.mp4:f3, anomaly/Shoplifting/Shoplifting031_x264.mp4:f4, anomaly/Shoplifting/Shoplifting031_x264.mp4:f5, anomaly/Shoplifting/Shoplifting031_x264.mp4:f6, mechanical: supported) The available evidence is consistent with a persistent Shoplifting hypothesis coinciding with person presence throughout the segment, but low generic-action confidence provides limited context for determining activity or involvement. | grade: ____ notes: ____

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 5, "unsupported": 0}
- citation: {"cited": 5, "total": 5}
- temporal_uncontained: 0
- failure: null

## I25 — Describe activity in normal/Normal_Videos_247_x264.mp4 between 100 and 150 seconds without confirming any crime.

Pattern: cautious | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] 25 evidence windows overlap the interval | baseline: ____ full: ____ notes: ____
- [F02] video carries no annotated anomaly interval | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)

### Full-arm answer
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: null

## I26 — Describe activity in normal/Normal_Videos_310_x264.mp4 without confirming any crime.

Pattern: cautious | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] 40 evidence windows in total | baseline: ____ full: ____ notes: ____
- [F02] video carries no annotated anomaly interval | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)

### Full-arm answer
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: null

## I27 — Describe activity in normal/Normal_Videos_289_x264.mp4 between 5 and 10 seconds without confirming any crime.

Pattern: cautious | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] video carries no annotated anomaly interval | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)

### Full-arm answer
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: null

## I28 — Show evidence in anomaly/RoadAccidents/RoadAccidents021_x264.mp4.

Pattern: sparse | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] only 3 evidence windows exist in total | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)

### Full-arm answer
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: null

## I29 — Show evidence in anomaly/Shooting/Shooting037_x264.mp4.

Pattern: sparse | abstention expected: False

### Expected facts (grade baseline + full)
- [F01] only 5 evidence windows exist in total | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)
- anomaly/Shooting/Shooting037_x264.mp4:f0 | anomaly/Shooting/Shooting037_x264.mp4 | 0.0-2.0s
- anomaly/Shooting/Shooting037_x264.mp4:f1 | anomaly/Shooting/Shooting037_x264.mp4 | 2.133-4.133s
- anomaly/Shooting/Shooting037_x264.mp4:f2 | anomaly/Shooting/Shooting037_x264.mp4 | 4.267-6.267s
- anomaly/Shooting/Shooting037_x264.mp4:f3 | anomaly/Shooting/Shooting037_x264.mp4 | 6.4-8.4s
- anomaly/Shooting/Shooting037_x264.mp4:f4 | anomaly/Shooting/Shooting037_x264.mp4 | 8.534-10.134s

### Full-arm answer
Title: None
Summary: None

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: {"error": "report summary contains unsupported language: 'definitely occurred'", "stage": "3f", "type": "validation"}

## I30 — Show truck detections in anomaly/Arson/Arson009_x264.mp4.

Pattern: no-evidence | abstention expected: True

### Expected facts (grade baseline + full)
- [F01] no evidence window carries a truck detection | baseline: ____ full: ____ notes: ____

### Baseline answer (templated, no LLM reasoning)

### Full-arm answer
Title: No verifiable claims
Summary: The supplied analysis contained no claims groundable in retrieved evidence.

### Full-arm claims (grade each)

### Mechanical context (read-only)
- claims: {"partially_supported": 0, "supported": 0, "unsupported": 0}
- citation: {"cited": 0, "total": 0}
- temporal_uncontained: 0
- failure: null
