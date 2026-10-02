# Bash wait patterns — never poll with `pgrep -f` in a sleep loop

How to wait for a background process from a Bash tool call, and the one anti-pattern that has already cost the AIGORA a 12-hour stuck turn.

## The gotcha (real incident, 2026-05-17)

A turn launched:

```bash
until ! pgrep -f "python3 scripts/test_live_v5" > /dev/null; do
  sleep 5
done
echo "Done."
```

Intent: wait until the script finishes. Actual behavior: the loop never exits.

Why: `pgrep -f` matches by **full command line**, and the shell that runs this loop is itself `bash -c '... eval "until ! pgrep -f \"python3 scripts/test_live_v5\" ...\""...'`. That bash process has the literal string `python3 scripts/test_live_v5` in its own argv, so `pgrep -f` always finds at least one match (the parent shell itself), so `! pgrep` is always false, so the `until` body runs forever. The real target process can be long-dead; the wait keeps spinning.

Net effect: the Bash tool call never returns, the turn is frozen, and the user sees a tool-call block that stays open indefinitely. Only an out-of-band `kill -TERM` on the loop's PID unsticks it.

## Banned patterns

These two shapes self-deadlock for the reason above. Do not emit them. Ever.

```bash
until ! pgrep -f "<anything>"; do sleep N; done
while pgrep -f "<anything>";   do sleep N; done
```

`guardrail_check.py` blocks these patterns at the hook level. If you see a block message about `pgrep` polling, do not try to work around it. Use one of the correct primitives below.

## Correct primitives

Pick whichever fits the situation.

### 1. Bash tool with `run_in_background: true` (preferred)

This is the AIGORA-native way. The Bash tool accepts a `run_in_background` parameter. You issue the long-running command once, the runtime returns control to you immediately, and you are **automatically notified** when the command completes. No polling, no sleep, no PID juggling.

```
Bash(command="python3 /root/leadgen/scripts/test_live_v5.py", run_in_background=true)
```

When the notification arrives, proceed with the next step. Until then, do unrelated work or wait for the next user message.

### 2. `wait $PID` inside the same Bash call

If you need to chain steps in a single Bash invocation (launch + post-process in one shot), capture the PID with `$!` and wait on it explicitly. This is robust because `wait` is keyed on the actual PID, not on a string pattern.

```bash
python3 scripts/test_live_v5.py &
pid=$!
wait "$pid"
echo "exit=$?"
# post-processing here
```

### 3. Monitor tool for streamed output

If you need to **react** to lines of stdout as the background process runs (progress reports, status events), use the `Monitor` tool — it streams each new stdout line as a notification. Reserve this for cases where you actually need the live stream; for pure "wait until done", `run_in_background` is lighter.

### 4. File-based completion signal (rare)

If the script writes a sentinel file at the end (e.g. `done.flag`), you can poll for that file with `until [ -f done.flag ]; do sleep 5; done`. This is safe because the wait condition has nothing to do with `pgrep`. But it is rarely needed once primitives 1 to 3 exist.

## Anti-patterns to avoid even if not self-deadlocking

- **Tight polling intervals** (`sleep 1` in a loop). Burns CPU and tool-call latency for no benefit. If you must poll, sleep 5 or 10.
- **Sleeping just to "wait for something to settle"** after a quick command. If the next command is dependent, chain them properly (`&&`, or sequential tool calls). If it is independent, do not block.
- **Retry-in-sleep on a failing command** to "let it work eventually". Diagnose the root cause.

## What to do if you find yourself wanting `pgrep -f` polling

Stop. Re-read the situation. One of these is true:

- You launched the process from a prior Bash call without `run_in_background`. → Re-launch it with `run_in_background=true` and let the notification fire.
- The process was launched by something else (a daemon, another turn, a cron). → Use `wait $PID` if you have the PID, or a sentinel file if the script writes one. Do not invent a `pgrep` poll.
- You just want to know if the process is still alive once, not loop. → `pgrep -f "<pattern>"` (single shot, no `until` or `while`) is fine. The danger is only the **looped form combined with `sleep`**.
