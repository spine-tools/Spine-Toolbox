<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { invoke } from "@tauri-apps/api/core";
import {
  ArrowRight,
  BarChart3,
  Check,
  ChevronDown,
  CircleHelp,
  Database,
  FolderOpen,
  LineChart,
  LayoutDashboard,
  Play,
  Plus,
  Settings2,
  SlidersHorizontal,
  Sparkles,
  Table2,
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
const selectedProject = ref(projects[0]);
const projectMenuOpen = ref(false);
const scenario = ref("Baseline 2030");
const selectedTool = ref("SpineOpt");
const inputFile = ref("energy_model.sqlite");
const excelInputFile = ref("");
const inputSourceMenuOpen = ref(false);
const resultFile = ref("results.sqlite");
const projectPath = ref("execution_tests/active_by_default");
const projectLoadError = ref("");
const plotReady = ref(false);
const isRunning = ref(false);
const workflowNodes = ref([
  { id: "input", label: "Input data", detail: "", icon: Database, className: "canvas-input", x: 20, y: 52 },
  { id: "tool", label: "SpineOpt", detail: "Tool", icon: Wrench, className: "canvas-tool", x: 210, y: 52 },
  { id: "results", label: "Results", detail: "", icon: Table2, className: "canvas-results", x: 400, y: 52 },
  { id: "excel-results", label: "Excel results", detail: "", icon: Table2, className: "canvas-excel", x: 400, y: 265 },
  { id: "plot", label: "Plot results", detail: "", icon: LineChart, className: "canvas-plot", x: 400, y: 430 },
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

const activeMode = computed(() => modes.find((mode) => mode.id === selectedMode.value));
const workflowConnections = ref([
  ["input", "tool"],
  ["tool", "results"],
  ["results", "excel-results"],
  ["results", "plot"],
]);

async function callBackend(method, params = {}) {
  const request = JSON.stringify({ method, params });
  const response = await invoke("python_bridge_request", { request });
  const message = JSON.parse(response);
  if (!message.ok) throw new Error(message.error);
  return message.result;
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
  if (source === "excel") openExcelPicker();
}

function closeInputSourceMenu(event) {
  if (!event.target.closest(".canvas-input")) inputSourceMenuOpen.value = false;
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

function nodePorts(node) {
  return [
    { x: node.x + 66, y: node.y, dx: 0, dy: -1 },
    { x: node.x + 132, y: node.y + 54, dx: 1, dy: 0 },
    { x: node.x + 66, y: node.y + 108, dx: 0, dy: 1 },
    { x: node.x, y: node.y + 54, dx: -1, dy: 0 },
  ];
}

function connectionPorts([sourceId, targetId]) {
  const source = workflowNodes.value.find((node) => node.id === sourceId);
  const target = workflowNodes.value.find((node) => node.id === targetId);
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
    const dataStores = project.items.filter((item) => item.type === "Data Store");
    if (dataStores.length) {
      inputFile.value = dataStores[0].database;
      workflowNodes.value.find((node) => node.id === "input").label = dataStores[0].name;
    }
    recentRuns.value = project.items
      .filter((item) => item.type !== "Data Store")
      .slice(0, 4)
      .map((item) => ({ name: item.name, status: item.type, time: "Project item" }));
  } catch (error) {
    projectLoadError.value = `Could not load project: ${error.message}`;
  }
}

onMounted(() => {
  loadProject();
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
        <button class="nav-item active"><LayoutDashboard :size="18" /> Overview</button>
        <button class="nav-item"><SlidersHorizontal :size="18" /> Workflows</button>
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

      <div class="content-grid">
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
            <div class="project-open-controls"><input v-model="projectPath" class="project-path" aria-label="Project directory" /><button class="secondary-button" @click="loadProject"><FolderOpen :size="16" /> Load project</button></div>
          </div>
          <p v-if="projectLoadError" class="project-error">{{ projectLoadError }}</p>

          <div class="section-heading">
            <div><p class="eyebrow">Workflow</p><h2>Build your run</h2></div>
            <button class="text-button"><Plus :size="16" /> New workflow</button>
          </div>

          <section ref="canvas" class="workflow-canvas" aria-label="Draggable workflow design view" @pointerdown.self="startSelection">
            <div class="canvas-toolbar"><span><span class="canvas-live-dot"></span> Design View</span><small>Drag boxes to arrange your workflow</small></div>
            <svg class="canvas-links" aria-hidden="true" @pointerdown.self="resetCanvasSelection">
              <defs><marker id="connection-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M 0 0 L 8 4 L 0 8 z" /></marker></defs>
              <g v-for="connection in workflowConnections" :key="connection.join('-')">
                <path class="connection-hit" :d="connectionPath(connection)" @pointerdown.stop @click.stop="selectConnection(connection)" />
                <path :class="{ selected: selectedConnection === connection.join('-') }" :d="connectionPath(connection)" marker-end="url(#connection-arrow)" />
              </g>
            </svg>
            <div v-if="selectionBox" class="selection-box" :style="{ left: `${selectionBox.x}px`, top: `${selectionBox.y}px`, width: `${selectionBox.width}px`, height: `${selectionBox.height}px` }"></div>
            <article v-for="node in workflowNodes" :key="node.id" class="canvas-node" :class="[node.className, { selected: selectedNodeIds.includes(node.id) }]" :style="{ left: `${node.x}px`, top: `${node.y}px` }" @pointerdown="startDrag($event, node)">
              <div class="canvas-node-head"><span class="canvas-node-icon"><component :is="node.icon" :size="24" /></span><span v-if="node.detail">{{ node.detail }}</span></div>
              <strong>{{ node.id === "tool" ? selectedTool : node.label }}</strong>
              <template v-if="node.id === 'input'">
                <div v-if="inputSourceMenuOpen" class="input-source-menu" @pointerdown.stop>
                  <button type="button" @click="chooseInputSource('database')"><Database :size="13" /> Use database</button>
                  <button type="button" @click="chooseInputSource('excel')"><Upload :size="13" /> Choose Excel file</button>
                </div>
                <input id="excel-input-picker" class="hidden-file-picker" type="file" accept=".xlsx,.xls" @change="importExcel" />
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
    </section>
  </main>
</template>