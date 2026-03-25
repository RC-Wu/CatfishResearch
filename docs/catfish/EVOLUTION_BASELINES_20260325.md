# Catfish Effect Against Evolution Baselines

Date: 2026-03-25

Scope: conservative positioning note for writing about Catfish Effect relative to prior evolve-style scientific-agent systems and closely adjacent evolutionary discovery systems.

## Bottom Line

Catfish should not be framed as introducing evolution, competition, multi-agent scientific workflows, persistent improvement loops, or multi-model usage into AI scientist systems. Those ingredients are already present, in different forms, across prior work such as The AI Scientist, AI Scientist-v2, AI co-scientist, AlphaEvolve, EvoScientist, CausalEvolve, and SAGA.

The strongest plausible Catfish claim is therefore not a new primitive, but a new system composition: explicit catfish-effect competition across agent groups, with parent-level selection, negotiated resource allocation, joint evaluation of provider/model/agent-group bundles, explicit capability-state updates, and a multi-project hierarchical scheduling graph. Even here, the safest wording is "a new orchestration/ecology for evolving scientific agents" rather than "the first evolutionary AI scientist."

## Baseline-By-Baseline Analysis

### The AI Scientist (Lu et al., 2024)

Primary sources:
- [Paper](https://arxiv.org/abs/2408.06292)
- [Official repository](https://github.com/SakanaAI/AI-Scientist)

Core mechanism:
- A template-driven autonomous research pipeline that generates ideas, checks novelty against the literature, writes and edits experiment code within a fixed experimental template, runs experiments, produces a paper draft, and then self-reviews.

Optimization loop:
- Search happens mostly over ideas, prompts, code edits, and reviewer-guided revisions inside a fixed task template.
- It is iterative and open-ended in spirit, but it is not an explicit evolutionary population algorithm with cross-generation parent/child competition.

What kind of evolution/search it performs:
- Prompt-driven search over research ideas and experimental implementations.
- No explicit population evolution, no explicit inter-group competition, and no explicit joint selection over model/provider/agent-group bundles.

What Catfish must not claim as new because of this baseline:
- End-to-end autonomous idea-to-paper execution.
- Automated novelty checking, experiment editing, and paper self-review.
- Using LLM agents to iteratively improve research artifacts without a human in the loop at each step.

Boundary relative to Catfish:
- Catfish can still claim a more explicit evolutionary ecology than The AI Scientist, but it should not claim to be the first autonomous scientific-agent loop.

### AI Scientist-v2 (Sakana AI, 2025)

Primary sources:
- [Paper](https://arxiv.org/abs/2504.08066)
- [Official repository](https://github.com/SakanaAI/AI-Scientist-v2)

Core mechanism:
- A stronger open-ended AI scientist system centered on agentic search rather than a single linear pipeline.
- The system uses best-first tree search over research directions, allocates effort across branches, and manages multiple drafts and execution attempts.

Optimization loop:
- Generate candidate directions and drafts.
- Expand promising branches with additional compute.
- Run experiments, debug, and refine promising nodes.
- Use search control to distribute effort across a tree of scientific trajectories.

What kind of evolution/search it performs:
- Explicit agentic tree search with compute allocation across branches.
- More search-heavy than the original AI Scientist, but still not a documented catfish-style population ecology.

What Catfish must not claim as new because of this baseline:
- Scaling scientific-agent performance with structured search rather than a single serial loop.
- Branch-level resource allocation.
- Maintaining multiple candidate scientific trajectories at once.

Boundary relative to Catfish:
- If Catfish has a multi-project hierarchical scheduling graph, that can be positioned as broader than AI Scientist-v2's branch search.
- But Catfish should not claim to be the first system to allocate search budget across multiple candidate research paths.

### AI co-scientist (Google, 2025)

Primary source:
- [Paper](https://arxiv.org/abs/2502.18864)

Core mechanism:
- A multi-agent scientific reasoning system with specialized agents that generate, debate, critique, rank, and refine hypotheses.
- Test-time compute is scaled by generating many candidates and evolving them through tournament-style selection and iterative refinement.

Optimization loop:
- Produce multiple hypotheses.
- Subject them to debate, critique, and ranking.
- Run tournament evolution to keep stronger hypotheses and refine them further.

What kind of evolution/search it performs:
- Hypothesis-level tournament evolution inside a scientific multi-agent system.
- Strong evidence that competitive evolutionary refinement in science-facing agents already exists in prior art.

What Catfish must not claim as new because of this baseline:
- Competition among candidate scientific outputs.
- Tournament-style refinement of scientific hypotheses.
- Multi-agent scientific discovery with explicit test-time compute scaling.

Boundary relative to Catfish:
- Catfish may still differ if its unit of competition is not just hypotheses but agent groups plus their provider/model configuration and resource contracts.
- That distinction must be stated explicitly; otherwise the overlap with AI co-scientist is substantial.

### AlphaEvolve (Google DeepMind, 2025)

Primary sources:
- [White paper PDF](https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/AlphaEvolve.pdf)
- [Official announcement](https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/)

Core mechanism:
- An evolutionary coding agent for algorithm discovery.
- Candidate programs live in an evolutionary database; an LLM prompt sampler selects prior solutions, proposes edits, evaluates new programs with automated metrics, and re-inserts successful variants.
- The system uses a heterogeneous model stack, with faster models for breadth and stronger models for depth.

Optimization loop:
- Sample prior programs from a growing repository.
- Mutate or improve them with LLM-generated edits.
- Evaluate candidates with automated graders.
- Reinsert successful children into the search population and continue asynchronously.

What kind of evolution/search it performs:
- Explicit evolutionary search over executable artifacts with evaluator-driven selection.
- Population/database-based search with automated fitness.
- Closest prior art for "LLM as mutation operator plus evaluator-defined evolution."

What Catfish must not claim as new because of this baseline:
- LLM-guided evolutionary search over programmatic artifacts.
- Automated evaluator-driven selection.
- Combining stronger and weaker models in the same evolutionary loop.
- Maintaining an asynchronous search population rather than a single chain of edits.

Boundary relative to Catfish:
- AlphaEvolve is not itself a full scientific-agent ecology, but it sharply weakens any Catfish claim that "evolutionary LLM systems with heterogeneous models and automated fitness" are new.
- Catfish has to differentiate at the level of scientific-agent organization, competition structure, and scheduling, not at the level of generic LLM-based evolution.

### EvoScientist (Yuan et al., 2026)

Primary source:
- [Paper](https://arxiv.org/abs/2603.08127)

Core mechanism:
- A multi-agent scientific system explicitly built around evolutionary improvement.
- The paper introduces an evolving AI scientist architecture with modules for ideation, execution, evaluation, and memory, plus a repeated evolution cycle across generated agents or scientific artifacts.

Optimization loop:
- Generate agentic or research candidates.
- Run experiments and evaluate outcomes.
- Update memory and evolve forward based on observed performance.
- Repeat over multiple rounds to improve scientific productivity.

What kind of evolution/search it performs:
- Explicit evolving AI scientist loop with memory and multi-agent structure.
- Among the closest baselines to Catfish in spirit.

What Catfish must not claim as new because of this baseline:
- "Evolving AI scientist" as a phrase or overall concept.
- Combining multi-agent scientific workflows with explicit evolution.
- Persistent memory/state updates that inform future rounds.

Boundary relative to Catfish:
- Any Catfish novelty claim has to be narrower than "an evolutionary AI scientist."
- The plausible boundary is a particular ecological design: explicit catfish-pressure across agent groups, bargaining, and joint evaluation of group composition and models.

### CausalEvolve (Chen et al., 2026)

Primary source:
- [Paper](https://arxiv.org/abs/2603.14575)

Core mechanism:
- An open-ended discovery system that combines evolutionary search with an explicitly maintained causal scratchpad.
- The system tries to improve not just candidate solutions, but the intermediate explanatory structure used to guide later search.

Optimization loop:
- Propose candidate solutions.
- Evaluate them and infer causal relations from outcomes.
- Update the scratchpad and use it to steer future mutations or refinements.

What kind of evolution/search it performs:
- Evolutionary search with persistent structured guidance.
- A relevant follow-up because it shows that memory-guided or explanation-guided evolution is already on record.

What Catfish must not claim as new because of this baseline:
- Coupling evolutionary search with persistent structured state that gets updated between rounds.
- Improving future search by distilling prior execution outcomes into explicit internal guidance.

Boundary relative to Catfish:
- If `Capability.md` is essentially an evolving structured memory of what an agent group can do, that overlaps conceptually with CausalEvolve-style scratchpad updates.
- The novelty would therefore have to be in how capability state participates in scheduling, bargaining, or population selection, not in the mere existence of an updated state file.

### Accelerating Scientific Discovery with Autonomous Goal-evolving Agents (SAGA, Du et al., 2025)

Primary source:
- [Paper](https://arxiv.org/abs/2512.21782)

Core mechanism:
- A bi-level self-improving agent system in which the outer loop proposes and revises goals or scoring functions while the inner loop optimizes behavior under the current objective.

Optimization loop:
- Observe current performance.
- Revise the goal or reward/scoring formulation.
- Optimize again under the revised objective.
- Continue open-endedly.

What kind of evolution/search it performs:
- Objective evolution plus solution optimization.
- Not a direct AI scientist paper, but directly relevant if Catfish evolves scoring logic, parent-selection rules, or bargaining incentives.

What Catfish must not claim as new because of this baseline:
- Open-ended evolution of objectives or scoring functions.
- Treating the optimization criterion itself as adaptively revisable.

Boundary relative to Catfish:
- If Catfish's parent-only scoring or bargaining rules are fixed, SAGA is mostly adjacent prior art.
- If Catfish adapts those rules online, then SAGA becomes a stronger overlap and novelty language should be reduced accordingly.

### Short Adjacency Checks

These are relevant enough to cite if a reviewer asks for more coverage, but they are weaker primary baselines than the systems above.

#### ShinkaEvolve (2025)

Primary source:
- [Paper](https://arxiv.org/abs/2509.19349)

Usefulness:
- Reinforces that AlphaEvolve-style LLM-guided evolutionary search was quickly generalized into an open-source framework.
- Weakens any "AlphaEvolve is unique and Catfish is the next such system" story.

#### EarthLink: A Self-Evolving AI Agent System for Climate Science (2026)

Primary source:
- [Paper](https://arxiv.org/abs/2507.17311)

Usefulness:
- Shows domain-specific scientific agents already being framed as self-evolving systems.
- This makes "self-evolving scientific agent" a weak novelty claim unless Catfish's mechanism is clearly different.

## What Is Clearly Not New In Catfish

Based on the sources above, Catfish should not claim novelty for any of the following in isolation:

- Autonomous end-to-end scientific workflows.
- Multi-agent decomposition for scientific ideation, experimentation, critique, or writing.
- Search over multiple scientific candidates rather than following one serial path.
- Evolutionary or tournament-style improvement of candidate hypotheses/programs.
- Evaluator-driven selection using automated metrics.
- Persistent memory or structured state updates between rounds.
- Using multiple models of different strengths in one search system.
- Dynamic allocation of compute across branches or candidates.
- Self-improving scoring/objective loops in the broad sense.

## Likely Novel Combination In Catfish

The most defensible Catfish story is a systems-combination contribution rather than a claim of a new search primitive.

| Catfish element | Conservative novelty assessment | Why |
|---|---|---|
| Explicit catfish-effect competition across agent groups | Moderate | Competition already exists in AI co-scientist and evolutionary search already exists in AlphaEvolve/EvoScientist, but the checked sources do not document an explicit catfish-pressure design over multiple agent groups as the central organizing mechanism. |
| Parent-only scoring | Weak to moderate | Selection rules are generally design choices inside evolutionary systems. The exact parent-only rule may be new in this exact package, but it is not a strong standalone novelty claim unless it yields a clear empirical advantage. |
| Resource bargaining across groups | Moderate | Prior work allocates compute and search budget, but the checked primary sources do not show explicit bargaining or negotiated resource exchange between scientific agent groups. |
| Provider/model/agent-group co-evaluation | Moderate to strong | Prior work uses multiple models, but joint selection over provider plus model plus agent-group composition is not clearly documented in the checked baselines. |
| `Capability.md` updates | Weak to moderate | Persistent structured memory is already present conceptually in EvoScientist and CausalEvolve. The structured file itself is more likely a useful systems device than a big conceptual novelty. |
| Multi-project hierarchical scheduling graph | Moderate to strong | Tree search and asynchronous queues already exist, but a cross-project hierarchical scheduling graph as the evolution substrate does not appear explicitly in the checked primary sources. |

## What To Frame As Prior Art vs Design Choice vs Likely Contribution

### Prior Art

These should be framed as already established:

- Scientific agents can autonomously propose, test, critique, and refine research outputs.
- Evolutionary or tournament search can improve scientific or algorithmic candidates.
- Multi-model systems can trade off cheap breadth against expensive depth.
- Persistent state or memory can inform future rounds.
- Search budget can be distributed across branches or candidates.

### Design Choice

These are probably best presented as implementation choices unless Catfish has unusually strong ablations:

- Parent-only scoring.
- The exact `Capability.md` file format and update protocol.
- The specific bargaining protocol, unless it can be shown to outperform simpler budget-allocation baselines.

### Likely Contribution

These are the most plausible contribution surfaces:

- Turning competition into an explicit ecological mechanism across agent groups rather than just across hypotheses or programs.
- Selecting not just outputs, but bundled research teams composed of provider/model/agent-group combinations.
- Using capability-state updates and bargaining inside a higher-level multi-project scheduling graph, so that the system evolves organizational structure as well as artifacts.

## Conservative Writing Guidance For A Paper

Safe positioning sentence:

> Prior systems have already demonstrated autonomous AI scientist pipelines, tournament or evolutionary refinement, multi-agent scientific reasoning, and heterogeneous-model search. Catfish therefore should be positioned not as the first evolving AI scientist, but as a new ecological orchestration of evolving scientific agents: it introduces explicit catfish-effect pressure across agent groups, joint selection over team composition and model/provider choice, and a hierarchical scheduler that couples capability updates with resource bargaining across projects.

Claims to avoid:

- "the first evolving AI scientist"
- "the first competitive scientific-agent system"
- "the first multi-model scientific discovery system"
- "the first system to use persistent capability updates in scientific agents"
- "the first system to allocate resources adaptively across research branches"

Claims that are more defensible:

- "a competitive ecological architecture for evolving scientific-agent teams"
- "joint co-evaluation of agent-group composition and model/provider choice"
- "a hierarchical multi-project scheduler for evolving research teams"
- "a systems-level combination of competition, bargaining, capability updates, and cross-project scheduling"

## Sources Checked

Core sources checked from primary materials as of 2026-03-25:

- Lu et al., "The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery," arXiv 2024: [https://arxiv.org/abs/2408.06292](https://arxiv.org/abs/2408.06292)
- Sakana AI, "The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search," arXiv 2025: [https://arxiv.org/abs/2504.08066](https://arxiv.org/abs/2504.08066)
- Google, "Towards an AI co-scientist," arXiv 2025: [https://arxiv.org/abs/2502.18864](https://arxiv.org/abs/2502.18864)
- Google DeepMind, "AlphaEvolve" white paper and official announcement, 2025:
  - [https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/AlphaEvolve.pdf](https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/AlphaEvolve.pdf)
  - [https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/](https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/)
- Yuan et al., "EvoScientist: Towards Multi-Agent Evolving AI Scientists for End-to-End Scientific Discovery," arXiv 2026: [https://arxiv.org/abs/2603.08127](https://arxiv.org/abs/2603.08127)
- Chen et al., "CausalEvolve: Towards Open-Ended Discovery with Causal Scratchpad," arXiv 2026: [https://arxiv.org/abs/2603.14575](https://arxiv.org/abs/2603.14575)
- Du et al., "Accelerating Scientific Discovery with Autonomous Goal-evolving Agents," arXiv 2025: [https://arxiv.org/abs/2512.21782](https://arxiv.org/abs/2512.21782)
- ShinkaEvolve, arXiv 2025: [https://arxiv.org/abs/2509.19349](https://arxiv.org/abs/2509.19349)
- EarthLink: A Self-Evolving AI Agent System for Climate Science, arXiv 2025: [https://arxiv.org/abs/2507.17311](https://arxiv.org/abs/2507.17311)

## Confidence Notes

- Strongest confidence: AlphaEvolve, The AI Scientist, AI Scientist-v2, AI co-scientist, EvoScientist.
- Moderate confidence: CausalEvolve and SAGA as boundary-setting adjacent prior art.
- Lower confidence for direct overlap: EarthLink and ShinkaEvolve are best treated as supporting adjacency references, not the central comparison set.
