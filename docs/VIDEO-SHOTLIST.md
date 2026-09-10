# Assignment 10 video: shot list

One take, about three minutes. OBS, display capture of the terminal and the
browser, mic on. `tools\demo_pipeline.ps1` runs every step with a four-second
pause between them, so there is nothing to type. Read the lines below over the
pauses; they are written to match what is on screen.

Before recording: close everything else, make the terminal font 16 or larger,
and run the script once so Chrome is already warm.

    cd "D:\Side Projects\AI Game Dev Course\rex-machina"
    .\tools\demo_pipeline.ps1

| Time | On screen | Say |
|---|---|---|
| 0:00 | Title line, repo path | "Rex Machina. This is the pipeline that made every line and every number in the game, run end to end. Nothing here is typed; the script runs each stage in order." |
| 0:10 | Step 1, Retry Read | "First, the Retry Read: the line the robot speaks after you lose. A generator drafts it, an evaluator checks it against five rules from the design document, a refiner rewrites from the rule that fired, and a circuit breaker stops a line that will not converge. Six of six first drafts broke a rule. One escalated." |
| 0:45 | Step 2, Copy Desk | "Second, the Copy Desk: the style-guide agent. It scores journey narration out of ten against the house voice and rewrites from the reason. The generator never sees the style guide, so every catch is a break the model made on its own." |
| 1:15 | Step 3, sync | "Now the engine integration. Each table the pipelines wrote is copied into the build byte for byte. The script hashes both ends and refuses to finish if any pair differs. No transform, no hand edit. The bytes the agent wrote are the bytes the game loads." |
| 1:40 | Step 4, tests | "Headless tests play the game without a browser: the fight is winnable from every journey outcome, the robot's veto holds, and every line it speaks is in a generated table." |
| 2:00 | Step 5, QA agent | "The adversarial QA agent re-attempts the six exploits the design document closed, then fuzzes three hundred fights. Fifteen hundred checks. It found three real bugs in an earlier build; they are fixed." |
| 2:25 | Step 6, browser opens | "And the game, loading those exact files. The footer says so: forty-two rows across five tables, unmodified." Press a key or two in Act 1. Then, if time: "Total cost of every model call across every pipeline for the whole capstone: twenty-five cents." |
| 2:55 | Stop | |

Upload unlisted to YouTube or Drive. Paste the link into
`docs/ASSIGNMENT-10-pipeline-audit.md` where it says "see submission", then
`python tools/md2pdf.py docs/ASSIGNMENT-10-pipeline-audit.md`.
