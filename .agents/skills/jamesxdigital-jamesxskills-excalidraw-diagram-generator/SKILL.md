---
name: excalidraw-diagram-generator
description: Generate Excalidraw diagrams and save them to the Obsidian vault. Use when asked to "create a diagram", "make a flowchart", "visualize a process", "draw a system architecture", "create a mind map", or "generate an Excalidraw file". Saves as .excalidraw.md in the correct Obsidian vault folder with an embedding MD file.
---

# Excalidraw Diagram Generator

Generates Excalidraw diagrams and saves them natively to the Obsidian vault at `~/Documents/obsidian-notes/`.

## Vault File Format (Critical)

Always save as **`.excalidraw.md`** (not `.excalidraw`). Plain `.excalidraw` files require a manual "convert to new version" step in Obsidian before embeds work.

### File structure

```
---

excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==

# Excalidraw Data

## Text Elements
<text content line 1> ^<element-id>

<text content line 2> ^<element-id>

%%
## Drawing
```json
{ ... full Excalidraw JSON ... }
```
%%
```

### Text Elements section

List every text element's content followed by `^<id>` on the same line (matching the element's `id` in the JSON). Multi-line text uses separate lines, with `^id` at the end of the last line:

```
STAGE 1 — BRAIN DUMP ^hdr-title

[ IMAGE ]

Placeholder:
Phone / mic
recording icon ^box1-txt

Speaking is 3× faster than typing ^stat
```

## Save Location

```
~/Documents/obsidian-notes/<project-folder>/excalidraw/<diagram-name>.excalidraw.md
```

After saving, **create or update an embedding MD file** in the project folder:

```markdown
## Stage 1 — Brain Dump

Brief description of what the diagram shows.

![[diagram-name.excalidraw]]
```

Sync after saving: `cd ~/Documents/obsidian-notes && git add -A && git commit -m "Add: <diagram name>" && git push`

## Diagram Types

| User Intent | Type | Keywords |
|-------------|------|----------|
| Process, steps, pipeline | Flowchart | workflow, process, stages, pipeline |
| Connections, components | Relationship | relationship, dependencies, architecture |
| Concepts, hierarchy | Mind Map | mind map, concepts, breakdown |
| Data movement | Data Flow | data flow, data processing |
| Cross-functional | Swimlane | swimlane, actors, responsibilities |

## JSON Element Structure

All elements require these fields:

```json
{
  "id": "descriptive-id",
  "type": "rectangle",
  "x": 0, "y": 0, "width": 200, "height": 100,
  "angle": 0,
  "strokeColor": "#1e1e2e",
  "backgroundColor": "#ffffff",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "roundness": null,
  "seed": 101,
  "version": 1,
  "versionNonce": 101,
  "isDeleted": false,
  "boundElements": null,
  "updated": 1708000000000,
  "link": null,
  "locked": false
}
```

**Text elements** additionally need:

```json
{
  "text": "Label text",
  "fontSize": 16,
  "fontFamily": 5,
  "textAlign": "center",
  "verticalAlign": "top",
  "baseline": 14,
  "containerId": null,
  "originalText": "Label text",
  "lineHeight": 1.25
}
```

**Arrow elements** additionally need:

```json
{
  "points": [[0, 0], [100, 0]],
  "lastCommittedPoint": null,
  "startBinding": null,
  "endBinding": null,
  "startArrowhead": null,
  "endArrowhead": "arrow",
  "roundness": {"type": 2}
}
```

## Key Rules

- **`fontFamily: 5`** (Excalifont) on all text elements — non-negotiable
- **`roughness: 0`** for clean, polished diagrams
- **`strokeStyle: "dashed"`** for placeholder/provisional boxes
- **`roundness: {"type": 3}`** on rectangles for rounded corners
- Use **descriptive string IDs** (e.g. `"hdr-title"`, `"box1-txt"`) — these are preserved on conversion; short IDs like `"bg"` get regenerated
- Multi-line text: use `\n` in the `text` field

## Layout Guidelines

| Item | Value |
|------|-------|
| Horizontal gap between elements | 60–80px |
| Vertical gap between rows | 40–60px |
| Standard box size | 220 × 160px |
| Slide canvas | 1200 × 580px |
| Font size — headings | 22–28px |
| Font size — body | 12–16px |

**Colour palette:**

| Role | Hex |
|------|-----|
| Dark header / bg | `#1e1e2e` |
| Placeholder box fill | `#f8f9fa` |
| Placeholder border | `#adb5bd` |
| Primary (Google green) | `#ebfbee` / `#2f9e44` |
| Alternative (gray) | `#f8f9fa` / `#868e96` |
| White text on dark | `#ffffff` |
| Body text | `#495057` |
| Muted text | `#868e96` |

## Full File Template

```
---

excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==

# Excalidraw Data

## Text Elements
Title text here ^title-id

%%
## Drawing
```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": {
    "viewBackgroundColor": "#f1f3f5",
    "gridSize": 20
  },
  "files": {}
}
```
%%
```

## Checklist

Before saving:
- [ ] File uses `.excalidraw.md` extension
- [ ] Frontmatter present (`excalidraw-plugin: parsed`, `tags: [excalidraw]`)
- [ ] All text elements listed in `## Text Elements` with `^id`
- [ ] JSON wrapped in `%%...%%`
- [ ] All text elements use `fontFamily: 5`
- [ ] No overlapping coordinates
- [ ] IDs are descriptive strings, not single letters
- [ ] Embedding MD file created or updated with `![[filename.excalidraw]]`
- [ ] Vault synced via git
