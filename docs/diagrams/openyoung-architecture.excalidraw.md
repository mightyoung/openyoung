---

excalidraw-plugin: parsed
tags: [excalidraw, openyoung, architecture]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==

# OpenYoung System Architecture

## Text Elements
OpenYoung AI Agent Platform ^title

CORE LAYER ^core-title
LLM Providers ^llm
Agent Engine ^agent
Tool Executor ^tools

RUNTIME LAYER ^runtime-title
Sandbox ^sandbox
Evaluator ^evaluator
Tracing ^tracing

HUB LAYER ^hub-title
DataCenter ^datacenter
EvaluationHub ^eval-hub
EvolutionEngine ^evolution
Harness ^harness

SKILLS LAYER ^skills-title
External Sources ^external
Heartbeat ^heartbeat
Package Manager ^pkg-mgr

USER INTERFACE ^ui-title
CLI REPL ^cli
API Server ^api

%%
## Drawing
```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "id": "title",
      "type": "text",
      "x": 400,
      "y": 20,
      "width": 400,
      "height": 40,
      "text": "OpenYoung AI Agent Platform",
      "fontSize": 28,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "top",
      "strokeColor": "#1e1e2e",
      "backgroundColor": "transparent"
    },
    {
      "id": "core-title",
      "type": "text",
      "x": 80,
      "y": 100,
      "width": 120,
      "height": 24,
      "text": "CORE LAYER",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "strokeColor": "#ffffff",
      "backgroundColor": "#1e1e2e"
    },
    {
      "id": "llm",
      "type": "rectangle",
      "x": 40,
      "y": 130,
      "width": 200,
      "height": 80,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#ebfbee",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "llm-txt",
      "type": "text",
      "x": 140,
      "y": 155,
      "width": 200,
      "height": 30,
      "text": "LLM Providers",
      "fontSize": 16,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#2f9e44",
      "backgroundColor": "transparent"
    },
    {
      "id": "agent",
      "type": "rectangle",
      "x": 40,
      "y": 230,
      "width": 200,
      "height": 80,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#ebfbee",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "agent-txt",
      "type": "text",
      "x": 140,
      "y": 255,
      "width": 200,
      "height": 30,
      "text": "Agent Engine",
      "fontSize": 16,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#2f9e44",
      "backgroundColor": "transparent"
    },
    {
      "id": "tools",
      "type": "rectangle",
      "x": 40,
      "y": 330,
      "width": 200,
      "height": 80,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#ebfbee",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "tools-txt",
      "type": "text",
      "x": 140,
      "y": 355,
      "width": 200,
      "height": 30,
      "text": "Tool Executor",
      "fontSize": 16,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#2f9e44",
      "backgroundColor": "transparent"
    },
    {
      "id": "runtime-title",
      "type": "text",
      "x": 320,
      "y": 100,
      "width": 140,
      "height": 24,
      "text": "RUNTIME LAYER",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "strokeColor": "#ffffff",
      "backgroundColor": "#1e1e2e"
    },
    {
      "id": "sandbox",
      "type": "rectangle",
      "x": 280,
      "y": 130,
      "width": 220,
      "height": 80,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#fff3bf",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "sandbox-txt",
      "type": "text",
      "x": 390,
      "y": 155,
      "width": 220,
      "height": 30,
      "text": "Sandbox",
      "fontSize": 16,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#f08c00",
      "backgroundColor": "transparent"
    },
    {
      "id": "evaluator",
      "type": "rectangle",
      "x": 280,
      "y": 230,
      "width": 220,
      "height": 80,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#fff3bf",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "eval-txt",
      "type": "text",
      "x": 390,
      "y": 255,
      "width": 220,
      "height": 30,
      "text": "Evaluator",
      "fontSize": 16,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#f08c00",
      "backgroundColor": "transparent"
    },
    {
      "id": "tracing",
      "type": "rectangle",
      "x": 280,
      "y": 330,
      "width": 220,
      "height": 80,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#fff3bf",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "tracing-txt",
      "type": "text",
      "x": 390,
      "y": 355,
      "width": 220,
      "height": 30,
      "text": "Tracing",
      "fontSize": 16,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#f08c00",
      "backgroundColor": "transparent"
    },
    {
      "id": "hub-title",
      "type": "text",
      "x": 560,
      "y": 100,
      "width": 120,
      "height": 24,
      "text": "HUB LAYER",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "strokeColor": "#ffffff",
      "backgroundColor": "#1e1e2e"
    },
    {
      "id": "datacenter",
      "type": "rectangle",
      "x": 540,
      "y": 130,
      "width": 160,
      "height": 60,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#e7f5ff",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "dc-txt",
      "type": "text",
      "x": 620,
      "y": 147,
      "width": 160,
      "height": 26,
      "text": "DataCenter",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#1971c2",
      "backgroundColor": "transparent"
    },
    {
      "id": "eval-hub",
      "type": "rectangle",
      "x": 540,
      "y": 200,
      "width": 160,
      "height": 60,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#e7f5ff",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "eh-txt",
      "type": "text",
      "x": 620,
      "y": 217,
      "width": 160,
      "height": 26,
      "text": "EvaluationHub",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#1971c2",
      "backgroundColor": "transparent"
    },
    {
      "id": "evolution",
      "type": "rectangle",
      "x": 540,
      "y": 270,
      "width": 160,
      "height": 60,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#e7f5ff",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "evo-txt",
      "type": "text",
      "x": 620,
      "y": 287,
      "width": 160,
      "height": 26,
      "text": "EvolutionEngine",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#1971c2",
      "backgroundColor": "transparent"
    },
    {
      "id": "harness",
      "type": "rectangle",
      "x": 540,
      "y": 340,
      "width": 160,
      "height": 60,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#e7f5ff",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "harness-txt",
      "type": "text",
      "x": 620,
      "y": 357,
      "width": 160,
      "height": 26,
      "text": "Harness",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#1971c2",
      "backgroundColor": "transparent"
    },
    {
      "id": "skills-title",
      "type": "text",
      "x": 760,
      "y": 100,
      "width": 120,
      "height": 24,
      "text": "SKILLS LAYER",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "strokeColor": "#ffffff",
      "backgroundColor": "#1e1e2e"
    },
    {
      "id": "external",
      "type": "rectangle",
      "x": 740,
      "y": 130,
      "width": 160,
      "height": 60,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#f3d9fa",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "ext-txt",
      "type": "text",
      "x": 820,
      "y": 147,
      "width": 160,
      "height": 26,
      "text": "External Sources",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#be4bdb",
      "backgroundColor": "transparent"
    },
    {
      "id": "heartbeat",
      "type": "rectangle",
      "x": 740,
      "y": 200,
      "width": 160,
      "height": 60,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#f3d9fa",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "hb-txt",
      "type": "text",
      "x": 820,
      "y": 217,
      "width": 160,
      "height": 26,
      "text": "Heartbeat",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#be4bdb",
      "backgroundColor": "transparent"
    },
    {
      "id": "pkg-mgr",
      "type": "rectangle",
      "x": 740,
      "y": 270,
      "width": 160,
      "height": 60,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#f3d9fa",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "pkg-txt",
      "type": "text",
      "x": 820,
      "y": 287,
      "width": 160,
      "height": 26,
      "text": "Package Manager",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#be4bdb",
      "backgroundColor": "transparent"
    },
    {
      "id": "ui-title",
      "type": "text",
      "x": 320,
      "y": 440,
      "width": 140,
      "height": 24,
      "text": "USER INTERFACE",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "strokeColor": "#ffffff",
      "backgroundColor": "#1e1e2e"
    },
    {
      "id": "cli",
      "type": "rectangle",
      "x": 280,
      "y": 470,
      "width": 180,
      "height": 60,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#ffe3e3",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "cli-txt",
      "type": "text",
      "x": 370,
      "y": 487,
      "width": 180,
      "height": 26,
      "text": "CLI REPL",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#e03131",
      "backgroundColor": "transparent"
    },
    {
      "id": "api",
      "type": "rectangle",
      "x": 480,
      "y": 470,
      "width": 180,
      "height": 60,
      "strokeColor": "#1e1e2e",
      "backgroundColor": "#ffe3e3",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 0,
      "roundness": {"type": 3}
    },
    {
      "id": "api-txt",
      "type": "text",
      "x": 570,
      "y": 487,
      "width": 180,
      "height": 26,
      "text": "API Server",
      "fontSize": 14,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#e03131",
      "backgroundColor": "transparent"
    },
    {
      "id": "arrow1",
      "type": "arrow",
      "x": 140,
      "y": 210,
      "points": [[0, 0], [0, 20]],
      "startArrowhead": null,
      "endArrowhead": "arrow",
      "strokeColor": "#1e1e2e",
      "strokeWidth": 2,
      "strokeStyle": "solid"
    },
    {
      "id": "arrow2",
      "type": "arrow",
      "x": 140,
      "y": 310,
      "points": [[0, 0], [0, 20]],
      "startArrowhead": null,
      "endArrowhead": "arrow",
      "strokeColor": "#1e1e2e",
      "strokeWidth": 2,
      "strokeStyle": "solid"
    },
    {
      "id": "arrow3",
      "type": "arrow",
      "x": 390,
      "y": 210,
      "points": [[0, 0], [0, 20]],
      "startArrowhead": null,
      "endArrowhead": "arrow",
      "strokeColor": "#1e1e2e",
      "strokeWidth": 2,
      "strokeStyle": "solid"
    },
    {
      "id": "arrow4",
      "type": "arrow",
      "x": 390,
      "y": 310,
      "points": [[0, 0], [0, 20]],
      "startArrowhead": null,
      "endArrowhead": "arrow",
      "strokeColor": "#1e1e2e",
      "strokeWidth": 2,
      "strokeStyle": "solid"
    },
    {
      "id": "arrow5",
      "type": "arrow",
      "x": 620,
      "y": 190,
      "points": [[0, 0], [0, 10]],
      "startArrowhead": null,
      "endArrowhead": "arrow",
      "strokeColor": "#1e1e2e",
      "strokeWidth": 2,
      "strokeStyle": "solid"
    },
    {
      "id": "arrow6",
      "type": "arrow",
      "x": 620,
      "y": 260,
      "points": [[0, 0], [0, 10]],
      "startArrowhead": null,
      "endArrowhead": "arrow",
      "strokeColor": "#1e1e2e",
      "strokeWidth": 2,
      "strokeStyle": "solid"
    },
    {
      "id": "arrow7",
      "type": "arrow",
      "x": 620,
      "y": 330,
      "points": [[0, 0], [0, 10]],
      "startArrowhead": null,
      "endArrowhead": "arrow",
      "strokeColor": "#1e1e2e",
      "strokeWidth": 2,
      "strokeStyle": "solid"
    },
    {
      "id": "arrow8",
      "type": "arrow",
      "x": 240,
      "y": 170,
      "points": [[0, 0], [40, 0]],
      "startArrowhead": null,
      "endArrowhead": "arrow",
      "strokeColor": "#1e1e2e",
      "strokeWidth": 2,
      "strokeStyle": "solid"
    },
    {
      "id": "arrow9",
      "type": "arrow",
      "x": 500,
      "y": 170,
      "points": [[0, 0], [40, 0]],
      "startArrowhead": null,
      "endArrowhead": "arrow",
      "strokeColor": "#1e1e2e",
      "strokeWidth": 2,
      "strokeStyle": "solid"
    },
    {
      "id": "arrow10",
      "type": "arrow",
      "x": 700,
      "y": 170,
      "points": [[0, 0], [40, 0]],
      "startArrowhead": null,
      "endArrowhead": "arrow",
      "strokeColor": "#1e1e2e",
      "strokeWidth": 2,
      "strokeStyle": "solid"
    }
  ],
  "appState": {
    "viewBackgroundColor": "#f8f9fa",
    "gridSize": 20
  },
  "files": {}
}
```
%%
