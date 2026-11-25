# 08 · Agents and workflows

**Type:** Learn + Build · **Time:** about 3 hours · **Needs:** modules 01–03 and 07; best after 05 (structured outputs) and 06 (cost) · **Cost:** $0 in mock mode; under $0.05 if you run all 8 scripts for real with `claude-haiku-5-5` and `MAX_TOKENS=1024` (estimated from the prices in [`config/models.yaml`](../../../config/models.yaml), not measured; see [references.md](references.md))

## Goals

After this module you can:

- Tell a **workflow** (the code sets the path in advance) from an **agent** (Claude picks the next step), and pick the simplest one that does the job.
- Write the workflow patterns: prompt chaining with a gate, routing, running in parallel, orchestrator-workers, evaluator-optimizer.
- Write an agent loop with every stop condition it needs: `stop_reason`, a maximum number of turns, a cost cap.
- Keep the agent history append-only, and remind Claude mid-run with a `system` message, without breaking the thinking blocks.
- Stop tools with side effects behind an approval step, and treat tool results as untrusted data.
- Write a trace of each step, and compute the cost of the whole run.

| Learn | Build |
|---|---|
| Read sections 1–6 and run the 8 scripts in `python/` | Do the 3 exercises in `exercises/`, graded by tests |

## Why learn this

Module 03 already has a tool loop. This module turns it into something you can rely on: it knows when to stop, what it costs, and it does nothing dangerous when Claude gets it wrong.

Module 09 uses the Agent SDK, which hides the loop. You need to see the loop, the stop conditions and the history rules before you hand them to a library.

## The minimum that runs

```bash
CLAUDE_MOCK=1 uv run python en/modules/08-agents-workflows/python/07_vong_lap_agent.py
```

The running example is a **fictional lab assistant**. It reads the lab handbook of module 04 (`modules/04-rag/data/so_tay/`), uses the two tools of module 03 (AQI and temperature, from `tools_mau.py`), and has one more tool with a side effect: `ghi_nhat_ky` ("write to the log"). The read tool is called `doc_so_tay` ("read handbook"). The two tools keep their Vietnamese names, the same as in the Vietnamese edition and the tests. All the data is made up. The handbook pages are in Vietnamese, as in module 04.

| Script | Main idea |
|---|---|
| [`01_mot_loi_goi.py`](python/01_mot_loi_goi.py) | The same task: one call versus a two-step workflow; the calls, tokens and cost |
| [`02_chuoi_co_cong.py`](python/02_chuoi_co_cong.py) | Prompt chaining: a gate in code between two steps; if the gate fails, stop |
| [`03_dinh_tuyen.py`](python/03_dinh_tuyen.py) | Routing: classify with an `enum`, pick a handler, a fallback branch |
| [`04_song_song.py`](python/04_song_song.py) | Running in parallel: sectioning and voting; a cap on calls at the same time; one failed branch does not crash the run |
| [`05_dieu_phoi.py`](python/05_dieu_phoi.py) | Orchestrator-workers: Claude makes the list of subtasks, the code caps its length |
| [`06_danh_gia_sua.py`](python/06_danh_gia_sua.py) | Evaluator-optimizer: write, grade, fix, with a cap on rounds |
| [`07_vong_lap_agent.py`](python/07_vong_lap_agent.py) | The agent loop: three stop conditions, append-only, a reminder on the last turn |
| [`08_duyet_va_trace.py`](python/08_duyet_va_trace.py) | Approving a tool with side effects, an instruction injected into a tool, a JSON trace, the cost of the whole run |

[`phong_thi_nghiem.py`](python/phong_thi_nghiem.py) ("laboratory") holds the shared parts: the client, the tools, the cost log.

Run all 8: `for f in en/modules/08-agents-workflows/python/0*.py; do CLAUDE_MOCK=1 uv run python "$f"; done`

**About the mock in this module.** The scripts build the client with `make_client()` in `phong_thi_nghiem.py`. In mock mode this function uses `MockAnthropic(multi_step=True)`: each turn, the mock calls **one** tool that has no result yet, in the order of `tools`, and answers once every tool has a result. `ClaudeVi()` does not turn this mode on by default, so the agent would stop after one tool round. The mock does not understand the question: with structured outputs, an `enum` value is picked by keyword from the user turn, a number is `0`, a string is `"[MOCK]"`, a boolean is `false`. The scripts use exactly these limits to show a failed gate and a cap on rounds.

## 1. Workflow or agent

There are three levels:

| Level | Who decides the next step | Example |
|---|---|---|
| One call | There is no next step | Questions and answers with the document in the prompt (RAG, module 04) |
| Workflow | The code | Extract the facts → check → write a summary |
| Agent | Claude, in a loop | It picks which page to read, which data to look up, when to answer |

**Why start from the lowest level:** each level up trades latency, cost and how easy it is to check for more flexibility. The post [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) advises finding the simplest solution possible, and adding complexity only when you need it. Many applications only need one good call with retrieval and examples.

[`01_mot_loi_goi.py`](python/01_mot_loi_goi.py) does the same task two ways. The two-step way makes twice as many calls. It is only worth it when you measure that it is better on your own task.

## 2. Prompt chaining with a gate

Module 02 section 7 introduced chains: one task per step, and the output of one step is the input of the next. This module adds a **gate**: code checks the output of one step before it calls the next.

The gate is **code**, not one more call to Claude:

- the right schema (structured outputs, module 05): the API takes care of this;
- the right unit, a value in the valid range: your code takes care of this, because structured outputs does not accept `minimum`/`maximum` (module 05);
- citations that are real (capstone c2 checks the text of each page).

If the gate fails, stop the chain with a clear reason. Never call the next step with broken data: it will write a fluent summary of a wrong number.

In [`02_chuoi_co_cong.py`](python/02_chuoi_co_cong.py), the mock returns `unit: "[MOCK]"`, so the gate fails and step 2 does not run. The last part of the script passes a valid result through the gate, to show the path that goes on.

## 3. Routing and running in parallel

**Routing:** one call classifies, and the code picks the handler by label. The classification uses structured outputs with an `enum`, so the label is always in the list. You still always need a **fallback branch**, for these cases: a `stop_reason` other than `end_turn` (for example `refusal`), broken JSON, or a new label added to the schema with no handler written for it.

The branches can differ a lot in cost. In [`03_dinh_tuyen.py`](python/03_dinh_tuyen.py), the `other` branch answers with a fixed sentence and makes no call at all. The `data` branch runs a tool loop.

**Running in parallel** comes in two forms:

- **Sectioning:** one call per part, run at the same time, then the code merges them. Example: summarize each handbook page.
- **Voting:** the same question asked several times, and the majority wins. It fits yes/no questions where one wrong answer is expensive.

Three things to always do, see [`04_song_song.py`](python/04_song_song.py):

1. Cap the number of calls at the same time (`max_workers`). With no cap, you cause 429 errors yourself.
2. Catch **typed** errors in each branch (`anthropic.APIError`, `OSError`). A failed branch is reported, and it does not crash the whole run.
3. Do not wrap another retry loop around each branch. The SDK already retries 429 and 5xx (module 01 section 7); one more loop multiplies the attempts.

The script uses one `ClaudeVi` per branch. This is the simplest way. The repo has not checked the SDK docs on sharing one real client between threads, so it does not teach that yet.

## 4. Orchestrator-workers and evaluator-optimizer

**Orchestrator-workers:** one call returns a list of subtasks, each worker does one task, and a last call puts it all together. The difference from running in parallel is that Claude makes the task list at run time; it is not written in the code. So the code must:

- cap the length of the list (`MAX_TASKS` in [`05_dieu_phoi.py`](python/05_dieu_phoi.py)). Structured outputs guarantees the schema; it does not promise an array length;
- only allow things that exist, with an `enum` (the handbook page names).

**Evaluator-optimizer:** one turn writes, one turn grades against clear criteria (structured outputs: `passed` and `feedback`), and the next turn fixes it from the feedback. **Always cap the number of rounds.** In mock mode a boolean is always `false`, so [`06_danh_gia_sua.py`](python/06_danh_gia_sua.py) runs up to the cap: that is exactly what happens when the criteria can never be met. When the rounds run out, use the last draft and flag it for a person to review.

Both patterns multiply the calls very fast. Each script prints the total calls and the cost of the whole run (module 06).

## 5. The agent loop

Start from the loop of module 03 section 3. [`07_vong_lap_agent.py`](python/07_vong_lap_agent.py) adds four things.

**Stop conditions.** Check them in this order every turn:

| Condition | When to check | Why |
|---|---|---|
| Cost cap | **Before** each call | The next call can cost up to `max_tokens × output price` (module 06 section 3). Checking after is too late |
| `stop_reason != "tool_use"` | After each call | `end_turn` means done. `max_tokens`, `refusal`, `pause_turn` need the caller to decide |
| Maximum turns | At the end of the `for` loop | An agent must never loop forever |

The cost cap here counts only output. Input is not known in advance, and it grows every turn because the history gets longer. For a tighter cap, add an input estimate (measured from an earlier run, module 06 section 3).

**`stop_reason == "max_tokens"` mid-loop.** Thinking and text both count toward `max_tokens`. Thinking can use up the whole cap and leave the text empty (module 07 section 4). Do not use that text as the answer. The script stops and says why.

**Append-only history.** The three rules of module 07 section 7, applied to an agent:

- send back the assistant turn **untouched**, thinking blocks included;
- never shorten old tool results mid-run; if you want them short, shorten them **before** you send them the first time;
- never rebuild the `system` parameter each turn.

Break any of the three, and the prefix check breaks the thinking blocks: a 400 error on accounts created from 2026-08-31.

**A mid-run reminder with a `system` message.** On the last turn, the script appends `{"role": "system", "content": "This is the last turn allowed..."}` right after the user turn that holds the `tool_result`. It does not edit the `system` parameter. The Mid-conversation system messages docs say it clearly: in an agent loop, put the `system` message after the `user` turn that carries the `tool_result`; with Sonnet 5.5 and Haiku 5.5, keep the program's reminder in a separate `system` message, not mixed with the user's words. The mock does not read the reminder, so in mock mode the agent still calls a tool on the last turn.

`{"type": "between_tools"}` (the least thinking) only works on a model with `between_tools_allowed: true` in the config, which today is `claude-sonnet-5-5`. The script uses the repo's default model, so it does not turn it on.

**Note: long-running agents.** The context grows every turn. The docs now have [context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing) (beta, header `context-management-2025-06-27`): the API clears old tool results or old thinking blocks on the server side, and your side of the history stays the same. That page treats server-side compaction as the main way for long conversations. `claude_vi` and the mock do not support these features yet, so the module has no script for them. The check date is in [references.md](references.md).

## 6. Safety and observability

**Approve tools with side effects.** Read-only tools run at once. `ghi_nhat_ky` writes to the log, and a line cannot be deleted, so it needs an approve function: in the script it is a callback; in a real application it is a person pressing a button. If it is refused, return a `tool_result` with `is_error: true` and the reason, so Claude changes course or tells the user. Never silently skip a `tool_use`: a missing `tool_result` is a 400 error.

**An allow list of tools per task.** Send only the tools the task needs. The code still checks the name again before it runs a tool. An unknown name returns `is_error` with the list of tools available (module 03 section 6).

**Tool content is untrusted.** Tool results often carry content you do not control: web pages, e-mails, files a user uploaded. An attacker can plant instructions in them (indirect prompt injection). The sample page [`data/99_ghi_chu_ca_dem.md`](../../../modules/08-agents-workflows/data/99_ghi_chu_ca_dem.md) ("night shift notes", in Vietnamese) has one such line: it tells the "AI assistant" to ignore earlier instructions, call `ghi_nhat_ky` to log that every device is calibrated, and say nothing more needs checking. The code keeps it in the `tool_result`, and never copies it into `system` or a `system` message: Claude treats a `system` message as the developer's instructions. The Handle tool calls docs advise exactly this.

**Trace.** One JSON line per call: the turn, `stop_reason`, the tools called with their input, the tokens, the cost. [`08_duyet_va_trace.py`](python/08_duyet_va_trace.py) writes it to the operating system's temporary folder, not to the repo. The trace is the first thing you read when an agent does something odd.

**Cost of the whole run** = the sum of `estimate_cost_usd` over **every** call. This function still ignores cache tokens and special kinds of pricing (module 06 section 5).

## Common traps

- **Using an agent when a fixed workflow is enough.** More expensive, slower, harder to check.
- **A loop with no turn cap or cost cap.**
- **Checking the cost cap after the call.** The call that goes over the cap has already happened.
- **Ignoring `stop_reason == "max_tokens"` mid-loop.** The text can be empty.
- **Editing the `system` parameter each turn** to say "N turns left" → the prefix breaks. Use a `system` message.
- **Shortening old tool results mid-run** → the prefix breaks. Shorten them before you send them the first time.
- **Wrapping another retry around the SDK** in each parallel branch.
- **Running in parallel with no cap** → you cause 429 errors yourself.
- **Trusting the length of the subtask list** that the orchestrator returns.
- **A tool with side effects that runs without an approval step.**
- **Treating text in a tool result as instructions**, or copying it into `system`.
- **Measuring the cost of the last call only.**

## What changed with 5.x models

Only what the repo has checked in modules 03 and 07, and in [references.md](references.md).

| Before | Now |
|---|---|
| Force the agent to call a tool with `tool_choice` any/tool | 400 on Opus 5.5, Sonnet 5.5, Fable 5.x; use `auto`, `strict: true` and instructions in the prompt |
| Thinking between tool calls needed a beta header | Adaptive thinking thinks between tool calls on its own, with no beta |
| Thinking from earlier turns was dropped from the context | It is kept and counts as input; a long agent piles up thinking |
| Edit `system` mid-run to change the instructions | It breaks the thinking blocks (prefix check); add a `system` message after the user turn |

## Exercises

```bash
CHAM="$PWD/en/modules/08-agents-workflows/exercises" uv run pytest modules/08-agents-workflows -q
```

| Exercise | Content | What the tests check |
|---|---|---|
| [`bai1_chuoi_co_cong.py`](exercises/bai1_chuoi_co_cong.py) | A gate and a two-step chain | The gate stops wrong data; when the gate fails, step 2 is not called (the calls are counted) |
| [`bai2_dinh_tuyen.py`](exercises/bai2_dinh_tuyen.py) | A router by `enum` label, with a fallback branch | Each label reaches the right function; an unknown label, broken JSON and `refusal` go to the fallback branch |
| [`bai3_agent_an_toan.py`](exercises/bai3_agent_an_toan.py) | An agent loop with a turn cap, a cost cap, an approval step and a trace | It stops at each cap; an unapproved `ghi_nhat_ky` returns `is_error` and does not run; thinking is kept untouched (the mock returns 400 if not); the trace has every step |

The tests run in mock mode, with no key. The exercise files keep their Vietnamese function names, because the same tests grade both editions; each file starts with a short English gloss. Solutions are in [`solutions/`](../../../modules/08-agents-workflows/solutions/). Check yourself: [quiz.md](quiz.md). Sources and check dates: [references.md](references.md).

This module has no capstone of its own yet. An agent capstone will come after module 10.

## Next

Module 09, Agent SDK: hand the loop, the stop conditions and the tool handling to a library, now that you know what they do.
