# distill: research shortlist (2026-11-10)

This merges four research scout reports:
- Hofstadter's toolkit,
- information theory,
- knowledge structure,
- measuring fidelity.

It's the menu for a follow-up Q&A or learn session. The design philosophy it serves is in `docs/distill-essence.md`. The scouts said they verified every source by web search, unless an entry says otherwise. That hasn't been re-checked here.

## Where the scouts converged

These came up independently in two or more reports, so they are the strongest signals.

1. **Some recall comes from the model's memory, not the pyramid.** LLMs already know Mill and GEB. Every test needs:
   - a **no-pyramid baseline**, run once with title only and once with a shuffled pyramid, reporting the pyramid's **lift** over it;
   - **canary claims**: altered claims planted in a copy of the pyramid, so recovering the original wording exposes memory use;
   - a pilot on a **post-cutoff or obscure text** before GEB.

   Raised by the Hofstadter (GEB Ch. VI), information theory and fidelity scouts.
2. **Generativity can be tested as held-out prediction.** Build from part of the source, then test on the rest. This generalises the Mill summary redaction. Three ways to score it:
   - judge the predicted content;
   - measure bits saved under a language model;
   - check how the pyramid applies to new cases.

   Hofstadter's version: an interpretation is right if its *new* theorems come out true (isomorphism), and Letter Spirit generates the rest of an alphabet in the spirit of a few seed letters. Raised by all four scouts.
3. **Purpose should be a declared parameter.** A pyramid would state its purpose: what it preserves and for whom. Sources:
   - *Le Ton beau de Marot*: a family of translations, each with declared constraints;
   - the information bottleneck: essence is defined by the target Y;
   - Kolmogorov structure functions: the split between model and noise is underdetermined until the purpose is fixed.

   That last point explains why the extractors disagreed, 64 vs 41 core claims. Parallel hierarchies over one source (the 4+1 architecture views; Lerdahl & Jackendoff on music) make "several pyramids per source" concrete.
4. **Schema: a minimal fixed core plus a declared vocabulary.**
   - The fixed core: anchors, one generic "built-from" upward relation with a `how`, one lateral relation, and the faithfulness and acyclicity rules.
   - Argument types, RST relations and plot units become *vocabularies* a pyramid declares.
   - Extract-Define-Canonicalize can induce the vocabulary: invent types, define them, merge near-duplicates.
   - Kintsch & van Dijk's macrorules (delete, generalize, construct) are a genre-independent operator set.

   This is backed by Hofstadter's critique that the representation *is* the cognition.
5. **Form can be partly checked by machine.** A `form` node kind or layer could carry checkable predicates (palindrome, acrostic, meter), plus a generation task scored by the same predicate. For code, form is the architecture: Parnas's hidden decisions and reflexion models.

## Contradictions with the current spec

From the Hofstadter scout. Each one is a decision for later, not a bug.

| Spec | Tension |
|---|---|
| §2, §7: claims are true/false atoms | A GEB pyramid could score 100% while losing the Crab Canon |
| §4–5: loops are `circular` defects; edges are acyclic | GEB's thesis is a tangled hierarchy. A legitimate level-crossing needs its own representation |
| §1: one pyramid per source | *Le Ton beau*: a declared family beats any single rendering |
| §3–4: node and basis types fixed before reading | The representation-building critique (Chalmers, French & Hofstadter, 1992) |
| §1: higher nodes as typed operations | The Ant Fugue: emergent ideas may not follow from their parts in one typed step |
| §1: the author's structure, faithfully | *Surfaces and Essences*: essence is what a competent reader recognises |
| §5: fan-in ≤ 7 | Cowan (2001): working memory is about 4 chunks. Maybe 4 in human mode |

## Non-judge metrics (the information theory scout)

These need an **open-weight model run locally** that returns log-probabilities for supplied text. The scout believes the Claude API doesn't expose them; not yet confirmed.

**Notation:**
- **S** is the source and **P** is the pyramid's canonical store.
- **C** is the claim set: the extracted claims, each with a weight.
- **L(x | y)** is the length in bits of x when y is supplied first, i.e. −Σ log₂ p(tokens of x | y) under a fixed model.

| Metric | Recipe | Main weakness |
|---|---|---|
| Storage ratio | xz(P) / xz(S), plus token ratio. Needs no model | Ignores fidelity |
| Bits explained | [L(S) − L(S \| P)] / L(S) | Dominated by wording; memory inflates it |
| Idea bits explained | The same, but on the claim set or a neutral paraphrase of the source | Inherits the extractors' instability |
| Two-part MDL | [L(P) + L(S \| P)] / L(S) < 1 means the pyramid "pays for itself" | As above |
| Per-node value | Change in L(C \| P) when one node is removed. Finds dead or duplicate nodes | One pass per node |
| Held-out generativity | Bits saved on section k+1, given a pyramid built from sections 1..k | Tests prediction, not deep generativity |
| Teaching-order cost | Σ L(node_i \| nodes before it), compared across orders | A model's ease isn't a human's |
| Empirical rate-distortion curve | Weighted recall loss against pyramid size, at several prune levels. Find the knee. Needs the LLM judge | Weights are a choice |

**Size expectation:**
- **Linear growth is the realistic best case.** At "lossless at `supporting`", the claims scale with the source.
- **Savings come from dropping wording and repetition,** so long, repetitive books compress best.
- **Compare compressed sizes.** Measure the canonical store, xz against xz. YAML keys almost vanish under compression.

## Making LLM judges trustworthy (the fidelity scout)

- **Weights from agreement.** Run 3 or more extractors and weight each claim by how many include it (Nenkova & Passonneau's Pyramid method, 2004, unrelated to distill's pyramid). This addresses the 64 vs 41 split.
- **A reliability score.** Track Krippendorff's alpha (ordinal) on weights and on judge verdicts, and set a minimum before targets count.
- **Atomic facts** (as in FActScore) instead of "partial = 0.5".
- **Confidence intervals on every recall figure.** At n≈148, a 95% interval is about ±4–5 points. Prediction-powered inference can combine a small human gold set with cheap automatic labels.
- **Calibrate the judge:**
  - use a judge from a different model family;
  - randomise the order of candidate matches;
  - hand-check about 50 verdicts per milestone.

  Reason: LLM judges favour their own model's output (Panickssery et al., 2024).
- **Pre-screen with a small consistency model.** A small NLI or alignment model (e.g. AlignScore) settles the clear cases cheaply, and only uncertain ones go to the LLM.
- **A QA test for answerability.** Generate questions from the cached claim set and answer them from the pyramid on a node budget.
- **Recall by source position and node depth** (FABLES found summarisers over-weight the end of a book).

## Learning (feeds learn and teach)

- **Knowledge space theory** (Doignon & Falmagne). Is a basis the same as a prerequisite? It's the formal home for per-node learner confidence.
- **Teaching-order cost and compression progress** (Schmidhuber). The "shortest path to the apex" becomes something you can measure.
- **Equivalent-learner tests.** Compare normalised gain on pre/post tests, using equivalence testing (TOST) rather than "no significant difference".
- **Concept maps** (Novak). Open-ended link labels, used in education.

## Suggested first picks

Picked for cost against payoff:

1. **A contamination baseline on Mill.** Run the regenerator with no pyramid and report the lift. It's cheap, and every later number depends on it.
2. **Storage ratio (xz) and anchors as pointers.** No model needed. Goes with the ROADMAP item.
3. **Weights from agreement plus alpha on the cached claim sets.** Fixes the instability the targets rest on.
4. **A held-out generativity test.** The first concrete step toward the ideal test.
5. **A declared `purpose` field in the manifest.** A design discussion before it's an implementation.
6. **A log-prob metrics prototype with a small local model.** The non-judge path. Needs a decision on which model.

The rest (schema induction, form layer, legitimate loops, the Toulmin/Walton/DF-QuAD fit for strength) are bigger design threads for the Q&A session.

## Key sources by topic

- **Hofstadter:**
  - *GEB* (1979): Ch. IV on isomorphism, Ch. VI on the location of meaning, Ch. X on levels and the Ant Fugue.
  - *Metamagical Themas* (1985).
  - *Fluid Concepts and Creative Analogies* (1995).
  - *Le Ton beau de Marot* (1997).
  - *I Am a Strange Loop* (2007).
  - *Surfaces and Essences*, with Sander (2013).
  - Chalmers, French & Hofstadter, *JETAI* (1992).
  - Mitchell, *Analogy-Making as Perception* (1993).
- **Information theory:**
  - Rissanen (1978); Grünwald, *MDL* (2007).
  - Li & Vitányi (2019).
  - Vereshchagin & Vitányi (2004); Gell-Mann & Lloyd (1996).
  - Shannon (1951, 1959); Blau & Michaeli (2019).
  - Tishby et al. (1999).
  - Xu et al., V-information (2020).
  - Delétang et al., "Language Modeling Is Compression" (2024).
  - Shi et al., Min-K% Prob (2024).
  - Schmidhuber (2009); Voita & Titov (2020).
  - Vasilyev et al., BLANC (2020).
- **Structure:**
  - Toulmin (1958); Walton, Reed & Macagno (2008).
  - Rago et al., DF-QuAD (2016); Baroni, Rago & Toni (2019).
  - Kintsch & van Dijk (1978).
  - Mann & Thompson, RST (1988).
  - Novak & Cañas (2008).
  - Cowan (2001).
  - Doignon & Falmagne (1985).
  - Lehnert (1981).
  - Zhang & Soh, EDC (2024); Ganter & Wille (1999).
  - Parnas (1972); Kruchten (1995); Murphy et al. (1995).
  - Lerdahl & Jackendoff (1983).
  - Gentner (1983); Spivak & Kent (2012).
- **Fidelity:**
  - Nenkova & Passonneau (2004).
  - Min et al., FActScore (2023).
  - Wang et al., QAGS (2020); Scialom et al., QuestEval (2021).
  - Zha et al., AlignScore (2023).
  - Zheng et al. (2023); Panickssery et al. (2024).
  - Artstein & Poesio (2008); Krippendorff (2011).
  - Chang et al. (2023); Golchin & Surdeanu (2024); Wu et al. (2024).
  - Kim et al., FABLES (2024).
  - Chakrabarty et al. (2024).
  - Yao et al., COLLIE (2024).
  - Angelopoulos et al., PPI (2023).
