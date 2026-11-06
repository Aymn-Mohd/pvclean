# Research Playbook: Claude + <gpu-host> + Mac

How Ayman runs a research project with Claude (chat), Claude Code on the <gpu-host> and Claude Code on the Mac. It is based on the Maritime-C paper (Sept to Oct 2026): a robustness study with 138 queued GPU jobs, 0 failures, five pre-registered extension phases, and one LaTeX source built into both a conference and a journal paper.

Use this file in three ways:
1. Copy it into every new research repo as `docs/RESEARCH_PLAYBOOK.md`.
2. Paste section 16 (the CLAUDE.md templates) into the repo's `CLAUDE.md` on each machine.
3. When you start a project with Claude (chat), attach this file and say "work the Maritime-C way".

---

## 1. The three roles

| Who | Machine | Job | Never does |
|---|---|---|---|
| Claude (chat, in the Project) | cloud | Plans the study: research questions, hypotheses, metrics and decision rules. Writes every Claude Code prompt. Reads reports and interprets them. Writes and builds the paper. Checks references (with Anara). Keeps the project docs current. | Runs GPU jobs. Types numbers into the paper. |
| Claude Code on the <gpu-host> | Ubuntu 22.04, i7-13700HX, RTX 4070 Laptop 8 GB, 32 GB | Runs everything heavy: training, evaluation, scoring and benchmarks, all through the queue. Commits and pushes results. Writes summaries and final reports. | Changes a pre-registered rule after the fact. Commits checkpoints. Runs alongside Isaac Sim on the GPU. |
| Claude Code on the Mac | macOS | Light analysis on CPU, CPU-only reruns, plots. Collects results from git (or the <gpu-host> over scp) and packs upload zips. Checks the <gpu-host> over SSH. | Training. Editing the <gpu-host>-runs branch. |

How data moves:

```
             prompts                     prompts
Claude chat ─────────► <gpu-host> Claude Code   Mac Claude Code ◄──── Claude chat
     ▲                    │  git push (<gpu-host>-runs)  ▲  │
     │                    └──────────► GitHub ─────┘  │ upload zip (MANIFEST + sha256)
     │  pasted report / attachment                     │
     └─────────────────────────────────────────────────┘
```

The loop:
1. Claude chat writes a prompt.
2. You paste it into Claude Code on the <gpu-host> or the Mac.
3. That machine runs the work, pushes it, and prints a report in a fixed format.
4. You paste the report back, or attach the zip.
5. Claude chat interprets the results, updates the project docs, and writes the next prompt.

Keep it to one consolidated report per phase, not a round trip for every small decision.

---

## 2. Non-negotiable principles

1. **Pre-register before running.** Each experiment's hypothesis, metric, decision rule and caveats go into `notes/decisions.md` as their own commit, before its job file moves into the queue. If the commit came after the job started, the result is post hoc.
2. **Freeze before the held-out data.** Freeze corruption parameters, model lists and recipes before any evaluation on test data. Never retune anything to pass a gate. If a gate fails, report it, then pivot or park the project.
3. **Generate every number.** Paper numbers come only from macros that a script writes from result files. Never type a number into prose or a table. If a value is unknown, use a visible `\todo{}` marker, and remove the marker only by regenerating.
4. **Label everything:**
   - `MAIN` for the pre-registered main study;
   - `EXTENSION` for a pre-registered follow-up;
   - `ANALYSIS` / `POST HOC` for checks that weren't planned;
   - `DESCRIPTIVE` when n is too small to test.

   Labels must appear in summaries, in table captions and in the paper text.
5. **Report negative and mixed results prominently.** "Not supported" and "inside seed noise" are results. Don't smooth over contradictions. Say both sides (for example, "supported by the rule on the mean, but only 1 of 2 models per model").
6. **Seed noise is the yardstick.** Train several seeds for some architectures. Count an effect only if it is outside the seed range, and set that rule in advance.
7. **Check surprising results before believing them.** Look for pipeline bugs first: overlays, normalisation, dtype and identical-input checks. Only then interpret.
8. **Verify references** against publisher records (Anara MCP). Flag preprints. Drop predatory venues.
9. **Be honest about novelty.** State limits plainly. A limitation, framed well, is a contribution.

---

## 3. Repo layout (template)

```
<project>/
  CLAUDE.md                  # rules for Claude Code on this machine (section 16)
  README.md
  configs/
    *.yaml                   # frozen experiment configs (corruptions.yaml, models.yaml, recipe_v1.yaml)
    queue/                   # job files the runner executes (NN_name.yaml, sorted by name)
    queue_staged/            # drafted jobs, NOT yet pre-registered or queued
  scripts/
    run_queue.py             # the queue runner (section 7)
    train.py  eval.py  score.py
    analyse.py               # main-study analysis -> results/analysis/*.csv/*.md
    analyse_<exp>.py         # one per extension (analyse_e1.py, ...)
    paper_bundle.py          # numbers.tex + tables/*.tex + figures for the paper
    ext_bundle.py            # same for extensions
  notes/
    decisions.md             # pre-registrations and every decision, with commit hashes
    extension_phases.md      # phase plan, GPU-hour estimates, status
    metrics.md               # exact metric definitions
  results/
    logs/queue.log
    queue_state.json         # job states, rc, start/end times
    window_skips.csv         # jobs not started because of a time rule
    stage*_scores_<machine>.csv / *_counts_<machine>.parquet
    analysis/                # <EXP>_summary.md + CSVs (the authoritative numbers)
    figures/  review/  bundle/
  weights/                   # gitignored
  paper/                     # optional; or a separate paper folder handled in Claude chat
  .gitignore                 # *.pth *.pt *.ckpt weights/ data/ results/**/checkpoints/ *.png over 3 MB
```

---

## 4. Git rules

- **Branches.**
  - `main`: code and frozen configs.
  - `analysis-vN`: a tag or branch for the analysis that a paper version uses.
  - `<gpu-host>-runs`: results pushed by the <gpu-host>.
  - `mac-runs`: results from the Mac, if any.
- **Push after every job** that produces results, so nothing lives only on one disk.
- **Pre-registration commits contain only the `decisions.md` change.** Use the message `prereg: <phase> (<exp ids>)`.
- **Never commit checkpoints or datasets.** Keep `.gitignore` strict. If a backup commit catches a large file and blocks the push, squash only the local, unpushed commits with the file untracked. Never rewrite pushed history.
- **The Mac reads results through a read-only worktree** (`git worktree add ../<repo>-<gpu-host>-runs origin/<gpu-host>-runs`), never by switching your working branch. Remove the worktree afterwards.
- **Quote the commit hash** in every summary and every bundle MANIFEST, so the paper can say where each number came from.

---

## 5. Project lifecycle

| Stage | Where | Output | Gate |
|---|---|---|---|
| 0 Scoping | Claude chat | Research questions (at most 3 or 4), hypotheses, primary metric, decision rules, model list, datasets, split rules, embedded or other practical limits | You approve it |
| 1 Build and smoke | <gpu-host> or Mac Claude Code | Pipeline, unit tests, a 1-sequence smoke test, a reproduction of one published number (for example, WaSR on MODS matching the paper within tolerance) | Smoke test passes; the reproduction is within tolerance |
| 2 Freeze | Claude chat + Claude Code | Frozen configs committed, `decisions.md` main pre-registration, test seeds fixed (`image_seed(0, path)`) | Committed before any test evaluation |
| 3 Main runs | <gpu-host> queue | All main jobs, in slices or overnight | 0 failed; resume test passed |
| 4 Analysis | <gpu-host> or Mac | `analyse.py`, then the summary `.md` and CSVs | Every pre-registered rule applied verbatim |
| 5 Paper bundle | <gpu-host> or Mac | `numbers.tex`, `tables/*.tex`, figures, `RESULTS_MACROS.md`, zip | Every macro is documented |
| 6 Writing | Claude chat | One LaTeX source, conference and journal outputs | Compiles; no TODO markers; numbers only through macros |
| 7 Review | Claude chat (+ external reviews pasted in) | Revision plan, ranked by cost and value | You choose the scope |
| 8 Extensions | <gpu-host> phases | E1, E2, ... each pre-registered, in slices | One report per phase |
| 9 Final | Claude chat | Final PDFs, Overleaf zip, results summary in the Project | Conference text unchanged unless intended (diff the pdftotext output) |

---

## 6. Pre-registration protocol

### 6.1 Entry template (`notes/decisions.md`)

```markdown
## <Phase N>: <E-ids> (<date>)
Status: PRE-REGISTERED (this commit precedes the queue file move)

### <E-id>: <short name>
- Question: <one sentence>
- Runs: <model ids, seeds, recipe; what changes vs baseline>
- Primary metric: <exact definition, image set, denominator>
- Hypothesis H-<id>: <direction and quantity>
- Decision rule: SUPPORTED if <...>; NOT SUPPORTED if <...>; PARTIAL otherwise.
- Effect threshold: an effect counts only if outside <the N-seed range / X points>.
- Primary vs secondary subsets: primary = <...>; secondary/descriptive = <...> (fixed now).
- Bootstrap: cluster by <sequence>, B = 2000, numpy default_rng(0), percentile 95 % CI.
- Caveats known in advance: <confounds, n, one seed>.
- Not tested here: <to stop scope creep>.
```

### 6.2 Rules

- Choose the primary subset before the run. A second subset that only tells the story better afterwards is descriptive. (Lesson: E2b's two real low-light subsets disagreed. Because extra_dark had been fixed as primary in advance, the interpretation stayed honest.)
- A subset under 40 images is "underpowered, descriptive only".
- With 3 models, a rank comparison is descriptive (a random order matches perfectly 1 time in 6).
- A post-hoc check that changes the reading (for example, scene-matched references, or the mean of 5 baseline seeds instead of seed 0) is welcome, but label it POST HOC everywhere.
- A pre-registered primary metric cannot be "demoted" later. Keep it, and add a decomposition next to it.

---

## 7. The <gpu-host> queue system

### 7.1 Runner behaviour (`scripts/run_queue.py`)

- Job files are `configs/queue/NN_<name>.yaml`, run in name order. The runner re-reads the folder after each job, so you can add jobs while it runs.
- Each job has `name`, `cmd`, `kind` (train / eval / score / cpu), `est_hours` and `depends_on`.
- **Exit codes:**
  - `0`: done.
  - `75`: paused at the window end. Not a failure; it resumes next time.
  - Anything else: failed. Log it and continue with the jobs that don't depend on it.
- **Checkpoints** every epoch, keeping the last 2. A resume test is part of stage 1.
- **State files:**
  - `results/queue_state.json` holds the state, rc, start and end times, and hours.
  - `results/logs/queue.log` is the human-readable log.
  - `results/window_skips.csv` lists jobs not started because of a time rule.
- **Runs as a systemd user service** (`maritime-queue` → `<project>-queue`), with `loginctl enable-linger` on, so it survives SSH disconnects and the Mac sleeping.
- **Before any GPU work, check `nvidia-smi`.** If Isaac Sim or another GPU process is running, stop and report. Never share the GPU silently.

### 7.2 Run modes

| Mode | When | Rule |
|---|---|---|
| SLICE (window) | You need the <gpu-host> back in a few hours | `WINDOW_END = slice start + 3h30, rounded down to 5 min`, set automatically. Jobs pause with exit 75 at the window end, and a train job is not started if its estimate doesn't fit. |
| OVERNIGHT (finish what you start) | You are away until a fixed time | No window. No new train job after a cutoff (for example, 10:30 for an 11:00 return). Everything already started runs to completion, even past the cutoff. |
| FULL (no limit) | Weekend or holiday | No window, no cutoff. Remove the override at the end. |

### 7.3 Slice planning

- Estimate job times from the logged durations of similar earlier jobs, not from guesses. (Lesson: MODS evaluation took about 19 min per unit, against 0.6 h estimated for all of it. CPU-bound evaluators break estimates.)
- Each slice is at most 3.5 h, and the first slice should give an early verdict on something.
- Put the job that settles the main hypothesis first, then the long and slow jobs.
- Don't run CPU-heavy evaluation in parallel with training that does on-the-fly augmentation. Both need the CPU.

---

## 8. The Mac's role

- **Collect and pack.** Fetch the results branch into a worktree, copy the listed files, write `MANIFEST.txt` (size, sha256, source commit), and zip as `<project>_<what>_upload_<YYYYMMDD>.zip`.
  - Keep it under 30 MB; downscale PNGs over 3 MB.
  - Use scp from the <gpu-host> only for files missing from git, and never for checkpoints or data.
- **macOS has no `timeout` command.** Don't use it in prompts for the Mac.
- **Light analysis, plots and table checks** on the CPU, plus SSH status checks of the <gpu-host>.
- **The Mac is not always online.** At uni it may have no internet. A <gpu-host> prompt must never depend on the Mac being reachable.

---

## 9. The hand-off loop with Claude chat

What you send back to Claude chat:
- The final report that Claude Code prints, in the format of section 10.F, pasted or as an attachment.
- For writing: the upload zip from the Mac (bundle + summaries + MANIFEST).
- For visual decisions (corruption realism, figures): the review sheet PNG.

What Claude chat does with it, every time:
1. Interprets the verdicts in plain words. Points out mixed and negative results, and anything that looks like a bug.
2. Updates the Project docs (`claude/<project>-results-summary.md`, the revision plan).
3. Writes the next prompt (the next slice, an overnight run, or a sanity check).
4. Says what is left, in GPU hours and writing time.

Tips:
- Say how long the <gpu-host> is free ("free until 3 pm", "away 10 pm to 11 am"). Claude picks the mode and the cutoff.
- Say "set it for me always" and the window end is computed in the prompt, so you never type a time.
- If you need the GPU (Isaac Sim), say so. Claude pauses the queue or plans around it.

---

## 10. Prompt templates (copy, fill in the `<...>`, paste into Claude Code)

### A. New project bootstrap (<gpu-host> or Mac)

````
<Project>: bootstrap. Work without asking me questions; log blockers in notes/decisions.md and continue.
1. Create the repo layout in docs/RESEARCH_PLAYBOOK.md section 3, with .gitignore (checkpoints, weights, data).
2. Write CLAUDE.md from section 16 of the playbook for this machine.
3. Implement scripts/run_queue.py as specified in section 7 (exit 0 / 75 / other, re-read queue/, checkpoint every epoch keep 2,
   window mode via --window-end or env <PROJECT>_WINDOW_END, cutoff mode, queue_state.json, queue.log, window_skips.csv).
4. Install it as a systemd user service <project>-queue; enable linger; test with a 2-minute dummy job, a pause at a window end and a resume.
5. Write notes/metrics.md from my spec below and unit tests for every metric.
Spec: <RQs, metrics, datasets, models>
Report: what was built, the test results, the commit hash.
````

### B. Pre-register and stage a phase

````
<Project>, Phase <N> (EXTENSION). Repo <home>/Desktop/<project>, branch <gpu-host>-runs (HEAD <hash> or later).
Work without asking me questions. If something blocks, write it in notes/decisions.md, skip it and continue.
0. git pull; check the queue is idle and the GPU is free (nvidia-smi). If another GPU process runs, stop and tell me.
1. Pre-registration: add a "Phase <N>" section to notes/decisions.md using the template in docs/RESEARCH_PLAYBOOK.md 6.1, with:
   <E-id, runs, metric, hypothesis, decision rule, primary/secondary subsets, effect threshold>.
   Commit and push it ALONE as "prereg: Phase <N> (<ids>)" before anything moves into configs/queue/.
2. Draft the job files in configs/queue_staged/; estimate each job from logged durations of similar jobs; split into slices of at most 3h30.
3. Move only slice <N>.1 into configs/queue/ (see mode below).
````

### C. Slice run (window mode)

````
MODE = SLICE. WINDOW_END = now + 3h30, rounded down to 5 min; export <PROJECT>_WINDOW_END and print it.
Start the <project>-queue service and confirm in queue.log that it picked up the window.
At the end of the slice: write partial summaries, commit, push, print the report (template F) and the exact command for the next slice.
````

### D. Overnight run (finish what you start)

````
MODE = OVERNIGHT. Unset <PROJECT>_WINDOW_END; set the no-window override. No new train job after <HH:MM>; every started job runs to completion.
Queue <list, in order: the hypothesis-deciding job first>.
At the end: remove the override, final summaries, commit, push, report (template F), leave the queue idle and the GPU free.
````

### E. Full run, no time limit

````
MODE = FULL, no time limit. Unset the window, use the no-window override, no cutoff. Run <everything that remains> to completion.
CPU items run with nice -n 10, at most 2 alongside training. Remove the override at the very end.
````

### F. Report format (end every <gpu-host> or Mac prompt with this)

````
Print a short report:
- jobs done / paused / failed (with rc); anything skipped by a time rule
- each verdict: SUPPORTED / PARTIAL / NOT SUPPORTED / DESCRIPTIVE, with numbers and 95 % CIs, exactly per the pre-registered rule
- POST HOC checks, labelled
- anything surprising, and whether it was sanity-checked
- fixes you made, and why (disclose every deviation)
- GPU hours used; remaining staged jobs with estimates
- commit hash (local == origin?), queue state, GPU state
````

### G. Mac: collect an upload bundle

````
<Project>: collect <what> into one zip for upload. Read-only: don't change the <gpu-host> or any remote branch. macOS has no `timeout`.
1. git fetch origin <gpu-host>-runs; git worktree add ../<repo>-<gpu-host>-runs origin/<gpu-host>-runs (don't switch my branch).
2. Copy: <list of summaries, CSVs, bundle zip, figures, decisions.md>. If missing from git, scp only those files from the <gpu-host>; never checkpoints or data.
3. Pack <home>/Desktop/<project>_<what>_upload_<YYYYMMDD>/ with bundle/, summaries/, figures/, review/ and MANIFEST.txt (size, sha256, source commit).
   If a number I need is not in a summary, compute it with a script from the result CSVs and save it as a .md file; never type it.
4. Zip; if over 30 MB, downscale PNGs over 3 MB to 2400 px wide. Remove the worktree.
5. Print the zip path and size, the file count, the missing / scp'd files, and the key numbers.
````

### H. Analysis-only CPU job

````
<Project>: ANALYSIS items (post hoc, not pre-registered; the primary metric stays primary). Run with nice -n 10.
For each item: definition first in notes/decisions.md under "ANALYSIS items", then the script scripts/analysis_extra.py,
then results/analysis/ANALYSIS_summary.md with every table labelled POST HOC. Items: <list>.
````

### I. Sanity check of a surprising result

````
Sanity check: <result, e.g. model X F1 6.7 vs 68.8 for others>.
1. Render 12 overlays of input, prediction and ground truth. 2. Check normalisation, dtype and value range against the main pipeline.
3. Check that the corruption output is bit-identical to the main pipeline for the same seed. 4. Compare with the same model's result on the main dataset.
Verdict: REAL EFFECT or PIPELINE BUG. If it's a bug: fix it, rerun only the affected units, recompute the verdict, and log it in decisions.md.
````

### J. Paper bundle

````
Generate the paper bundle from results/analysis only:
numbers.tex (one macro per number, readable names, documented in RESULTS_MACROS.md), tables/*.tex (tabular only, booktabs),
figures (PDF, vector, paper labels, not code names). Formats: Q/CE/mCE 1 decimal; rho, tau, R and differences 2 decimals; counts integer;
negatives as $-$; round half up from the summary's printed value. Zip to results/bundle/ with MANIFEST and commit hash.
````

### K. Status check (any time)

````
Status only, change nothing: queue state (running job, elapsed vs estimate, done / failed counts), last 10 lines of queue.log,
nvidia-smi summary, git HEAD vs origin, disk free. Print in 10 lines.
````

---

## 11. From numbers to the paper

- **One source, two outputs.** `\newif\ifjournal` with `main_conference.tex` (`\journalfalse`, IEEEtran conference) and `main_journal.tex` (`\journaltrue`, IEEEtran journal).
  - Put journal-only material in `\ifjournal ... \fi`.
  - When there is too much for the conference version, cut in this order: configuration prose, then secondary figures, then secondary tables, then related-work detail, then results.
- **Inputs:**
  - `preamble.tex` loads `numbers.tex` (main study) and `numbers_ext.tex` (extensions).
  - Tables are `\input{tables/x}` files that hold only the tabular.
  - Figures are generated PDFs.
- **Readable macro names** (`\eFourBDRrealGlitterMean`), not table coordinates (`\eFourBTCRBCD`). Lesson: the auto-generated coordinate macros were unreadable and rounded some values to integers by mistake. Claude chat now regenerates curated macros with its own script from the summary `.md` tables.
- **Round half up** from the printed value (41.55 → 41.6), using Decimal, not float formatting.
- **Signed differences** carry `+`, and prose avoids "fell by −0.20" (write "changed by").
- **Build checks every time:**
  - `pdflatex`, `bibtex`, `pdflatex`, `pdflatex`;
  - 0 overfull boxes and 0 undefined references;
  - page count;
  - `grep TODO` = 0;
  - `diff` of `pdftotext` for the version that should not change;
  - a test compile of the Overleaf zip from scratch.
- **Deliverables:** the PDF(s) + an Overleaf zip (sources, `numbers*.tex`, tables, figures, `ext_data/`, generator scripts) + an updated results summary in the Project.

---

## 12. Writing rules (Ayman's standing rules)

- ASD-STE100 register: short, direct, active sentences in simple tenses, one idea per sentence, each term defined once.
- No em-dashes or en-dashes in prose. Write ranges as "0.59 to 0.88". No bold in the body.
- IEEEtran, at most 6 numbered sections (add subsections, not sections), no ORCID. The affiliation starts with "School of Engineering,".
- Journal abstract of 250 words or fewer (IEEE). The conference abstract can be shorter and kept separate with `\ifjournal`.
- Soften claims to what the data shows ("in our evaluation", "on the available real subsets").
- AI disclosure in the acknowledgment: Claude drafted the text and code, Anara found and checked the literature, and the author verified everything.
- No code release unless decided. If a reviewer asks for one, the middle option is to release configs, image manifests, exclusion lists and parameter tables.
- Address people with title + name ("Dr. Kiyan"). Emails are short and plain, ask for critical feedback, and end with a low-friction next step.

---

## 13. Statistics defaults

- Cluster bootstrap over sequences (not images), B = 2000, `numpy.random.default_rng(0)`, percentile 95 % CI. Resample all models jointly and recompute every score in each replicate.
- Rank agreement: Spearman ρ as primary, Kendall τ-b as secondary, both with bootstrap CIs.
- Relative scores (corrupted / clean) as the primary measure of robustness; absolute scores mostly measure clean accuracy (Miller et al., accuracy on the line).
- Effective robustness: an OLS fit of logit(adverse) on logit(clean); report the residuals.
- Seed noise: at least 2 seeds for 3 architectures in the main study, 5 seeds in a follow-up. Report seed range / between-model range.
- Scene or domain mix: check whether the real subsets differ from the reference in scene type, and post-stratify the reference if they do (lesson: this removed the only "significant" RQ3 result).
- Intervention transfer: as a second validity test, check whether a training change that moves the synthetic score also moves the real score.
- Decompose failure modes into precision vs recall, so the costs are clear (false avoidance vs collision).

---

## 14. Lessons and pitfalls from Maritime-C

1. **Augmentation confounds:** public checkpoints were trained with augmentation that our self-trained models lacked. Check training recipes before you compare model groups.
2. **The implementation can differ from its name:** smp's PSPNet runs only 2.25 M of 24.3 M parameters. Report the parameters that actually run.
3. **TensorRT engine size is not a model-size proxy:** generated kernels inflate it.
4. **TF32 on the GPU breaks bit-exact export checks.** Compare against an fp32 CPU reference.
5. **Tests can be flaky under GPU load:** a test that fails alongside training and passes alone is flaky. Note it in `decisions.md`.
6. **A periodic backup commit can catch checkpoints** and block the push. Keep `.gitignore` strict from day 1.
7. **One cheap post-hoc check can flip a reading:** comparing with seed 0 overstated a gain; the 5-seed mean corrected it. Do this check every time.
8. **Do the bug hunt before interpreting a dramatic result** (SegFormer-B2 collapsing on MODS turned out to be real; check every time anyway).
9. **CPU-bound evaluators break time estimates.** Measure one unit first.
10. **macOS has no `timeout`.** The Mac can go offline. <gpu-host> prompts must stand alone.
11. **A synthetic corruption must also respond to interventions.** If it misses a known effect, the model of the corruption is incomplete (glitter: camera response missing).
12. **Show realism visually before freezing:** make review sheets of synthetic next to real frames, and calibrate parameters on image statistics of data outside the test set, never on model scores.

---

## 15. Checklists

### Before an overnight or full run
- [ ] Hypotheses committed alone (`prereg:` commit) before the queue move
- [ ] `nvidia-smi` is free; no Isaac Sim
- [ ] Mode and cutoff set; override removal written into the prompt
- [ ] The job that decides the main hypothesis is first
- [ ] Disk space checked; checkpoint retention = 2
- [ ] The prompt ends with report template F

### After each phase
- [ ] `<EXP>_summary.md` with labels, job table, verdicts and caveats
- [ ] Pushed; local == origin
- [ ] Results summary in the Claude Project updated
- [ ] Remaining work re-estimated (GPU h, writing h)

### Before sending a paper out
- [ ] 0 TODO markers, 0 overfull boxes, 0 undefined references
- [ ] Every number traced to a macro, and every macro to a results file and commit
- [ ] References verified (Anara); preprints flagged
- [ ] Claims match the data (softened where n is small)
- [ ] Conference page limit met; journal abstract of 250 words or fewer
- [ ] PDF + Overleaf zip (test-compiled from scratch)

---

## 16. CLAUDE.md templates

### <gpu-host> (`CLAUDE.md` in the repo, Ubuntu)

```markdown
# CLAUDE.md (<gpu-host>)
Machine: <gpu-host>, Ubuntu 22.04, RTX 4070 Laptop 8 GB, i7-13700HX, 32 GB. Headless; reached over SSH from the Mac.
Role: GPU executor. All heavy work goes through scripts/run_queue.py and the <project>-queue user service.
Rules:
- Work without asking questions; log blockers in notes/decisions.md and continue with what doesn't depend on them.
- Never move a job from configs/queue_staged/ to configs/queue/ before its pre-registration is committed alone.
- Apply decision rules verbatim. Anything not pre-registered is labelled POST HOC.
- Before GPU work, check nvidia-smi; if Isaac Sim or another GPU process runs, stop and report.
- Never commit checkpoints, weights or data. Never rewrite pushed history.
- Disclose every deviation or fix in decisions.md and in the final report.
- Numbers for the paper are generated only from results/analysis; never typed.
- End every task with the report format in docs/RESEARCH_PLAYBOOK.md 10.F.
Modes: SLICE (WINDOW_END = start + 3h30 rounded down to 5 min), OVERNIGHT (cutoff, finish what you start), FULL (no limit). Remove overrides at the end.
```

### Mac (`CLAUDE.md` in the repo, macOS)

```markdown
# CLAUDE.md (Mac)
Role: light CPU analysis, plots, collecting results and packing upload zips, SSH status checks of the <gpu-host>.
Rules:
- Never train. Never push to <gpu-host>-runs. Read results through a read-only git worktree and remove it after.
- macOS has no `timeout`; don't use it.
- Upload zips: MANIFEST.txt with size, sha256 and source commit; under 30 MB; no checkpoints or data.
- Missing numbers are computed by script from result CSVs and saved as .md; never typed.
- End every task with the report format in docs/RESEARCH_PLAYBOOK.md 10.F.
```

### Claude chat (Project instructions)

```markdown
Work the Maritime-C way (see RESEARCH_PLAYBOOK.md).
- Give me Claude Code prompts for any coding or run work; don't run heavy work yourself.
- Use the Anara MCP for literature and reference checks.
- Pre-register each experiment before it is queued; label EXTENSION / POST HOC / DESCRIPTIVE.
- Interpret every report plainly, including mixed and negative results; update the Project results summary; then give the next prompt and what is left.
- Papers: one source with \ifjournal; numbers only through generated macros; my writing rules (STE100, no dashes, no bold, at most 6 sections).
- Give LaTeX only when I ask for it; otherwise give results and PDFs.
```
