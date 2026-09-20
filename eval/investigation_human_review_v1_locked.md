# Locked Human Evaluation Record v1

Manual grades transcribed authoritatively from the outside-repository human review. Mechanical validator statuses are preserved as context only. Reviewer identity and review date were not recorded.

## Aggregate counts (verified programmatically)

- Baseline facts: 28 supported / 10 partial / 8 unsupported (n=46)
- Full-system facts: 34 supported / 8 partial / 4 unsupported (n=46)
- Full-system claims: 155 supported / 3 partial / 0 unsupported (n=158)

## Temporal relations

- Explicitly human graded (Supported/Supported): I11, I12, I13, I14, I15
- Not yet human graded (excluded from percentages): I01, I10

## Per-case grades

### I01 — Show person detections in anomaly/Burglary/Burglary032_x264.mp4 between 27 and 49 seconds.
- F01: baseline=Unsupported, full=Partial — person detected in 9 evidence windows
- F02: baseline=Supported, full=Supported — windows span 27.7s to 48.9s
- F03: baseline=Supported, full=Supported — Burglary surveillance-event label present in all 9 windows
- Partial claims: claim_006
- temporal before f13 -> f22: baseline=not yet human graded, full=not yet human graded

### I02 — Show car detections in anomaly/RoadAccidents/RoadAccidents011_x264.mp4.
- F01: baseline=Partial, full=Partial — car detected in 34 evidence windows
- F02: baseline=Supported, full=Supported — windows span 0.0s to 71.9s

### I03 — Show person detections in normal/Normal_Videos_251_x264.mp4.
- F01: baseline=Unsupported, full=Supported — person detected in 7 evidence windows
- F02: baseline=Unsupported, full=Unsupported — video carries no annotated anomaly interval
- Partial claims: claim_002, claim_005

### I04 — Show driving-car activity in anomaly/RoadAccidents/RoadAccidents016_x264.mp4.
- F01: baseline=Unsupported, full=Supported — driving car activity present in 14 evidence windows

### I05 — Show garbage-collecting activity in anomaly/Shoplifting/Shoplifting020_x264.mp4 between 0 and 100 seconds.
- F01: baseline=Unsupported, full=Unsupported — garbage collecting activity present in 2 evidence windows

### I06 — Show extinguishing-fire activity in anomaly/Arson/Arson041_x264.mp4.
- F01: baseline=Partial, full=Supported — extinguishing fire activity present in 2 evidence windows

### I07 — Show Arrest evidence in anomaly/Arrest/Arrest039_x264.mp4 between 0 and 120 seconds.
- F01: baseline=Supported, full=Supported — Arrest surveillance-event label present in 11 evidence windows

### I08 — Show Shoplifting evidence in anomaly/Shoplifting/Shoplifting044_x264.mp4 between 0 and 60 seconds.
- F01: baseline=Supported, full=Supported — Shoplifting surveillance-event label present in 23 evidence windows
- F02: baseline=Supported, full=Supported — windows span 0.0s to 61.7s

### I09 — Show Burglary evidence in anomaly/Burglary/Burglary033_x264.mp4.
- F01: baseline=Supported, full=Supported — Burglary surveillance-event label present in 20 evidence windows

### I10 — Reconstruct the event order in anomaly/Shooting/Shooting010_x264.mp4 between 36 and 42 seconds.
- F01: baseline=Supported, full=Supported — annotated Shooting interval is 36.5s to 42.0s (frames 1095-1260 at 30 fps)
- F02: baseline=Supported, full=Supported — evidence windows f17, f18, f19 overlap the annotated interval
- temporal before f17 -> f18: baseline=not yet human graded, full=not yet human graded
- temporal before f18 -> f19: baseline=not yet human graded, full=not yet human graded

### I11 — Reconstruct the event order in anomaly/Robbery/Robbery048_x264.mp4 between 14 and 32 seconds.
- F01: baseline=Supported, full=Supported — annotated Robbery interval is 15.0s to 31.0s (frames 450-930 at 30 fps)
- F02: baseline=Supported, full=Supported — evidence windows f7 through f14 overlap the annotated interval
- temporal before f7 -> f14: baseline=Supported, full=Supported

### I12 — Reconstruct the event order in anomaly/Explosion/Explosion036_x264.mp4 between 65 and 69 seconds.
- F01: baseline=Supported, full=Supported — annotated Explosion interval is 65.0s to 69.0s (frames 1950-2070 at 30 fps)
- F02: baseline=Supported, full=Supported — 3 evidence windows overlap the annotated interval
- temporal before f30 -> f32: baseline=Supported, full=Supported

### I13 — Describe the Burglary to Shoplifting transition in anomaly/Shoplifting/Shoplifting034_x264.mp4 around 27 seconds.
- F01: baseline=Supported, full=Supported — window f12 carries the Burglary surveillance-event label
- F02: baseline=Supported, full=Supported — window f13 carries the Shoplifting surveillance-event label
- temporal before f12 -> f13: baseline=Supported, full=Supported

### I14 — Describe the Shoplifting to Burglary transition in anomaly/Shoplifting/Shoplifting034_x264.mp4 around 166 seconds.
- F01: baseline=Supported, full=Supported — window f77 carries the Shoplifting surveillance-event label
- F02: baseline=Supported, full=Supported — window f78 carries the Burglary surveillance-event label
- temporal before f77 -> f78: baseline=Supported, full=Supported

### I15 — Describe the Vandalism to Assault transition in anomaly/Assault/Assault010_x264.mp4 around 60 to 76 seconds.
- F01: baseline=Supported, full=Supported — window f29 carries the Vandalism surveillance-event label
- F02: baseline=Supported, full=Supported — window f35 carries the Assault surveillance-event label
- temporal before f29 -> f35: baseline=Supported, full=Supported

### I16 — Show evidence around 100 seconds in anomaly/Burglary/Burglary032_x264.mp4.
- F01: baseline=Supported, full=Partial — 10 evidence windows overlap the 90s to 110s interval

### I17 — Show evidence between 400 and 440 seconds in anomaly/Explosion/Explosion007_x264.mp4.
- F01: baseline=Unsupported, full=Unsupported — 20 evidence windows overlap the 400s to 440s interval

### I18 — Show evidence between 200 and 220 seconds in anomaly/Assault/Assault010_x264.mp4.
- F01: baseline=Unsupported, full=Partial — 11 evidence windows overlap the 200s to 220s interval

### I19 — Show person detections with RoadAccidents evidence in anomaly/RoadAccidents/RoadAccidents001_x264.mp4.
- F01: baseline=Partial, full=Supported — a single window f6 carries both a person detection and the RoadAccidents label
- F02: baseline=Supported, full=Supported — window f6 spans 12.8s to 14.8s

### I20 — Show person detections with Burglary evidence in anomaly/Burglary/Burglary032_x264.mp4 between 27 and 49 seconds.
- F01: baseline=Supported, full=Supported — 9 evidence windows carry both a person detection and the Burglary label

### I21 — Show suitcase detections with Shoplifting evidence in anomaly/Shoplifting/Shoplifting034_x264.mp4 between 36 and 60 seconds.
- F01: baseline=Supported, full=Supported — 4 evidence windows carry both a suitcase detection and the Shoplifting label

### I22 — Summarize the incident in anomaly/Robbery/Robbery048_x264.mp4.
- F01: baseline=Supported, full=Supported — 23 evidence windows span 0.0s to 46.9s
- F02: baseline=Supported, full=Supported — annotated Robbery interval is 15.0s to 31.0s
- F03: baseline=Supported, full=Supported — windows f7 through f14 overlap the annotated interval

### I23 — Summarize the incident in anomaly/RoadAccidents/RoadAccidents002_x264.mp4.
- F01: baseline=Unsupported, full=Partial — 6 evidence windows span 0.0s to 11.5s

### I24 — Summarize the incident in anomaly/Shoplifting/Shoplifting031_x264.mp4.
- F01: baseline=Supported, full=Supported — 7 evidence windows span 0.0s to 14.8s

### I25 — Describe activity in normal/Normal_Videos_247_x264.mp4 between 100 and 150 seconds without confirming any crime.
- F01: baseline=Partial, full=Supported — 25 evidence windows overlap the interval
- F02: baseline=Partial, full=Supported — video carries no annotated anomaly interval

### I26 — Describe activity in normal/Normal_Videos_310_x264.mp4 without confirming any crime.
- F01: baseline=Partial, full=Partial — 40 evidence windows in total
- F02: baseline=Partial, full=Partial — video carries no annotated anomaly interval

### I27 — Describe activity in normal/Normal_Videos_289_x264.mp4 between 5 and 10 seconds without confirming any crime.
- F01: baseline=Partial, full=Supported — video carries no annotated anomaly interval

### I28 — Show evidence in anomaly/RoadAccidents/RoadAccidents021_x264.mp4.
- F01: baseline=Partial, full=Partial — only 3 evidence windows exist in total

### I29 — Show evidence in anomaly/Shooting/Shooting037_x264.mp4.
- F01: baseline=Supported, full=Unsupported — only 5 evidence windows exist in total

### I30 — Show truck detections in anomaly/Arson/Arson009_x264.mp4.
- F01: baseline=Partial, full=Supported — no evidence window carries a truck detection
