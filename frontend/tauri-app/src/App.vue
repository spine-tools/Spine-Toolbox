<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import {
  ArrowRight,
  BarChart3,
  Check,
  ChevronDown,
  CircleHelp,
  Database,
  FolderOpen,
  GitBranch,
  History,
  Layers,
  LineChart,
  LayoutDashboard,
  Redo2,
  Play,
  Plus,
  Search,
  Save,
  Settings2,
  SlidersHorizontal,
  Sparkles,
  Table2,
  Undo2,
  Upload,
  Wrench,
} from "lucide-vue-next";

const modes = [
  { id: "input", title: "Input data to Excel Results", description: "Import source data and prepare a results workbook.", icon: Upload },
  { id: "excel", title: "Excel to Excel", description: "Transform one workbook into another.", icon: Table2 },
  { id: "plot", title: "Results to Plot", description: "Turn results into a visual report.", icon: BarChart3 },
];

const projects = ["No project loaded", "Demo energy system", "North Sea study"];
const selectedMode = ref("input");
const currentView = ref("workflow");
const selectedProject = ref(projects[0]);
const projectMenuOpen = ref(false);
const scenario = ref("Baseline 2030");
const scenarios = ref([]);
const scenarioMenuOpen = ref(false);
const selectedTool = ref("");
const tools = ref([]);
const toolMenuOpen = ref(false);
const inputFile = ref("energy_model.sqlite");
const dbContent = ref(null);
const excelInputFile = ref("");
const inputSourceMenuOpen = ref(false);
const resultFile = ref("results.sqlite");
const projectLoadError = ref("");
const classicDbEditorStatus = ref("");
const plotReady = ref(false);
const isRunning = ref(false);
const workflowNodes = ref([
  { id: "input", label: "Input data", detail: "", icon: Database, className: "canvas-input", x: 20, y: 52 },
  { id: "stack-card", label: "Stack", detail: "", icon: Layers, className: "canvas-stack-card", x: 210, y: 52 },
  { id: "database", label: "Database", detail: "", icon: Database, className: "canvas-database", x: 400, y: 52 },
  { id: "tool", label: "Tool", detail: "", icon: Wrench, className: "canvas-tool", x: 590, y: 52 },
  { id: "results", label: "Results", detail: "", icon: Table2, className: "canvas-results", x: 780, y: 52 },
]);
const draggingNodes = ref([]);
const dragOrigins = ref({});
const dragStart = ref({ x: 0, y: 0 });
const selectedNode = ref(null);
const selectedNodeIds = ref([]);
const selectedConnection = ref("");
const canvas = ref(null);
const selectionBox = ref(null);
const selectionStart = ref({ x: 0, y: 0 });
const recentRuns = ref([
  { name: "Baseline 2030", status: "Ready", time: "Today, 10:42" },
  { name: "High demand", status: "Ready", time: "Yesterday, 16:08" },
]);

const projectPath = ref("");
const LAST_PROJECT_PATH_KEY = "spinetoolbox:lastProjectPath";
const lastProjectPath = ref(localStorage.getItem(LAST_PROJECT_PATH_KEY) || "");
const workflowConnections = ref([
  ["input", "stack-card"],
  ["stack-card", "database"],
  ["database", "tool"],
  ["tool", "results"],
]);

// Stacks group several canvas nodes (e.g. a Tool + an Exporter) into one collapsible card,
// mirroring how the old Toolbox design view lets you chain multiple items together.
const stacks = ref([]);

function resolveStackEndpoint(nodeId) {
  const owner = stacks.value.find((stack) => stack.collapsed && stack.memberIds.includes(nodeId));
  return owner ? owner.id : nodeId;
}

const canvasNodes = computed(() => {
  const hiddenIds = new Set(stacks.value.filter((stack) => stack.collapsed).flatMap((stack) => stack.memberIds));
  const visibleReal = workflowNodes.value.filter((node) => !hiddenIds.has(node.id));
  const stackNodes = stacks.value.map((stack) => ({
    id: stack.id,
    label: stack.label,
    detail: stack.collapsed ? `${stack.memberIds.length} steps` : "Stack",
    icon: Layers,
    className: "canvas-stack",
    x: stack.x,
    y: stack.y,
    isStack: true,
    stackRef: stack,
  }));
  return [...visibleReal, ...stackNodes];
});

const canvasConnections = computed(() => {
  const seen = new Set();
  const result = [];
  for (const [source, target] of workflowConnections.value) {
    const resolvedSource = resolveStackEndpoint(source);
    const resolvedTarget = resolveStackEndpoint(target);
    if (resolvedSource === resolvedTarget) continue;
    const key = `${resolvedSource}-${resolvedTarget}`;
    if (seen.has(key)) continue;
    seen.add(key);
    result.push([resolvedSource, resolvedTarget]);
  }
  return result;
});

function groupSelectedIntoStack() {
  const members = workflowNodes.value.filter((node) => selectedNodeIds.value.includes(node.id));
  if (members.length < 2) return;
  const x = members.reduce((sum, node) => sum + node.x, 0) / members.length;
  const y = members.reduce((sum, node) => sum + node.y, 0) / members.length;
  stacks.value.push({ id: `stack-${Date.now()}`, label: `Stack (${members.length})`, x, y, memberIds: members.map((node) => node.id), collapsed: true });
  selectedNodeIds.value = [];
  selectedNode.value = null;
}

function toggleStack(stack) {
  stack.collapsed = !stack.collapsed;
}

function ungroupStack(stack) {
  stacks.value = stacks.value.filter((candidate) => candidate.id !== stack.id);
}

async function callBackend(method, params = {}) {
  const request = JSON.stringify({ method, params });
  const response = await invoke("python_bridge_request", { request });
  const message = JSON.parse(response);
  if (!message.ok) throw new Error(message.error);
  return message.result;
}
async function openProjectDialog() {
  try {
    const selection = await openDialog({ directory: true, multiple: false });
    let dir = "";
    if (Array.isArray(selection)) dir = selection[0] || "";
    else dir = selection || "";
    if (!dir) return;
    projectPath.value = dir;
    projectMenuOpen.value = false;
    try {
      await loadProject();
    } catch (e) {
      projectLoadError.value = `Could not load project: ${e.message}`;
    }
  } catch (e) {
    if (window.__TAURI_INTERNALS__) {
      projectLoadError.value = `Could not open native project dialog: ${e.message}`;
      return;
    }
    document.querySelector('#project-picker').click();
  }
}

async function handleProjectPicker(event) {
  const files = event.target.files;
  if (!files || !files.length) return;
  // Try to get a full path from the first File object (available in Tauri/webview).
  const first = files[0];
  let dir = "";
  // Prefer absolute paths exposed via `path` (Tauri); fall back to webkitRelativePath.
  if (first.path) {
    try {
      const p = first.path;
      dir = p.replace(/\\[^\\]*$/, "");
    } catch (e) {
      // ignore
    }
  }
  if (!dir && first.webkitRelativePath) {
    dir = first.webkitRelativePath.split('/')[0];
  }

  // If the selected folder contains a project.json file, read it and send its contents
  // to the backend so we can show project metadata even when absolute paths are not available.
  const fileArray = Array.from(files);
  const projectFile = fileArray.find((f) => f.name === 'project.json' || (f.webkitRelativePath && f.webkitRelativePath.endsWith('project.json')) || (f.path && f.path.endsWith('project.json')));
  projectMenuOpen.value = false;
  if (projectFile) {
    try {
      const text = await projectFile.text();
      const result = await callBackend('project_from_json', { content: text });
      // Populate UI from returned project metadata
      selectedProject.value = result.path || dir || projects[0];
      const dataStores = result.items.filter((item) => item.type === 'Data Store');
      if (dataStores.length) {
        inputFile.value = dataStores[0].database;
        const inputNode = workflowNodes.value.find((node) => node.id === 'input');
        if (inputNode) inputNode.label = dataStores[0].name;
      }
      const toolItems = result.items.filter((item) => item.type === 'Tool' || item.name.toLowerCase().includes('spineopt') || item.name.toLowerCase().includes('flextool'));
      tools.value = toolItems.map((t) => t.name);
      if (tools.value.length && !selectedTool.value) selectedTool.value = tools.value[0];
      recentRuns.value = result.items.filter((item) => item.type !== 'Data Store').slice(0, 4).map((item) => ({ name: item.name, status: item.type, time: 'Project item' }));
      projectPath.value = dir || '';
    } catch (e) {
      projectLoadError.value = `Could not load project: ${e.message}`;
    } finally {
      event.target.value = null;
    }
    return;
  }

  if (!dir) dir = projectPath.value || "";
  projectPath.value = dir;
  try {
    await loadProject();
  } catch (e) {
    projectLoadError.value = `Could not load project: ${e.message}`;
  } finally {
    event.target.value = null;
  }
}

function openProject() {
  selectedProject.value = projects[(projects.indexOf(selectedProject.value) + 1) % projects.length];
  projectMenuOpen.value = false;
}

async function runWorkflow() {
  isRunning.value = true;
  projectLoadError.value = "";
  try {
    const job = await callBackend("start_run", { path: projectPath.value, tool: selectedTool.value, scenario: scenario.value });
    let status = job.status;
    while (status === "starting" || status === "running") {
      await new Promise((resolve) => window.setTimeout(resolve, 500));
      const currentJob = await callBackend("job", { job_id: job.job_id });
      status = currentJob.status;
      if (status === "failed") throw new Error(currentJob.error || "Spine Engine failed");
    }
    recentRuns.value.unshift({ name: `${selectedTool.value} / ${scenario.value}`, status: status === "completed" ? "Ready" : status, time: "Just now" });
  } catch (error) {
    projectLoadError.value = `Run failed: ${error.message}`;
  } finally {
    isRunning.value = false;
  }
}

function openExcelPicker() {
  document.querySelector("#excel-input-picker").click();
}

function chooseInputSource(source) {
  inputSourceMenuOpen.value = false;
  if (source === "database") currentView.value = "database";
  if (source === "excel") openExcelPicker();
}

function closeInputSourceMenu(event) {
  if (!event.target.closest(".canvas-input")) inputSourceMenuOpen.value = false;
  if (!event.target.closest(".canvas-stack-card")) scenarioMenuOpen.value = false;
}

function resetCanvasSelection() {
  selectedNode.value = null;
  selectedNodeIds.value = [];
  selectedConnection.value = "";
}

function clearCanvasSelection(event) {
  if (!event.target.closest(".workflow-canvas")) resetCanvasSelection();
}

function previewPlot() {
  plotReady.value = true;
}

async function importExcel(event) {
  const file = event.target.files[0];
  if (!file) return;
  projectLoadError.value = "";
  excelInputFile.value = file.name;
  try {
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
    const result = await callBackend("import_excel", {
      path: projectPath.value,
      filename: file.name,
      content: btoa(binary),
      data_store: workflowNodes.value.find((node) => node.id === "input").label,
    });
    recentRuns.value.unshift({ name: `Imported ${result.filename}`, status: `${result.imported} items`, time: "Just now" });
    if (result.errors.length) projectLoadError.value = result.errors.join(" ");
  } catch (error) {
    projectLoadError.value = `Excel import failed: ${error.message}`;
  } finally {
    event.target.value = "";
  }
}

async function openDatabase(event) {
  const file = event.target.files[0];
  if (!file) return;
  try {
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
    const result = await callBackend("open_database", { filename: file.name, content: btoa(binary) });
    dbContent.value = result;
    inputFile.value = result.filename || file.name;
  } catch (error) {
    console.error("Open database failed:", error);
  } finally {
    event.target.value = "";
  }
}

async function openClassicDatabaseEditor() {
  projectLoadError.value = "";
  classicDbEditorStatus.value = "Opening classic DB Editor...";
  try {
    const result = await callBackend("open_database_editor", {
      path: projectPath.value,
      data_store: workflowNodes.value.find((node) => node.id === "input").label,
    });
    classicDbEditorStatus.value = `Opened ${result.data_store} in classic DB Editor`;
  } catch (error) {
    classicDbEditorStatus.value = "";
    projectLoadError.value = `Could not open classic database editor: ${error.message}`;
  }
}

function startDrag(event, node) {
  draggingNodes.value = selectedNodeIds.value.includes(node.id)
    ? workflowNodes.value.filter((candidate) => selectedNodeIds.value.includes(candidate.id))
    : [node];
  dragOrigins.value = Object.fromEntries(draggingNodes.value.map((candidate) => [candidate.id, { x: candidate.x, y: candidate.y }]));
  dragStart.value = { x: event.clientX, y: event.clientY };
  window.addEventListener("pointermove", moveNode);
  window.addEventListener("pointerup", stopDrag, { once: true });
}

function moveNode(event) {
  if (!draggingNodes.value.length) return;
  const canvasBounds = canvas.value.getBoundingClientRect();
  const deltaX = event.clientX - dragStart.value.x;
  const deltaY = event.clientY - dragStart.value.y;
  for (const node of draggingNodes.value) {
    const origin = dragOrigins.value[node.id];
    node.x = Math.max(8, Math.min(canvasBounds.width - 140, origin.x + deltaX));
    node.y = Math.max(42, Math.min(canvasBounds.height - 118, origin.y + deltaY));
  }
}

function stopDrag(event) {
  if (Math.hypot(event.clientX - dragStart.value.x, event.clientY - dragStart.value.y) < 5) selectNode(draggingNodes.value[0]);
  draggingNodes.value = [];
  window.removeEventListener("pointermove", moveNode);
}

function startSelection(event) {
  const canvasBounds = canvas.value.getBoundingClientRect();
  inputSourceMenuOpen.value = false;
  resetCanvasSelection();
  selectionStart.value = { x: event.clientX - canvasBounds.left, y: event.clientY - canvasBounds.top };
  selectionBox.value = { ...selectionStart.value, width: 0, height: 0 };
  selectedNode.value = null;
  selectedConnection.value = "";
  window.addEventListener("pointermove", updateSelection);
  window.addEventListener("pointerup", stopSelection, { once: true });
}

function updateSelection(event) {
  const canvasBounds = canvas.value.getBoundingClientRect();
  const endX = event.clientX - canvasBounds.left;
  const endY = event.clientY - canvasBounds.top;
  selectionBox.value = {
    x: Math.min(selectionStart.value.x, endX),
    y: Math.min(selectionStart.value.y, endY),
    width: Math.abs(endX - selectionStart.value.x),
    height: Math.abs(endY - selectionStart.value.y),
  };
}

function stopSelection() {
  const box = selectionBox.value;
  selectedNodeIds.value = workflowNodes.value
    .filter((node) => node.x >= box.x && node.y >= box.y && node.x + 132 <= box.x + box.width && node.y + 108 <= box.y + box.height)
    .map((node) => node.id);
  selectionBox.value = null;
  window.removeEventListener("pointermove", updateSelection);
}

function selectNode(node) {
  if (selectedNode.value && selectedNode.value.id !== node.id) {
    const connection = [selectedNode.value.id, node.id];
    if (!workflowConnections.value.some(([source, target]) => source === connection[0] && target === connection[1])) {
      workflowConnections.value.push(connection);
    }
    selectedNode.value = null;
    inputSourceMenuOpen.value = false;
    return;
  }
  selectedConnection.value = "";
  selectedNode.value = node;
  selectedNodeIds.value = [node.id];
  inputSourceMenuOpen.value = node.id === "input" ? !inputSourceMenuOpen.value : false;
}

function toggleToolMenu() {
  toolMenuOpen.value = !toolMenuOpen.value;
}

function chooseTool(tool) {
  selectedTool.value = tool;
  toolMenuOpen.value = false;
}

function toggleScenarioMenu() {
  scenarioMenuOpen.value = !scenarioMenuOpen.value;
}

function chooseScenario(nextScenario) {
  scenario.value = nextScenario;
  scenarioMenuOpen.value = false;
}

function nodePorts(node) {
  return [
    { x: node.x + 66, y: node.y, dx: 0, dy: -1 },
    { x: node.x + 132, y: node.y + 54, dx: 1, dy: 0 },
    { x: node.x + 66, y: node.y + 108, dx: 0, dy: 1 },
    { x: node.x, y: node.y + 54, dx: -1, dy: 0 },
  ];
}

function connectionPorts([sourceId, targetId]) {
  const source = canvasNodes.value.find((node) => node.id === sourceId);
  const target = canvasNodes.value.find((node) => node.id === targetId);
  return nodePorts(source).flatMap((sourcePort) => nodePorts(target).map((targetPort) => ({ sourcePort, targetPort }))).reduce(
    (nearest, pair) => (Math.hypot(pair.targetPort.x - pair.sourcePort.x, pair.targetPort.y - pair.sourcePort.y) < Math.hypot(nearest.targetPort.x - nearest.sourcePort.x, nearest.targetPort.y - nearest.sourcePort.y) ? pair : nearest)
  );
}

function connectionPath(connection) {
  const { sourcePort, targetPort } = connectionPorts(connection);
  const distance = Math.max(35, Math.hypot(targetPort.x - sourcePort.x, targetPort.y - sourcePort.y) / 3);
  return `M ${sourcePort.x} ${sourcePort.y} C ${sourcePort.x + sourcePort.dx * distance} ${sourcePort.y + sourcePort.dy * distance}, ${targetPort.x + targetPort.dx * distance} ${targetPort.y + targetPort.dy * distance}, ${targetPort.x} ${targetPort.y}`;
}

function selectConnection(connection) {
  selectedNode.value = null;
  selectedNodeIds.value = [];
  inputSourceMenuOpen.value = false;
  selectedConnection.value = connection.join("-");
}

function deleteSelectedConnection(event) {
  if ((event.key === "Delete" || event.key === "Backspace") && selectedConnection.value) {
    workflowConnections.value = workflowConnections.value.filter((connection) => connection.join("-") !== selectedConnection.value);
    selectedConnection.value = "";
  }
}

async function loadProject() {
  projectLoadError.value = "";
  try {
    const project = await callBackend("project", { path: projectPath.value });
    selectedProject.value = project.path;
    if (project.path) {
      lastProjectPath.value = project.path;
      localStorage.setItem(LAST_PROJECT_PATH_KEY, project.path);
    }
    const dataStores = project.items.filter((item) => item.type === "Data Store");
    if (dataStores.length) {
      inputFile.value = dataStores[0].database;
      workflowNodes.value.find((node) => node.id === "input").label = dataStores[0].name;
      const scenarioResult = await callBackend("list_scenarios", { path: project.path, data_store: dataStores[0].name });
      scenarios.value = scenarioResult.scenarios;
      if (scenarios.value.length && !scenarios.value.includes(scenario.value)) scenario.value = scenarios.value[0];
    } else {
      scenarios.value = [];
    }
    // Populate tool list from project items of type 'Tool' or known tool names
    const toolItems = project.items.filter((item) => item.type === "Tool" || item.name.toLowerCase().includes("spineopt") || item.name.toLowerCase().includes("flextool"));
    tools.value = toolItems.map((t) => t.name);
    if (tools.value.length && !selectedTool.value) selectedTool.value = tools.value[0];
    recentRuns.value = project.items
      .filter((item) => item.type !== "Data Store")
      .slice(0, 4)
      .map((item) => ({ name: item.name, status: item.type, time: "Project item" }));
  } catch (error) {
    projectLoadError.value = `Could not load project: ${error.message}`;
  }
}

async function reopenLastProject() {
  if (!lastProjectPath.value) return;
  projectPath.value = lastProjectPath.value;
  await loadProject();
}

onMounted(() => {
  window.addEventListener("keydown", deleteSelectedConnection);
  window.addEventListener("pointerdown", closeInputSourceMenu);
  window.addEventListener("pointerdown", clearCanvasSelection);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", deleteSelectedConnection);
  window.removeEventListener("pointerdown", closeInputSourceMenu);
  window.removeEventListener("pointerdown", clearCanvasSelection);
});
</script>

<template>
  <main class="app-shell">
    <aside class="sidebar">
      <div class="brand-mark"><Sparkles :size="18" /></div>
      <div class="brand-copy">
        <strong>Spine</strong>
        <span>Toolbox</span>
      </div>
      <nav class="nav-list" aria-label="Main navigation">
        <button class="nav-item" :class="{ active: currentView === 'workflow' }" @click="currentView = 'workflow'"><LayoutDashboard :size="18" /> Design view</button>
        <button class="nav-item" :class="{ active: currentView === 'database' }" @click="currentView = 'database'"><Database :size="18" /> Database editor</button>
        <button class="nav-item"><BarChart3 :size="18" /> Results</button>
      </nav>
      <div class="sidebar-bottom">
        <button class="nav-item"><Settings2 :size="18" /> Settings</button>
        <div class="connection-status"><span class="status-dot"></span><span>Python bridge connected</span></div>
      </div>
    </aside>

    <section class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">User mode</p>
          <h1>Good morning<span class="accent">.</span></h1>
        </div>
        <button class="icon-button" title="Help"><CircleHelp :size="19" /></button>
      </header>

      <div v-if="currentView === 'workflow'" class="content-grid">
        <section class="primary-column">
          <div class="project-banner">
            <div class="project-icon"><FolderOpen :size="22" /></div>
            <div class="project-details">
              <span class="field-label">Current project</span>
              <button class="project-selector" @click="projectMenuOpen = !projectMenuOpen">
                {{ selectedProject }} <ChevronDown :size="16" />
              </button>
              <div v-if="projectMenuOpen" class="project-menu">
                <button v-for="project in projects" :key="project" @click="selectedProject = project; projectMenuOpen = false">{{ project }}</button>
              </div>
            </div>
            <div class="project-open-controls"><input v-model="projectPath" class="project-path" aria-label="Project directory" /><button class="secondary-button" @click="openProjectDialog"><FolderOpen :size="16" /> Load project</button><button v-if="lastProjectPath" class="secondary-button" :title="lastProjectPath" @click="reopenLastProject"><History :size="16" /> Reopen last project</button></div>
          </div>
          <p v-if="projectLoadError" class="project-error">{{ projectLoadError }}</p>

          <div class="section-heading">
            <div><p class="eyebrow">Workflow</p><h2>Build your run</h2></div>
            <button v-if="selectedNodeIds.length > 1" class="text-button" @click="groupSelectedIntoStack"><Layers :size="16" /> Group into stack</button>
            <button class="text-button"><Plus :size="16" /> New workflow</button>
          </div>

          <section ref="canvas" class="workflow-canvas" aria-label="Draggable workflow design view" @pointerdown.self="startSelection">
            <div class="canvas-toolbar"><span><span class="canvas-live-dot"></span> Design View</span><small>Drag boxes to arrange your workflow</small></div>
            <svg class="canvas-links" aria-hidden="true" @pointerdown.self="resetCanvasSelection">
              <defs><marker id="connection-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M 0 0 L 8 4 L 0 8 z" /></marker></defs>
              <g v-for="connection in canvasConnections" :key="connection.join('-')">
                <path class="connection-hit" :d="connectionPath(connection)" @pointerdown.stop @click.stop="selectConnection(connection)" />
                <path :class="{ selected: selectedConnection === connection.join('-') }" :d="connectionPath(connection)" marker-end="url(#connection-arrow)" />
              </g>
            </svg>
            <div v-if="selectionBox" class="selection-box" :style="{ left: `${selectionBox.x}px`, top: `${selectionBox.y}px`, width: `${selectionBox.width}px`, height: `${selectionBox.height}px` }"></div>
            <article v-for="node in canvasNodes" :key="node.id" class="canvas-node" :class="[node.className, { selected: selectedNodeIds.includes(node.id) }]" :style="{ left: `${node.x}px`, top: `${node.y}px` }" @pointerdown="startDrag($event, node)">
              <div class="canvas-node-head"><span class="canvas-node-icon"><component :is="node.icon" :size="24" /></span><span v-if="node.detail">{{ node.detail }}</span></div>
              <template v-if="node.isStack">
                <strong @click.stop="toggleStack(node.stackRef)" class="tool-card">{{ node.label }} <ChevronDown :size="14" /></strong>
                <button class="stack-ungroup" title="Ungroup" @click.stop="ungroupStack(node.stackRef)">×</button>
              </template>
              <template v-else>
                <template v-if="node.id === 'stack-card'">
                  <strong @click.stop="toggleScenarioMenu" class="tool-card">{{ node.label }} <ChevronDown :size="14" /></strong>
                  <small>{{ scenario || "Choose scenario" }}</small>
                  <div v-if="scenarioMenuOpen" class="scenario-menu" @pointerdown.stop>
                    <button v-for="item in scenarios" :key="item" type="button" :class="{ active: item === scenario }" @click="chooseScenario(item)">{{ item }}</button>
                    <span v-if="!scenarios.length">No scenarios found</span>
                  </div>
                </template>
                <strong v-else-if="node.id !== 'tool'">{{ node.label }}</strong>
                <template v-else>
                  <strong @click.stop="toggleToolMenu" class="tool-card">{{ selectedTool || node.label }}</strong>
                  <div v-if="toolMenuOpen" class="tool-menu" @pointerdown.stop>
                    <button v-for="t in tools" :key="t" @click="chooseTool(t)">{{ t }}</button>
                  </div>
                </template>
                <template v-if="node.id === 'input'">
                  <div v-if="inputSourceMenuOpen" class="input-source-menu" @pointerdown.stop>
                    <button type="button" @click="chooseInputSource('database')"><Database :size="13" /> Use database</button>
                    <button type="button" @click="chooseInputSource('excel')"><Upload :size="13" /> Choose Excel file</button>
                  </div>
                  <input id="excel-input-picker" class="hidden-file-picker" type="file" accept=".xlsx,.xls" @change="importExcel" />
                  <input id="db-input-picker" class="hidden-file-picker" type="file" accept=".sqlite,.db" @change="openDatabase" />
                  <input id="project-picker" class="hidden-file-picker" type="file" webkitdirectory directory multiple @change="handleProjectPicker" />
                </template>
              </template>
            </article>
          </section>

          <section class="action-panel">
            <div><p class="eyebrow">{{ selectedTool }}</p><h2>Configure your run</h2></div>
            <label class="scenario-field"><span>Scenario</span><select v-model="scenario"><option>Baseline 2030</option><option>High demand</option><option>Low renewables</option></select></label>
            <div class="action-buttons"><button class="plot-button" :class="{ ready: plotReady }" @click="previewPlot"><LineChart :size="16" /> {{ plotReady ? "Plot ready" : "Plot results" }}</button><button class="run-button" :disabled="isRunning" @click="runWorkflow"><Play :size="17" fill="currentColor" /> {{ isRunning ? "Preparing run..." : "Run workflow" }} <ArrowRight :size="17" /></button></div>
          </section>
        </section>
      </div>

      <section v-else class="database-editor" aria-label="Database editor">
        <nav class="db-menu-bar"><button>File</button><button>Edit</button><button>Session</button><button>View</button><button>Help</button></nav>
        <header class="db-toolbar">
          <button title="Open database" @click="document.querySelector('#db-input-picker').click()"><FolderOpen :size="17" /></button><button title="Open in classic DB Editor" @click="openClassicDatabaseEditor"><LayoutDashboard :size="17" /></button><button title="Save session"><Save :size="17" /></button><span></span><button title="Undo"><Undo2 :size="17" /></button><button title="Redo"><Redo2 :size="17" /></button><span></span><button title="Commit"><Check :size="17" /></button><button title="History"><History :size="17" /></button><span></span><button title="Graph view"><GitBranch :size="17" /></button><label class="db-search"><Search :size="15" /><input placeholder="Search" /></label>
        </header>
        <div class="db-tabs"><button class="active"><Database :size="14" /> {{ inputFile }} <b>×</b></button><button title="Open database"><Plus :size="15" /></button><button class="classic-db-button" type="button" @click="openClassicDatabaseEditor"><LayoutDashboard :size="14" /> Classic DB Editor</button></div>
        <p v-if="projectLoadError || classicDbEditorStatus" class="db-status" :class="{ error: projectLoadError }">{{ projectLoadError || classicDbEditorStatus }}</p>
        <div class="db-dock-grid">
          <section class="db-dock entity-tree-dock"><header>Entity tree <span>×</span></header><div class="tree-filter"><Search :size="13" /><input placeholder="Filter" /></div><div class="db-tree"><p><ChevronDown :size="13" /> commodity</p><p class="tree-child">electricity</p><p class="tree-child">gas</p><p><ChevronDown :size="13" /> node</p><p class="tree-child selected-row">North</p><p class="tree-child">South</p><p><ChevronDown :size="13" /> unit</p></div></section>
          <section class="db-dock parameter-values-dock"><header>Parameter value <span>×</span></header><table class="db-table"><thead><tr><th>Entity class</th><th>Entity</th><th>Parameter</th><th>Alternative</th><th>Value</th></tr></thead><tbody><tr class="selected-row"><td>node</td><td>North</td><td>demand</td><td>Base</td><td>120</td></tr><tr><td>node</td><td>South</td><td>demand</td><td>Base</td><td>94</td></tr><tr><td>unit</td><td>Gas plant</td><td>capacity</td><td>Base</td><td>300</td></tr><tr><td>unit</td><td>Wind</td><td>capacity</td><td>Base</td><td>150</td></tr></tbody></table></section>
          <section class="db-dock entity-dock"><header>Entity <span>×</span></header><table class="db-table"><thead><tr><th>Entity class</th><th>Name</th><th>Description</th></tr></thead><tbody><tr class="selected-row"><td>node</td><td>North</td><td>Northern system node</td></tr><tr><td>node</td><td>South</td><td>Southern system node</td></tr><tr><td>unit</td><td>Gas plant</td><td>Combined cycle gas</td></tr></tbody></table></section>
          <section v-if="dbContent" class="db-dock raw-db-dock"><header>Database: <strong>{{ dbContent.filename }}</strong> <span>×</span></header><div class="db-raw">
              <div v-for="table in dbContent.tables" :key="table.name" class="db-table-preview">
                <h4>{{ table.name }} ({{ table.columns.length }} cols / {{ table.rows.length }} rows)</h4>
                <table class="db-table"><thead><tr><th v-for="col in table.columns" :key="col">{{ col }}</th></tr></thead>
                <tbody><tr v-for="(row, idx) in table.rows" :key="idx"><td v-for="col in table.columns" :key="col">{{ row[col] }}</td></tr></tbody></table>
              </div>
            </div></section>

          <section class="db-dock scenario-dock"><header>Scenario <span>×</span></header><div class="tree-filter"><Search :size="13" /><input placeholder="Filter" /></div><div class="db-tree"><p class="selected-row"><ChevronDown :size="13" /> Base</p><p class="tree-child">Base</p><p><ChevronDown :size="13" /> High demand</p><p class="tree-child">Base</p><p class="tree-child">High demand</p></div></section>
        </div>
      </section>
    </section>
  </main>
</template>