# Skills Usage Guide

Installed globally at `C:\Users\jadha\.config\opencode\skills\`. Restart opencode after install to load.

| Skill | Folder | Install name | Purpose |
|-------|--------|--------------|---------|
| no-ai-slop | `no-ai-slop` | `no-ai-slop` | Edit writing to remove AI slop while preserving voice, or detect slop patterns |
| design-taste-frontend | `design-taste-frontend` | `design-taste-frontend` | Build anti-slop landing pages / portfolios / redesigns with design-system aware code |

Verify:
```powershell
Get-ChildItem $env:USERPROFILE\.config\opencode\skills
# should show: design-taste-frontend, no-ai-slop
```

All skills are invoked with `/` + install name (from frontmatter `name:`). See `SKILL.md:1` in each folder.

---

## 1. /no-ai-slop — `C:\Users\jadha\.config\opencode\skills\no-ai-slop\SKILL.md:1`

**Frontmatter:** `name: no-ai-slop` — *Edit drafts into sharper, more human writing while preserving the writer's personal voice, or detect AI-slop patterns without rewriting.*

Source: https://github.com/petergyang/no-ai-slop — `skills/no-ai-slop/SKILL.md:1` + `eval.md`

### Two jobs (see `SKILL.md:8`)

**A. Edit (default) — minimum effective edit**
```
/no-ai-slop

Paste your draft here...
```
The agent:
1. Reads full draft, identifies core point + voice traits to preserve (`SKILL.md: Workflow 1-2`)
2. Removes 20+ patterns (binary contrasts, throat-clearing, faux-insight, colon reveals, puffery, weasel attribution, etc. — `SKILL.md: Patterns to cut`)
3. Checks against `eval.md`, fixes if any check fails
4. Returns **full edited draft + What changed** section

**B. Detect / audit — no rewrite**
```
/no-ai-slop is this slop? Paste your draft here...
/no-ai-slop audit this draft: ...
/no-ai-slop scan for slop: ...
```
Returns quoted lines + pattern name + 3-word fix. No rewrite, no AI-detector score.

### When it asks follow-ups (`SKILL.md: What to ask for`)
- If no draft provided → will ask to paste it
- If audience/format unclear → *"Who is this for and where will it be published?"*
- If goal unclear → *"What should the reader think/feel/do?"*

### Examples
```
/no-ai-slop The future isn't coming. It's already here. Our cutting-edge platform leverages AI to foster paradigm shifts.

/no-ai-slop is this slop? It's not X. It's Y. Here's the thing: The part everyone misses is distribution.

Draft an AI slop post about productivity   # generates satirical slop (per README)
```

### Patterns it catches (20+)
Binary contrasts, throat-clearing openers, faux-insight setups, colon reveals, dramatic fragments, superficial `-ing` analysis, importance puffery, weasel attribution, synonym cycling, fake-profound endings, em-dash overuse, etc. See `SKILL.md: Patterns to cut` and the README list.

---

## 2. /design-taste-frontend — `C:\Users\jadha\.config\opencode\skills\design-taste-frontend\SKILL.md:1`

**Frontmatter:** `name: design-taste-frontend` — *Anti-slop frontend skill for landing pages, portfolios, and redesigns...*

Source: https://github.com/Leonxlnx/taste-skill — `skills/taste-skill/SKILL.md:1` (v2 experimental, 87k)

> **Scope:** Landing pages, portfolios, redesigns. Not dashboards/data tables/multi-step product UI. Every rule is **contextual** — reads brief first (`SKILL.md:0`).

### Invocation
```
# Greenfield landing/portfolio
/design-taste-frontend Build a SaaS landing for a devtool — Linear-minimal, dark mode, for technical buyers

# Redesign existing
/design-taste-frontend Audit this page first then redesign: [paste code or URL] — preserve brand colors

# With vibe
/design-taste-frontend Portfolio for a creative studio — Awwwards, experimental, playful
```

### Workflow the skill follows

**0. Brief Inference (`SKILL.md:0`)** — agent outputs one line *before coding*:
```
Reading this as: <page kind> for <audience>, with a <vibe> language, leaning toward <design system/aesthetic>
```
If brief ambiguous → asks **one** clarifying question only.

**1. Three Dials (`SKILL.md:1`)** — auto-set from brief, overridable conversationally:
- `DESIGN_VARIANCE: 8` (1=safe symmetry, 10=artsy chaos)
- `MOTION_INTENSITY: 6` (1=static, 10=cinematic)
- `VISUAL_DENSITY: 4` (1=airy gallery, 10=packed cockpit)

Baseline `8/6/4`. Example overrides: `minimalist/calm → 5-6/3-4/2-3`, `playful/Awwwards → 9-10/8-10/3-4`, `public-sector → 3-4/2-3/4-5`.

**2. Design System Map (`SKILL.md:2`)** — picks official package when brief matches:
Microsoft→Fluent, Google→Material 3, IBM→Carbon, Shopify→Polaris, Atlassian→Atlaskit, GitHub→Primer, UK→govuk-frontend, US→USWDS, modern SaaS→shadcn/ui or Tailwind v4. One system per project.

**3. Defaults (`SKILL.md:3`):** React/Next.js RSC, Tailwind v4, `motion/react`, `next/font`, Phosphor/Hugeicons/Radix/Tabler icons (lucide discouraged), never hand-roll SVGs.

**4. Design Engineering (`SKILL.md:4`):** Typography, color (1 accent <80% saturation, no AI-purple default, palette lock), layout, shadows, states (loading/empty/error), a11y, hero/nav/bento rules, image strategy (use image-gen or picsum.photos/real photos — no fake div screenshots).

**5. Motion (`SKILL.md:5`):** Only when dial >5 and brief warrants; Motion `useMotionValue`/`useScroll`, GSAP `ScrollTrigger` with canonical skeletons (`start: "top top"`, `pin: true`), reduced-motion required.

**6-11.** Performance, dial definitions, dark-mode, AI tells, pre-flight checks.

### Pre-flight checks (`SKILL.md:7` etc.)
Hero fits viewport (headline ≤2 lines, subtext ≤20 words), nav single line ≤80px, bento rhythm, eyebrow restraint (≤1 per 3 sections), no duplicate CTA intent, button/form contrast WCAG AA, etc. Failing any = broken.

### Stack it expects
Tailwind v4, Motion (`motion/react`), `next/font`, official design-system package if applicable. Verifies `package.json` before importing any lib (`SKILL.md:3.F`).

---

## General Notes

- **Global vs project:** Installed to `~/.config/opencode/skills/<name>/SKILL.md`. Project-local alternative is `.opencode/skills/<name>/SKILL.md`. Config merged, project overrides global.
- **Not hot-reloaded:** After `SKILL.md` changes, quit and restart opencode.
- **Copy to project (if needed):**
  ```powershell
  Copy-Item -Recurse -Force "$env:USERPROFILE\.config\opencode\skills\no-ai-slop" ".opencode\skills\"
  Copy-Item -Recurse -Force "$env:USERPROFILE\.config\opencode\skills\design-taste-frontend" ".opencode\skills\"
  ```
- **Updating:**
  ```powershell
  # manual re-download (git not required)
  Invoke-WebRequest https://raw.githubusercontent.com/petergyang/no-ai-slop/main/skills/no-ai-slop/SKILL.md -OutFile $env:USERPROFILE\.config\opencode\skills\no-ai-slop\SKILL.md
  Invoke-WebRequest https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/SKILL.md -OutFile $env:USERPROFILE\.config\opencode\skills\design-taste-frontend\SKILL.md
  ```

---

## Quick Reference

```
/no-ai-slop <draft>                          # edit
/no-ai-slop is this slop? <draft>            # detect
/design-taste-frontend <brief>               # build landing/portfolio
/design-taste-frontend redesign: <url/code>  # audit-first redesign
```
