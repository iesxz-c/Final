# Locked Ablation Human Grades v1

Transcribed exactly from AEGIS_Ablation_Human_Grading_Sheet.xlsx (`Your POV` columns). Full-system reference reproduced verbatim from the locked review. Reviewer identity and date not recorded.

## Aggregate expected-fact support rates (human-judged, n=46)

| Configuration | Supported | Partial | Unsupported | Supported % |
|---|---|---|---|---|
| Full | 34 | 8 | 4 | 73.91 |
| No Temporal | 5 | 20 | 21 | 10.87 |
| No Verification | 13 | 18 | 15 | 28.26 |
| No Planning | 7 | 14 | 25 | 15.22 |

Change vs Full (percentage points, fully supported benchmark facts):
- No Temporal: -63.04
- No Verification: -45.65
- No Planning: -58.69

## Claim-level evidence grounding (Full only, n=158)

- 155 supported / 3 partial / 0 unsupported (98.10% claim-support rate — a grounding rate, not classification accuracy)

## Temporal subset I10–I15 (12 facts)

- Full: 12/0/0 (100.00% fully supported)
- No Temporal: 0/4/8 (0.00% fully supported)
- No Verification: 6/4/2 (50.00% fully supported)
- No Planning: 0/3/9 (0.00% fully supported)

Note: only 5 benchmark temporal relations were explicitly human graded (all Supported for Baseline and Full); 3 remain ungraded and are excluded from all percentages.

## Per-case grades

### I01 — Show person detections in anomaly/Burglary/Burglary032_x264.mp4 between 27 and 49 seconds.
- F01: NT=Partial, NV=Supported, NP=Supported — person detected in 9 evidence windows
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Supported, NV=Supported, NP=Supported — windows span 27.7s to 48.9s
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F03: NT=Partial, NV=Supported, NP=Supported — Burglary surveillance-event label present in all 9 windows
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I02 — Show car detections in anomaly/RoadAccidents/RoadAccidents011_x264.mp4.
- F01: NT=Partial, NV=Unsupported, NP=Unsupported — car detected in 34 evidence windows
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Partial, NV=Partial, NP=Unsupported — windows span 0.0s to 71.9s
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I03 — Show person detections in normal/Normal_Videos_251_x264.mp4.
- F01: NT=Unsupported, NV=Partial, NP=Partial — person detected in 7 evidence windows
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Unsupported, NV=Unsupported, NP=Unsupported — video carries no annotated anomaly interval
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I04 — Show driving-car activity in anomaly/RoadAccidents/RoadAccidents016_x264.mp4.
- F01: NT=Partial, NV=Partial, NP=Unsupported — driving car activity present in 14 evidence windows
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I05 — Show garbage-collecting activity in anomaly/Shoplifting/Shoplifting020_x264.mp4 between 0 and 100 seconds.
- F01: NT=Unsupported, NV=Unsupported, NP=Unsupported — garbage collecting activity present in 2 evidence windows
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I06 — Show extinguishing-fire activity in anomaly/Arson/Arson041_x264.mp4.
- F01: NT=Unsupported, NV=Unsupported, NP=Unsupported — extinguishing fire activity present in 2 evidence windows
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I07 — Show Arrest evidence in anomaly/Arrest/Arrest039_x264.mp4 between 0 and 120 seconds.
- F01: NT=Partial, NV=Unsupported, NP=Unsupported — Arrest surveillance-event label present in 11 evidence windows
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I08 — Show Shoplifting evidence in anomaly/Shoplifting/Shoplifting044_x264.mp4 between 0 and 60 seconds.
- F01: NT=Partial, NV=Partial, NP=Partial — Shoplifting surveillance-event label present in 23 evidence windows
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Partial, NV=Unsupported, NP=Unsupported — windows span 0.0s to 61.7s
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I09 — Show Burglary evidence in anomaly/Burglary/Burglary033_x264.mp4.
- F01: NT=Partial, NV=Partial, NP=Unsupported — Burglary surveillance-event label present in 20 evidence windows
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I10 — Reconstruct the event order in anomaly/Shooting/Shooting010_x264.mp4 between 36 and 42 seconds.
- F01: NT=Unsupported, NV=Partial, NP=Unsupported — annotated Shooting interval is 36.5s to 42.0s (frames 1095-1260 at 30 fps)
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Partial, NV=Supported, NP=Partial — evidence windows f17, f18, f19 overlap the annotated interval
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I11 — Reconstruct the event order in anomaly/Robbery/Robbery048_x264.mp4 between 14 and 32 seconds.
- F01: NT=Unsupported, NV=Unsupported, NP=Unsupported — annotated Robbery interval is 15.0s to 31.0s (frames 450-930 at 30 fps)
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Partial, NV=Unsupported, NP=Unsupported — evidence windows f7 through f14 overlap the annotated interval
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I12 — Reconstruct the event order in anomaly/Explosion/Explosion036_x264.mp4 between 65 and 69 seconds.
- F01: NT=Partial, NV=Supported, NP=Partial — annotated Explosion interval is 65.0s to 69.0s (frames 1950-2070 at 30 fps)
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Partial, NV=Supported, NP=Partial — 3 evidence windows overlap the annotated interval
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I13 — Describe the Burglary to Shoplifting transition in anomaly/Shoplifting/Shoplifting034_x264.mp4 around 27 seconds.
- F01: NT=Unsupported, NV=Partial, NP=Unsupported — window f12 carries the Burglary surveillance-event label
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Unsupported, NV=Partial, NP=Unsupported — window f13 carries the Shoplifting surveillance-event label
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I14 — Describe the Shoplifting to Burglary transition in anomaly/Shoplifting/Shoplifting034_x264.mp4 around 166 seconds.
- F01: NT=Unsupported, NV=Supported, NP=Unsupported — window f77 carries the Shoplifting surveillance-event label
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Unsupported, NV=Supported, NP=Unsupported — window f78 carries the Burglary surveillance-event label
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I15 — Describe the Vandalism to Assault transition in anomaly/Assault/Assault010_x264.mp4 around 60 to 76 seconds.
- F01: NT=Unsupported, NV=Partial, NP=Unsupported — window f29 carries the Vandalism surveillance-event label
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Unsupported, NV=Supported, NP=Unsupported — window f35 carries the Assault surveillance-event label
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I16 — Show evidence around 100 seconds in anomaly/Burglary/Burglary032_x264.mp4.
- F01: NT=Partial, NV=Partial, NP=Partial — 10 evidence windows overlap the 90s to 110s interval
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I17 — Show evidence between 400 and 440 seconds in anomaly/Explosion/Explosion007_x264.mp4.
- F01: NT=Unsupported, NV=Unsupported, NP=Unsupported — 20 evidence windows overlap the 400s to 440s interval
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I18 — Show evidence between 200 and 220 seconds in anomaly/Assault/Assault010_x264.mp4.
- F01: NT=Unsupported, NV=Partial, NP=Unsupported — 11 evidence windows overlap the 200s to 220s interval
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I19 — Show person detections with RoadAccidents evidence in anomaly/RoadAccidents/RoadAccidents001_x264.mp4.
- F01: NT=Partial, NV=Partial, NP=Partial — a single window f6 carries both a person detection and the RoadAccidents label
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Supported, NV=Supported, NP=Supported — window f6 spans 12.8s to 14.8s
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I20 — Show person detections with Burglary evidence in anomaly/Burglary/Burglary032_x264.mp4 between 27 and 49 seconds.
- F01: NT=Partial, NV=Partial, NP=Unsupported — 9 evidence windows carry both a person detection and the Burglary label
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I21 — Show suitcase detections with Shoplifting evidence in anomaly/Shoplifting/Shoplifting034_x264.mp4 between 36 and 60 seconds.
- F01: NT=Unsupported, NV=Partial, NP=Partial — 4 evidence windows carry both a suitcase detection and the Shoplifting label
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I22 — Summarize the incident in anomaly/Robbery/Robbery048_x264.mp4.
- F01: NT=Unsupported, NV=Partial, NP=Partial — 23 evidence windows span 0.0s to 46.9s
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Partial, NV=Unsupported, NP=Partial — annotated Robbery interval is 15.0s to 31.0s
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F03: NT=Partial, NV=Unsupported, NP=Partial — windows f7 through f14 overlap the annotated interval
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I23 — Summarize the incident in anomaly/RoadAccidents/RoadAccidents002_x264.mp4.
- F01: NT=Unsupported, NV=Unsupported, NP=Unsupported — 6 evidence windows span 0.0s to 11.5s
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I24 — Summarize the incident in anomaly/Shoplifting/Shoplifting031_x264.mp4.
- F01: NT=Unsupported, NV=Partial, NP=Partial — 7 evidence windows span 0.0s to 14.8s
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I25 — Describe activity in normal/Normal_Videos_247_x264.mp4 between 100 and 150 seconds without confirming any crime.
- F01: NT=Unsupported, NV=Unsupported, NP=Partial — 25 evidence windows overlap the interval
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Supported, NV=Supported, NP=Supported — video carries no annotated anomaly interval
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I26 — Describe activity in normal/Normal_Videos_310_x264.mp4 without confirming any crime.
- F01: NT=Unsupported, NV=Unsupported, NP=Unsupported — 40 evidence windows in total
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
- F02: NT=Supported, NV=Supported, NP=Supported — video carries no annotated anomaly interval
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I27 — Describe activity in normal/Normal_Videos_289_x264.mp4 between 5 and 10 seconds without confirming any crime.
- F01: NT=Partial, NV=Partial, NP=Partial — video carries no annotated anomaly interval
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I28 — Show evidence in anomaly/RoadAccidents/RoadAccidents021_x264.mp4.
- F01: NT=Unsupported, NV=Unsupported, NP=Unsupported — only 3 evidence windows exist in total
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I29 — Show evidence in anomaly/Shooting/Shooting037_x264.mp4.
- F01: NT=Partial, NV=Partial, NP=Unsupported — only 5 evidence windows exist in total
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 

### I30 — Show truck detections in anomaly/Arson/Arson009_x264.mp4.
- F01: NT=Supported, NV=Supported, NP=Supported — no evidence window carries a truck detection
  study note: If this ablated arm drops from Supported to Partial/Unsupported compared with Full, that is evidence that the removed component contributed to this capability. 
