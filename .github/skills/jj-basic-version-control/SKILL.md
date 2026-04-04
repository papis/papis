---
name: jj-basic-version-control
description: 'Use when doing basic Jujutsu version control in this repo: naming a change with jj describe, finishing a change with jj commit, resuming a change with jj edit, managing release tags with jj tag, managing branch-like pointers with jj bookmark, and turning stacked but independent work into siblings with jj parallelize.'
argument-hint: '[goal, revision, or bookmark name]'
user-invocable: true
---

# JJ Basic Version Control

Use this skill for day-to-day `jj` workflows. Keep the language and commands Jujutsu-native instead of translating back to Git.

## Defaults

- Prefer change IDs over commit IDs when selecting revisions because change IDs stay stable when the commit is rewritten.
- Start with `jj st` and `jj log` so you know what `@` and `@-` refer to before rewriting anything.
- Use `jj describe` to name the current change early.
- Use `jj commit` when you want to finish the current change and immediately continue in a fresh working-copy change.
- Use `jj edit` only when you intentionally want new working-copy changes to amend an existing change directly.
- Use bookmarks for moving branch-like pointers, tags for fixed release markers, and `jj parallelize` only when changes are truly independent.

## Procedure

1. Inspect the current state.
   - Run `jj st`.
   - Run `jj log` or a narrower revset if the graph is busy.
2. Decide whether you are naming the current change or finishing it.
   - If the current change needs a description, run `jj describe -m "message"` or `jj describe`.
   - If the current change is ready and you want a new empty working-copy change on top, run `jj commit -m "message"`.
3. Resume an existing change only when direct amendment is the right choice.
   - Run `jj edit <rev>` to make that revision the working copy.
   - Prefer `jj new` plus `jj squash` instead if you want to review follow-up edits before folding them back in.
4. Manage named pointers deliberately.
   - Use `jj bookmark set <name> -r <rev>` to create or update a branch-like pointer by name.
   - Use `jj bookmark move <name> --to <rev>` when an existing bookmark should advance to a different revision.
   - Use `jj bookmark list` to confirm targets.
   - Use `jj tag set <name> -r <rev>` for a release or milestone marker.
   - Use `jj tag list` to confirm tags.
5. Fix graph shape when stacked changes are actually independent.
   - If change `B` sits on top of change `A` but does not depend on it, run `jj parallelize 'A | B'` or the equivalent revset.
   - Only do this when the revisions should become siblings. If one change depends on the other, keep the stack or use `jj rebase` instead.
6. Verify the result and keep recovery simple.
   - Re-run `jj st` and `jj log`.
   - If the rewrite was wrong, use `jj undo` and inspect history with `jj op log`.

## Decision Points

- Name the current change: use `jj describe`.
- Finish the current change and continue on a fresh one: use `jj commit`.
- Amend an older change directly: use `jj edit <rev>`.
- Create or move a branch-like pointer: use `jj bookmark`.
- Mark a fixed release point: use `jj tag`.
- Convert dependent-looking history into independent siblings: use `jj parallelize`.

## Completion Checks

- The intended revision has the right description.
- The working copy points at the revision you expect.
- Bookmarks or tags point to the intended revision.
- Any parallelized revisions now appear as siblings in `jj log`.
- If the graph looks wrong, recover with `jj undo` before doing more rewrites.