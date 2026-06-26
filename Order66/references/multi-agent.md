# Multi-Agent Use

When multiple agents are working in parallel:

- Each agent must state its owned files/modules before editing.
- Each agent must avoid broad format churn outside its owned files.
- Each agent should run this skill twice: once before editing to find likely release
  blockers, and once after editing to report residual risks.
- Final handoff must distinguish:
  - issues fixed;
  - tests run;
  - tests not run;
  - manual smoke still required;
  - unrelated dirty files observed but not touched.
- If two agents touch shared command wiring or shared API types, the integrator must run a
  final combined check after both land.
