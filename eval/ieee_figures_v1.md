# IEEE Figures v1 — provenance report

All values transcribed from `eval/investigation_human_review_ablation_v1_locked.json`
(summary block) and cross-checked against the locked counts. No values
recalculated, no rounding beyond the two decimals stored in the artifacts.

## fig1_baseline_vs_full (.png/.pdf)
- Chart type: 100% stacked bar (matplotlib, no seaborn, no subplots).
- Source: locked summary — baseline {28,10,8}, full {34,8,4}, n=46 each.
- Values: 60.87/21.74/17.39 and 73.91/17.39/8.70; bars total 100.00%.
- Verified match: yes (28/46=60.87, 10/46=21.74, 8/46=17.39,
  34/46=73.91, 8/46=17.39, 4/46=8.70).

## fig2_ablation (.png/.pdf)
- Chart type: bar chart with value labels + subtle pp-difference annotations.
- Source: locked summary — Full 34/46, NT 5/46, NV 13/46, NP 7/46.
- Values: 73.91 / 10.87 / 28.26 / 15.22; deltas −63.04 / −45.65 / −58.69 pp.
- Verified match: yes (5/46=10.87, 13/46=28.26, 7/46=15.22).

## fig3_temporal_support (.png/.pdf)
- Chart type: bar chart.
- Source: locked `temporal_subset_stats` — Full 12/12, NT 0/12, NV 6/12,
  NP 0/12 over cases I10–I15 only.
- Values: 100.00 / 0.00 / 50.00 / 0.00.
- Verified match: yes. No 8/8 temporal-relation claim anywhere in figures
  or captions.

## Output specification
- Dimensions: 3.5 x 2.6 in (IEEE single-column), `bbox_inches="tight"`.
- PNG DPI: 600.
- PDF: true vector output (matplotlib PDF backend).
- Style: serif, white background, light horizontal gridlines only,
  compact legends, no 3D/decorations.

## Confirmations
- No pre-existing figures existed; `figures/` is new, nothing modified.
- Locked evaluation JSON and human grading artifacts untouched.
- No "accuracy" wording in any figure title, label, legend, or caption
  (captions live with the paper, not in the figures).
