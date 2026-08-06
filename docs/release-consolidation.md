# XPRIZE release consolidation

Release branch: `release/xprize-2026`

Verified implementation base at branch creation:
`7d48e4f1e050551c0f7135282874dda91101d463`.

`main` was `d8e4156370418c7c07025c7866fa55e73fdf3a94`. The release base is a
strict descendant of `main` with no main-only commits. The complete stack is
linear and has these named dependency points, oldest to newest:

1. `agent/complete-premium-product-ui` at `fd613f0`
2. `agent/core-product-completion` at `093a186`
3. `agent/core-product-hardening` at `e2f08a7`
4. `agent/core-product-finalization` at `dfc8c5b`
5. `agent/exceptional-judge-experience` at `dd25da1`
6. `agent/internship-learning-platform` at `8161ae2`
7. `agent/internship-platform-completion` at `7d48e4f`

The release pull request must target `main` directly. None of the named agent
branches is a runtime, deployment, or review dependency after consolidation.
The exact ahead/behind counts and commit list must be refreshed in the release
PR immediately before merge.
