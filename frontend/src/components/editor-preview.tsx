"use client";

import React, { useState, useEffect } from "react";
import Editor from "@monaco-editor/react";
import { useStore, UIComponent } from "../lib/store";
import { Code2, Monitor, Play, RefreshCw, AlertCircle, Database, HelpCircle } from "lucide-react";

export default function EditorPreview() {
  const {
    components,
    selectedComponentId,
    setSelectedComponentId,
    selectedProjectId,
    updateComponentCode,
    mockMode,
    apiBaseUrl,
    addLog
  } = useStore();

  // Filter components belonging to active project
  const projectComponents = components.filter((c) => c.project_id === selectedProjectId);
  const activeComp = projectComponents.find((c) => c.id === selectedComponentId) || projectComponents[0];

  const [codeValue, setCodeValue] = useState("");
  const [refinePrompt, setRefinePrompt] = useState("");
  const [isQueryingRAG, setIsQueryingRAG] = useState(false);
  const [ragResult, setRagResult] = useState<any>(null);
  const [previewTab, setPreviewTab] = useState<"render" | "raw">("render");

  useEffect(() => {
    if (activeComp) {
      setCodeValue(activeComp.code);
      setSelectedComponentId(activeComp.id);
    } else {
      setCodeValue("");
    }
  }, [selectedComponentId, selectedProjectId, activeComp]);

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined && activeComp) {
      setCodeValue(value);
      updateComponentCode(activeComp.id, value);
    }
  };

  const handleRefineCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!refinePrompt.trim() || isQueryingRAG) return;

    setIsQueryingRAG(true);
    setRagResult(null);
    addLog(`[RAG] Initiating refinement query search: "${refinePrompt}"...`);

    if (mockMode) {
      await new Promise((r) => setTimeout(r, 800));
      const mockResponse = {
        answer: `I analyzed your prompt and retrieved components from the vector database. Here are the recommendations:
- Modify the background styling class to use bg-zinc-950 for high contrast.
- Ensure the hover state has 'transition-all duration-200' to align with UI micro-animations rules.
- Check component import blocks.`,
        retrieved_contexts: [
          { id: "style_rag_test_999", collection: "styles", distance: 0.985 },
          { id: "site_rag_test_999_Sidebar", collection: "components", distance: 1.042 }
        ]
      };
      setRagResult(mockResponse);
      setIsQueryingRAG(false);
      addLog("[RAG] Refinement suggestions returned from mock agent.");
    } else {
      try {
        const response = await fetch(`${apiBaseUrl}/rag/query`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: refinePrompt, limit: 2 })
        });
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        setRagResult(data);
        setIsQueryingRAG(false);
        addLog(`[RAG] Refinement query complete. Matched ${data.retrieved_contexts.length} contexts.`);
      } catch (err: any) {
        addLog(`[ERROR] RAG prompt query failed: ${err.message}`);
        setIsQueryingRAG(false);
      }
    }
  };

  // Helper to render interactive visual mock depending on component name
  const renderVisualMockup = () => {
    if (!activeComp) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-zinc-500 text-sm">
          <AlertCircle className="w-8 h-8 mb-2 text-zinc-600" />
          No components generated yet. Trigger a crawl under the Projects tab.
        </div>
      );
    }

    const cName = activeComp.name.toLowerCase();

    if (cName.includes("hero") || cName.includes("landing")) {
      return (
        <div className="w-full bg-zinc-950 text-white rounded-xl p-8 border border-zinc-800 text-center font-sans">
          <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 bg-emerald-950/40 px-2 py-1 rounded">
            Live Preview (HeroSection)
          </span>
          <h1 className="text-3xl font-extrabold mt-6 mb-4">Design Beautiful Websites</h1>
          <p className="text-zinc-400 text-xs max-w-md mx-auto mb-6 leading-relaxed">
            Instantly crawl existing layout styles and synthesize React components styled with Tailwind.
          </p>
          <div className="flex justify-center gap-3">
            <button className="px-4 py-2 rounded text-xs font-bold bg-emerald-500 hover:bg-emerald-600 text-black transition-colors">
              Get Started
            </button>
            <button className="px-4 py-2 rounded text-xs font-bold bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700">
              Learn More
            </button>
          </div>
        </div>
      );
    }

    if (cName.includes("navbar") || cName.includes("header")) {
      return (
        <div className="w-full bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex justify-between items-center text-white font-sans">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-emerald-500 flex items-center justify-center text-black font-extrabold text-xs">A</div>
            <span className="font-bold text-sm">AI Marketplace</span>
          </div>
          <div className="flex gap-4 text-zinc-400 text-xs font-semibold">
            <span className="hover:text-white cursor-pointer">Features</span>
            <span className="hover:text-white cursor-pointer">Pricing</span>
          </div>
          <button className="px-3 py-1.5 text-[10px] font-bold rounded bg-emerald-500 text-black">
            Console
          </button>
        </div>
      );
    }

    if (cName.includes("product") || cName.includes("grid") || cName.includes("card")) {
      return (
        <div className="w-full bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-white font-sans">
          <h3 className="font-bold text-sm mb-4">Featured Products (ProductGrid)</h3>
          <div className="grid grid-cols-2 gap-4">
            {[1, 2].map((i) => (
              <div key={i} className="bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden p-3">
                <div className="h-24 bg-zinc-700 rounded-md mb-2 flex items-center justify-center text-[10px] text-zinc-400 uppercase font-mono">
                  Image placeholder
                </div>
                <div className="flex justify-between items-center">
                  <div>
                    <h4 className="font-bold text-xs">Product Item {i}</h4>
                    <span className="text-[10px] text-emerald-400 font-semibold">$99.00</span>
                  </div>
                  <button className="px-2 py-1 text-[8px] font-bold rounded bg-zinc-700 hover:bg-emerald-500 hover:text-black">
                    Add
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // Default layout simulation
    return (
      <div className="w-full bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-white font-sans text-center">
        <h3 className="text-base font-bold mb-2 text-emerald-400">{activeComp.name}</h3>
        <p className="text-zinc-500 text-xs mb-4">Code parsed structure preview. Component compiled dynamically.</p>
        <div className="border border-dashed border-zinc-700 rounded p-4 text-xs font-mono text-zinc-400 bg-zinc-950/60 max-h-48 overflow-y-auto text-left leading-relaxed">
          {activeComp.code.slice(0, 300)}...
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col gap-6 w-full h-full">
      {/* File selector header */}
      <div className="bg-zinc-900/40 border border-white/5 px-6 py-4 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20 text-emerald-500">
            <Code2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">Component Builder Workspace</h2>
            <p className="text-xs text-zinc-400">Edit TSX structures and verify styling coordinates</p>
          </div>
        </div>

        {/* File tabs selector */}
        <div className="flex flex-wrap gap-2 w-full md:w-auto">
          {projectComponents.length === 0 ? (
            <span className="text-xs text-zinc-500 font-medium">No component files present.</span>
          ) : (
            projectComponents.map((comp) => {
              const isSelected = comp.id === selectedComponentId;
              return (
                <button
                  key={comp.id}
                  onClick={() => setSelectedComponentId(comp.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                    isSelected
                      ? "bg-emerald-500 text-black border-emerald-500"
                      : "bg-zinc-950/40 border border-white/5 hover:border-zinc-700 text-zinc-400"
                  }`}
                >
                  {comp.name}.tsx
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Workspace split columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full items-start">
        {/* Left Column: Monaco Code Editor */}
        <div className="bg-zinc-900/40 border border-white/5 rounded-2xl overflow-hidden flex flex-col">
          <div className="bg-zinc-950/60 border-b border-white/5 px-5 py-3 flex justify-between items-center">
            <span className="text-xs font-bold text-zinc-400 flex items-center gap-2">
              <Code2 className="w-4 h-4 text-emerald-500" /> Source Editor
            </span>
            <span className="text-[10px] font-mono text-zinc-500 uppercase">TypeScript React</span>
          </div>

          <div className="py-2.5 bg-[#1b1b1c]">
            {activeComp ? (
              <Editor
                height="500px"
                language="typescript"
                theme="vs-dark"
                value={codeValue}
                onChange={handleEditorChange}
                options={{
                  minimap: { enabled: false },
                  fontSize: 13,
                  fontFamily: "var(--font-jetbrains-mono), monospace",
                  scrollbar: { vertical: "visible" },
                  automaticLayout: true
                }}
              />
            ) : (
              <div className="h-[500px] flex items-center justify-center text-zinc-500 text-sm">
                No active component code loaded.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Preview pane & RAG console */}
        <div className="space-y-6">
          {/* Visual Preview Container */}
          <div className="bg-zinc-900/40 border border-white/5 rounded-2xl overflow-hidden flex flex-col">
            <div className="bg-zinc-950/60 border-b border-white/5 px-5 py-3 flex justify-between items-center flex-wrap gap-2">
              <span className="text-xs font-bold text-zinc-400 flex items-center gap-2">
                <Monitor className="w-4 h-4 text-emerald-500" /> Interactive Preview Panel
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPreviewTab("render")}
                  className={`text-[10px] font-bold px-2.5 py-1 rounded transition-colors ${
                    previewTab === "render" ? "bg-emerald-500 text-black" : "text-zinc-500 hover:text-white"
                  }`}
                >
                  Rendered
                </button>
                <button
                  onClick={() => setPreviewTab("raw")}
                  className={`text-[10px] font-bold px-2.5 py-1 rounded transition-colors ${
                    previewTab === "raw" ? "bg-emerald-500 text-black" : "text-zinc-500 hover:text-white"
                  }`}
                >
                  Raw Layout
                </button>
              </div>
            </div>

            <div className="p-6 bg-zinc-950 flex items-center justify-center min-h-[300px]">
              {previewTab === "render" ? (
                renderVisualMockup()
              ) : (
                <pre className="w-full text-xs font-mono text-zinc-400 bg-zinc-900 border border-zinc-800 p-4 rounded-xl max-h-72 overflow-y-auto leading-relaxed">
                  {activeComp ? activeComp.code : "No source code to display."}
                </pre>
              )}
            </div>
          </div>

          {/* RAG Refinement Console drawer */}
          <div className="bg-zinc-900/40 border border-white/5 p-6 rounded-2xl">
            <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
              <Database className="text-emerald-500 w-5 h-5" /> RAG Refinement Console
            </h3>
            <p className="text-xs text-zinc-400 mb-4 leading-relaxed">
              Query vector databases to retrieve design palettes, semantic grids, and styling components from other crawled packages.
            </p>

            <form onSubmit={handleRefineCode} className="flex gap-2 mb-4">
              <input
                type="text"
                required
                placeholder="e.g. Find layout colors and spacing profile..."
                value={refinePrompt}
                onChange={(e) => setRefinePrompt(e.target.value)}
                className="flex-1 bg-zinc-950 border border-white/5 hover:border-zinc-700 rounded-lg px-4 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-medium"
              />
              <button
                type="submit"
                disabled={isQueryingRAG}
                className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 disabled:bg-zinc-800 text-black font-bold text-xs transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                {isQueryingRAG ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-current" />
                )}
                Query
              </button>
            </form>

            {ragResult && (
              <div className="space-y-3 animate-fade-in">
                <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-800 text-xs text-zinc-300 leading-relaxed max-h-48 overflow-y-auto font-sans">
                  <div className="font-bold text-emerald-400 mb-2 flex items-center gap-1.5">
                    <HelpCircle className="w-4 h-4 text-emerald-500" /> RAG Agent Recommendations:
                  </div>
                  {ragResult.answer}
                </div>

                <div className="flex gap-2">
                  {ragResult.retrieved_contexts.map((doc: any, i: number) => (
                    <span
                      key={i}
                      className="text-[9px] font-semibold px-2 py-1 bg-zinc-950 border border-zinc-850 rounded text-zinc-400 font-mono"
                    >
                      Matched {doc.collection} ({doc.id}) Dist: {doc.distance}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
