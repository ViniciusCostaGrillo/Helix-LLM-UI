"use client";

import React, { useState } from "react";
import { useStore, Project, Execution, UIComponent } from "../lib/store";
import { FolderGit2, Plus, Play, Info, CheckCircle2 } from "lucide-react";

export default function ProjectsView() {
  const {
    projects,
    selectedProjectId,
    setSelectedProjectId,
    addProject,
    mockMode,
    apiBaseUrl,
    addLog,
    addExecution,
    setComponents
  } = useStore();

  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [crawlUrl, setCrawlUrl] = useState("https://example.com");
  const [crawlerType, setCrawlerType] = useState("Playwright");
  const [isRunning, setIsRunning] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    const newProj: Project = {
      id: `proj_${Date.now()}`,
      name: newName,
      description: newDesc || "No description provided.",
      user_id: "default-user"
    };

    addProject(newProj);
    setSelectedProjectId(newProj.id);
    addLog(`[PROJECT] Created new project: ${newProj.name} (${newProj.id})`);
    setNewName("");
    setNewDesc("");
  };

  const handleTriggerPipeline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!crawlUrl.trim() || isRunning) return;

    setIsRunning(true);
    setSuccessMsg("");
    addLog(`[PIPELINE] Starting orchestration execution context for URL: ${crawlUrl}...`);

    const execId = `exec_${Date.now().toString().slice(-6)}`;
    const newExec: Execution = {
      id: execId,
      project_id: selectedProjectId,
      date: new Date().toISOString().replace("T", " ").slice(0, 19),
      status: "RUNNING",
      crawler_type: crawlerType,
      url: crawlUrl
    };

    addExecution(newExec);

    if (mockMode) {
      // Simulate sequential nodes running
      const steps = [
        `[CRAWLER] Launching headless Chrome scraper via ${crawlerType}...`,
        `[CRAWLER] Captured page screenshot and saved raw HTML. Status: Success.`,
        `[EXTRACTOR] Analyzing HTML hierarchy and CSS class trees...`,
        `[EXTRACTOR] Parsed DOM tree. Found 14 semantic nodes, fonts: [Inter], colors: [#0f172a].`,
        `[VISION] Starting visual layouts density spacing profile calculator...`,
        `[VISION] Discovered background canvas color #ffffff, visual content density: 42%.`,
        `[ANALYZER] Prompting LLM Layout analyzer for design tokens guidelines...`,
        `[ANALYZER] Synthesis Guidelines created: metadata.json compiled.`,
        `[CODEGEN] Converting layout specs into responsive React TSX component modules...`,
        `[CODEGEN] Produced modular components: HeroBlock, NavbarMenu, FeatureGrid.`,
        `[DATASET] Packaging crawler history and code components site manifest...`,
        `[DATASET] Package site_000099.zip successfully indexed.`,
        `[RAG] Vectorizing and upserting layout layout embeddings into ChromaDB collection...`,
        `[SYSTEM] Daily batch processing pipelines completed successfully. State saved.`
      ];

      for (let i = 0; i < steps.length; i++) {
        await new Promise((r) => setTimeout(r, 400));
        addLog(steps[i]);
      }

      // Add mock components generated to this project
      const mockComps: UIComponent[] = [
        {
          id: `comp_${Date.now()}_1`,
          project_id: selectedProjectId,
          name: "NavbarMenu",
          code: `import React from 'react';

export default function NavbarMenu() {
  return (
    <nav className="w-full bg-zinc-900 border-b border-zinc-800 py-4 px-8 flex justify-between items-center text-white font-sans">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded bg-emerald-500 flex items-center justify-center text-black font-extrabold">A</div>
        <span className="text-lg font-bold tracking-tight">AI Marketplace</span>
      </div>
      <div className="hidden md:flex gap-6 text-zinc-400 text-sm font-semibold">
        <a href="#" className="hover:text-white transition-colors">Features</a>
        <a href="#" className="hover:text-white transition-colors">Pricing</a>
        <a href="#" className="hover:text-white transition-colors">Developers</a>
      </div>
      <button className="px-4 py-2 text-xs font-bold rounded-lg bg-emerald-500 hover:bg-emerald-600 text-black transition-colors">
        Console
      </button>
    </nav>
  );
}`,
          type: "navbar"
        },
        {
          id: `comp_${Date.now()}_2`,
          project_id: selectedProjectId,
          name: "HeroBlock",
          code: `import React from 'react';

export default function HeroBlock() {
  return (
    <header className="w-full py-24 px-6 bg-zinc-950 text-white font-sans text-center">
      <div className="max-w-3xl mx-auto flex flex-col items-center">
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight mb-6">
          The Intelligent Way to <br />
          <span className="text-emerald-500">Construct UI Layouts</span>
        </h1>
        <p className="text-zinc-400 text-lg max-w-xl mb-8 leading-relaxed">
          Retrieval-augmented layout synthesis packages design specs and typescript components automatically.
        </p>
        <button className="px-6 py-3 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-black font-semibold transition-colors shadow-lg shadow-emerald-500/20">
          Trigger Pipeline
        </button>
      </div>
    </header>
  );
}`,
          type: "landing"
        }
      ];

      setComponents(mockComps);
      setIsRunning(false);
      setSuccessMsg(`Successfully executed pipeline ${execId}! navbar and landing components populated in editor.`);
      
      // Update execution status
      useStore.setState((state) => ({
        executions: state.executions.map(e => e.id === execId ? { ...e, status: "COMPLETED" } : e)
      }));

    } else {
      // Live API Call
      try {
        const response = await fetch(`${apiBaseUrl}/generation/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ project_id: selectedProjectId, prompt: crawlUrl })
        });
        
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        
        addLog(`[API] Generation triggered. ExecutionID: ${data.execution_id}`);
        setSuccessMsg(`Pipeline triggered in live worker daemon! Execution ID: ${data.execution_id}`);
        
        // Wait and check worker job completion
        setIsRunning(false);
      } catch (err: any) {
        addLog(`[ERROR] Live API pipeline trigger failed: ${err.message}`);
        setIsRunning(false);
        
        useStore.setState((state) => ({
          executions: state.executions.map(e => e.id === execId ? { ...e, status: "FAILED" } : e)
        }));
      }
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full">
      {/* Left side: Projects selector list */}
      <div className="lg:col-span-2 space-y-6">
        <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <FolderGit2 className="text-emerald-500" /> Projects Explorer
            </h2>
            <span className="text-xs font-semibold px-2.5 py-1 bg-zinc-800 border border-zinc-700 rounded-full text-zinc-400">
              {projects.length} Active
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projects.map((proj) => {
              const isSelected = proj.id === selectedProjectId;
              return (
                <div
                  key={proj.id}
                  onClick={() => setSelectedProjectId(proj.id)}
                  className={`p-5 rounded-xl border cursor-pointer transition-all duration-200 flex flex-col justify-between ${
                    isSelected
                      ? "bg-zinc-950 border-emerald-500/80 shadow-lg shadow-emerald-500/5"
                      : "bg-zinc-950/60 border-zinc-800 hover:border-zinc-700"
                  }`}
                >
                  <div>
                    <h3 className={`font-bold text-base mb-1 ${isSelected ? "text-emerald-400" : "text-white"}`}>
                      {proj.name}
                    </h3>
                    <p className="text-xs text-zinc-400 leading-relaxed mb-4">{proj.description}</p>
                  </div>
                  <div className="flex justify-between items-center text-[10px] text-zinc-500 font-mono">
                    <span>ID: {proj.id}</span>
                    <span>User: {proj.user_id}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Create new project form */}
        <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Plus className="text-emerald-500 w-5 h-5" /> Initialize New Project Workspace
          </h2>
          <form onSubmit={handleCreateProject} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Project Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dashboard Redesign"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-medium"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Description</label>
                <input
                  type="text"
                  placeholder="e.g. Crawling layout specifications..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-medium"
                />
              </div>
            </div>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-black font-bold text-sm transition-colors cursor-pointer"
            >
              Create Project
            </button>
          </form>
        </div>
      </div>

      {/* Right side: Orchestration Control Room */}
      <div className="space-y-6">
        <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Play className="text-emerald-500 w-5 h-5" /> Orchestration Panel
            </h2>
            
            <div className="bg-zinc-950/80 border border-zinc-800 p-4 rounded-lg mb-6 flex gap-3 text-xs text-zinc-400">
              <Info className="text-emerald-400 shrink-0 w-4 h-4 mt-0.5" />
              <div>
                Selected Project: <span className="font-semibold text-white">
                  {projects.find((p) => p.id === selectedProjectId)?.name || "None"}
                </span>
                <p className="mt-1">
                  Triggers playbooks sequentially to crawl HTML/CSS style metrics and build vector indexes.
                </p>
              </div>
            </div>

            <form onSubmit={handleTriggerPipeline} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Target URL</label>
                <input
                  type="url"
                  required
                  placeholder="https://example.com"
                  value={crawlUrl}
                  onChange={(e) => setCrawlUrl(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-medium font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Scraping Engine</label>
                <select
                  value={crawlerType}
                  onChange={(e) => setCrawlerType(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-semibold"
                >
                  <option value="Playwright">Playwright headless Chromium</option>
                  <option value="Crawl4AI">Crawl4AI Markdowns scraper</option>
                  <option value="Firecrawl">Firecrawl APIs extractor</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={isRunning}
                className={`w-full py-3 rounded-lg font-bold text-sm transition-all duration-200 flex justify-center items-center gap-2 ${
                  isRunning
                    ? "bg-zinc-800 text-zinc-500 cursor-not-allowed border border-zinc-750"
                    : "bg-gradient-to-r from-emerald-500 to-teal-500 text-black hover:opacity-95 shadow-md shadow-emerald-500/10 cursor-pointer"
                }`}
              >
                {isRunning ? (
                  <>
                    <div className="w-4 h-4 rounded-full border-2 border-zinc-500 border-t-white animate-spin"></div>
                    Executing Pipelines...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    Launch Daily Pipeline
                  </>
                )}
              </button>
            </form>
          </div>

          {successMsg && (
            <div className="mt-4 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex gap-2.5 text-xs text-emerald-400 animate-fade-in leading-relaxed">
              <CheckCircle2 className="shrink-0 w-4 h-4 mt-0.5" />
              <span>{successMsg}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
