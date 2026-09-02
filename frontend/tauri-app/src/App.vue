<script setup>
import { computed, ref } from "vue";
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
const resultFile = ref("results.sqlite");
const plotReady = ref(false);
const isRunning = ref(false);
const workflowNodes = ref([
  { id: "input", label: "Input data", detail: "Database", icon: Database, className: "canvas-input", x: 20, y: 52 },
  { id: "tool", label: "SpineOpt", detail: "Tool", icon: Wrench, className: "canvas-tool", x: 275, y: 52 },
  { id: "results", label: "Results", detail: "Database", icon: Table2, className: "canvas-results", x: 530, y: 52 },
  { id: "excel-input", label: "Excel input", detail: "Input file", icon: Upload, className: "canvas-excel", x: 20, y: 235 },
  { id: "excel-results", label: "Excel results", detail: "Output file", icon: Table2, className: "canvas-excel", x: 530, y: 235 },
  { id: "plot", label: "Plot results", detail: "Visualization", icon: LineChart, className: "canvas-plot", x: 530, y: 360 },
]);
const draggingNode = ref(null);
const dragOffset = ref({ x: 0, y: 0 });
const recentRuns = ref([
  { name: "Baseline 2030", status: "Ready", time: "Today, 10:42" },
  { name: "High demand", status: "Ready", time: "Yesterday, 16:08" },
]);

const activeMode = computed(() => modes.find((mode) => mode.id === selectedMode.value));

function openProject() {
  selectedProject.value = projects[(projects.indexOf(selectedProject.value) + 1) % projects.length];
  projectMenuOpen.value = false;
}

function runWorkflow() {
  isRunning.value = true;
  window.setTimeout(() => {
    isRunning.value = false;
    recentRuns.value.unshift({ name: scenario.value, status: "Ready", time: "Just now" });
  }, 900);
}

function previewPlot() {
  plotReady.value = true;
}

function startDrag(event, node) {
  draggingNode.value = node;
  dragOffset.value = { x: event.clientX - node.x, y: event.clientY - node.y };
  window.addEventListener("pointermove", moveNode);
  window.addEventListener("pointerup", stopDrag, { once: true });
}

function moveNode(event) {
  if (!draggingNode.value) return;
  draggingNode.value.x = Math.max(8, event.clientX - dragOffset.value.x);
  draggingNode.value.y = Math.max(8, event.clientY - dragOffset.value.y);
}

function stopDrag() {
  draggingNode.value = null;
  window.removeEventListener("pointermove", moveNode);
}
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
            <button class="secondary-button" @click="openProject"><FolderOpen :size="16" /> Open project</button>
          </div>

          <div class="section-heading">
            <div><p class="eyebrow">Workflow</p><h2>Build your run</h2></div>
            <button class="text-button"><Plus :size="16" /> New workflow</button>
          </div>

          <section class="workflow-canvas" aria-label="Draggable workflow design view">
            <div class="canvas-toolbar"><span><span class="canvas-live-dot"></span> Design View</span><small>Drag boxes to arrange your workflow</small></div>
            <div class="canvas-links"><span class="link-one"></span><span class="link-two"></span><span class="link-three"></span><span class="link-four"></span></div>
            <article v-for="node in workflowNodes" :key="node.id" class="canvas-node" :class="node.className" :style="{ left: `${node.x}px`, top: `${node.y}px` }" @pointerdown="startDrag($event, node)">
              <div class="canvas-node-head"><span class="canvas-node-icon"><component :is="node.icon" :size="18" /></span><span>{{ node.detail }}</span><button class="node-menu" title="Node options">...</button></div>
              <strong>{{ node.id === "tool" ? selectedTool : node.label }}</strong>
              <template v-if="node.id === 'input'">
                <label class="canvas-select"><select v-model="inputFile"><option>energy_model.sqlite</option><option>north_sea_data.sqlite</option><option>demo_data.sqlite</option></select></label>
              </template>
              <template v-else-if="node.id === 'tool'">
                <label class="canvas-select"><select v-model="selectedTool"><option>SpineOpt</option><option>Spine Engine</option><option>Data Connection</option><option>Python script</option></select></label>
              </template>
              <template v-else-if="node.id === 'results'">
                <label class="canvas-select"><select v-model="resultFile"><option>results.sqlite</option><option>spineopt_results.sqlite</option><option>export_results.xlsx</option></select></label>
              </template>
              <small v-else>{{ node.label === "Plot results" && plotReady ? "Plot preview ready" : node.label === "Plot results" ? "Open after a run" : node.detail }}</small>
              <button v-if="node.id === 'plot'" class="node-open" @pointerdown.stop @click="previewPlot">Open</button>
            </article>
          </section>

          <section class="action-panel">
            <div><p class="eyebrow">{{ selectedTool }}</p><h2>Configure your run</h2></div>
            <label class="scenario-field"><span>Scenario</span><select v-model="scenario"><option>Baseline 2030</option><option>High demand</option><option>Low renewables</option></select></label>
            <div class="action-buttons"><button class="plot-button" :class="{ ready: plotReady }" @click="previewPlot"><LineChart :size="16" /> {{ plotReady ? "Plot ready" : "Plot results" }}</button><button class="run-button" :disabled="isRunning" @click="runWorkflow"><Play :size="17" fill="currentColor" /> {{ isRunning ? "Preparing run..." : "Run workflow" }} <ArrowRight :size="17" /></button></div>
          </section>
        </section>

        <aside class="recent-panel">
          <div class="section-heading compact"><div><p class="eyebrow">Workspace</p><h2>Recent runs</h2></div><button class="icon-button" title="Add run"><Plus :size="18" /></button></div>
          <div class="run-list">
            <article v-for="run in recentRuns.slice(0, 4)" :key="run.time + run.name" class="run-item"><span class="run-indicator"><Check :size="14" /></span><div><strong>{{ run.name }}</strong><small>{{ run.time }}</small></div><span class="run-status">{{ run.status }}</span></article>
          </div>
          <div class="tip-box"><Sparkles :size="18" /><div><strong>Keep it simple</strong><p>Choose a mode, select a scenario, and let Toolbox handle the rest.</p></div></div>
        </aside>
      </div>
    </section>
  </main>
</template>