"use client";

import React, { useState } from "react";
import { useStore, UIComponent } from "../lib/store";
import { Database, Search, Layout, Code2, Palette, ShieldAlert } from "lucide-react";

interface RetrievedItem {
  id: string;
  collection: string;
  document: string;
  distance: number;
  metadata: any;
}

export default function RagConsoleView() {
  const { mockMode, apiBaseUrl, addLog } = useStore();
  const [searchTerm, setSearchTerm] = useState("dashboard header menu");
  const [collection, setCollection] = useState("components");
  const [limit, setLimit] = useState(3);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<RetrievedItem[]>([]);
  const [synthesisAnswer, setSynthesisAnswer] = useState("");

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim() || isSearching) return;

    setIsSearching(true);
    setSearchResults([]);
    setSynthesisAnswer("");
    addLog(`[RAG CONSOLE] Querying collection '${collection}' for prompt: "${searchTerm}"...`);

    if (mockMode) {
      await new Promise((r) => setTimeout(r, 700));

      const mockAnswer = (
        `Found relevant layout configurations for prompt: "${searchTerm}".\n\n` +
        `The matched component code structure indicates standard Tailwind spacing coordinates. ` +
        `Use bg-gray-900 border-zinc-800 to maintain style alignment with other layout nodes.`
      );

      const mockDocs: RetrievedItem[] = [
        {
          id: "site_rag_test_999_Sidebar",
          collection: "components",
          document: "import React from 'react';\nexport default function Sidebar() {\n  return <aside className=\"bg-gray-900\">Sidebar</aside>;\n}",
          distance: 0.9543,
          metadata: { component_id: "Sidebar", site_id: "site_rag_test_999" }
        },
        {
          id: "site_rag_test_999",
          collection: "styles",
          document: "Primary Color: #10b981 (emerald-500), Background: #09090b",
          distance: 1.0854,
          metadata: { site_id: "site_rag_test_999" }
        }
      ];

      setSearchResults(mockDocs);
      setSynthesisAnswer(mockAnswer);
      setIsSearching(false);
      addLog("[RAG CONSOLE] Local mock search query completed.");
    } else {
      try {
        const response = await fetch(`${apiBaseUrl}/rag/query`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt: searchTerm,
            collection_name: collection === "all" ? undefined : collection,
            limit: limit
          })
        });

        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();

        setSearchResults(data.retrieved_contexts || []);
        setSynthesisAnswer(data.answer || "");
        setIsSearching(false);
        addLog(`[RAG CONSOLE] Live similarity search returned ${data.retrieved_contexts?.length} results.`);
      } catch (err: any) {
        addLog(`[ERROR] RAG query failed: ${err.message}`);
        setIsSearching(false);
      }
    }
  };

  const getDistanceBadge = (dist: number) => {
    let color = "text-emerald-400 bg-emerald-950/20 border-emerald-500/20";
    let label = "High Confidence";
    
    if (dist > 1.2) {
      color = "text-red-400 bg-red-950/20 border-red-500/20";
      label = "Low Match";
    } else if (dist >= 1.0) {
      color = "text-yellow-400 bg-yellow-950/20 border-yellow-500/20";
      label = "Moderate Match";
    }

    return (
      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${color}`}>
        {dist.toFixed(4)} ({label})
      </span>
    );
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full">
      {/* Left side: query inputs */}
      <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl h-fit">
        <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2 mb-6">
          <Database className="text-emerald-500" /> Vector Space Explorer
        </h2>

        <form onSubmit={handleQuery} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Search Terms</label>
            <input
              type="text"
              required
              placeholder="e.g. emerald buttons dashboard"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-medium"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">ChromaDB Collection</label>
            <select
              value={collection}
              onChange={(e) => setCollection(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-semibold"
            >
              <option value="all">Search All Collections</option>
              <option value="pages">Pages (DOM structure marks)</option>
              <option value="components">Components (React TSX codes)</option>
              <option value="styles">Styles (design guidelines)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Top-K Result Limit</label>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-semibold"
            >
              <option value={2}>Top 2 Matches</option>
              <option value={3}>Top 3 Matches</option>
              <option value={5}>Top 5 Matches</option>
              <option value={10}>Top 10 Matches</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isSearching}
            className="w-full py-3 rounded-lg bg-emerald-500 hover:bg-emerald-600 disabled:bg-zinc-800 text-black font-bold text-sm transition-colors flex justify-center items-center gap-2 cursor-pointer shadow-md shadow-emerald-500/10"
          >
            <Search className="w-4 h-4" />
            {isSearching ? "Searching..." : "Query Vector Space"}
          </button>
        </form>
      </div>

      {/* Right side: results rendering */}
      <div className="lg:col-span-2 space-y-6">
        {/* Synthesis display */}
        {synthesisAnswer && (
          <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl">
            <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-3">
              RAG Agent Response Synthesis
            </h3>
            <div className="bg-zinc-950 border border-zinc-850 p-5 rounded-xl text-xs text-zinc-300 leading-relaxed font-sans whitespace-pre-wrap">
              {synthesisAnswer}
            </div>
          </div>
        )}

        {/* Vector document cards list */}
        <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl">
          <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-wider mb-4">
            Vector Similarity Matches
          </h3>

          <div className="space-y-4">
            {searchResults.length === 0 ? (
              <div className="text-center py-10 text-zinc-500 text-xs">
                No matching results. Input query prompt to search index collections.
              </div>
            ) : (
              searchResults.map((item, idx) => (
                <div key={idx} className="bg-zinc-950 border border-zinc-850 rounded-xl p-5 space-y-3">
                  <div className="flex justify-between items-start flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-zinc-900 border border-zinc-800 rounded text-zinc-400">
                        {item.collection === "pages" ? (
                          <Layout className="w-3.5 h-3.5 text-emerald-500" />
                        ) : item.collection === "components" ? (
                          <Code2 className="w-3.5 h-3.5 text-blue-500" />
                        ) : (
                          <Palette className="w-3.5 h-3.5 text-purple-500" />
                        )}
                      </div>
                      <span className="text-xs font-bold text-white">{item.id}</span>
                      <span className="text-[10px] uppercase font-semibold text-zinc-500 font-mono">
                        {item.collection}
                      </span>
                    </div>

                    {getDistanceBadge(item.distance)}
                  </div>

                  <pre className="text-[10px] font-mono text-zinc-400 bg-zinc-900/60 border border-zinc-850 p-3.5 rounded-lg max-h-40 overflow-y-auto leading-relaxed select-text">
                    {item.document}
                  </pre>
                  
                  <div className="text-[9px] text-zinc-500 font-mono flex gap-4">
                    <span>Metadata: {JSON.stringify(item.metadata)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
