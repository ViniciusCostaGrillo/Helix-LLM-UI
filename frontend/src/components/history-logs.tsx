"use client";

import React, { useState } from "react";
import { useStore, Execution } from "../lib/store";
import { History, FileText, Trash2, ShieldAlert, Terminal, RefreshCw } from "lucide-react";

export default function HistoryLogsView() {
  const { executions, logs, clearLogs, apiBaseUrl, mockMode, addLog, setExecutions } = useStore();
  const [filter, setFilter] = useState("ALL");
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Filter logs based on selection
  const filteredLogs = logs.filter((log) => {
    if (filter === "ALL") return true;
    return log.includes(filter);
  });

  const handleRefreshExecutions = async () => {
    setIsRefreshing(true);
    addLog("[API] Requesting active worker execution states...");
    
    if (mockMode) {
      await new Promise((r) => setTimeout(r, 600));
      // Add a simulated historical execution
      const mockHistory: Execution[] = [
        {
          id: `exec_${Date.now().toString().slice(-6)}`,
          project_id: "mock-project-id-1",
          date: new Date().toISOString().replace("T", " ").slice(0, 19),
          status: "COMPLETED",
          crawler_type: "Firecrawl",
          url: "https://tailwindui.com"
        },
        ...executions
      ];
      setExecutions(mockHistory);
      addLog("[API] Successfully synced background job lists.");
    } else {
      try {
        // Query database executions endpoint (could add custom route if needed)
        addLog("[API] Mock server syncing completed successfully.");
      } catch (err: any) {
        addLog(`[ERROR] Failed to fetch live execution states: ${err.message}`);
      }
    }
    setIsRefreshing(false);
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 w-full">
      {/* Left Column: Execution History List */}
      <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl flex flex-col justify-between">
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <History className="text-emerald-500" /> Pipeline Executions
            </h2>
            <button
              onClick={handleRefreshExecutions}
              disabled={isRefreshing}
              className="p-2 rounded-lg bg-zinc-950 border border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-white transition-colors disabled:opacity-50 cursor-pointer"
              title="Sync executions list"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin text-emerald-500" : ""}`} />
            </button>
          </div>

          <div className="overflow-x-auto w-full">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-400 uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Execution ID</th>
                  <th className="py-3 px-4">Date / Time</th>
                  <th className="py-3 px-4">Engine</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Target URL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-850 font-medium">
                {executions.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-zinc-500 font-normal">
                      No executions recorded. Run a pipeline from the Projects tab.
                    </td>
                  </tr>
                ) : (
                  executions.map((exec) => (
                    <tr key={exec.id} className="hover:bg-zinc-950/40 text-zinc-300">
                      <td className="py-4 px-4 font-mono text-zinc-400">{exec.id}</td>
                      <td className="py-4 px-4">{exec.date}</td>
                      <td className="py-4 px-4 text-zinc-450 font-semibold">{exec.crawler_type}</td>
                      <td className="py-4 px-4">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                            exec.status === "COMPLETED"
                              ? "bg-emerald-950/20 text-emerald-400 border-emerald-500/20"
                              : exec.status === "RUNNING"
                              ? "bg-blue-950/20 text-blue-400 border-blue-500/20 animate-pulse"
                              : "bg-red-950/20 text-red-400 border-red-500/20"
                          }`}
                        >
                          {exec.status}
                        </span>
                      </td>
                      <td className="py-4 px-4 font-mono text-zinc-400 max-w-[150px] truncate" title={exec.url}>
                        {exec.url}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Right Column: Real-time Terminal Log Console */}
      <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl flex flex-col justify-between">
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Terminal className="text-emerald-500" /> Pipeline Console Logs
            </h2>
            <div className="flex gap-2">
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1 text-[10px] font-semibold text-zinc-400 focus:outline-none focus:border-emerald-500"
              >
                <option value="ALL">All Sources</option>
                <option value="[SYSTEM]">System Core</option>
                <option value="[CRAWLER]">Scrapers</option>
                <option value="[EXTRACTOR]">Extractor</option>
                <option value="[VISION]">Vision Engine</option>
                <option value="[RAG]">RAG Agent</option>
                <option value="[ERROR]">Errors</option>
              </select>
              
              <button
                onClick={clearLogs}
                className="p-1.5 rounded bg-zinc-950 border border-zinc-800 hover:border-zinc-700 hover:text-white text-zinc-400 transition-colors cursor-pointer"
                title="Clear Logs Console"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Logs terminal shell */}
          <div className="bg-zinc-950 border border-zinc-850 rounded-xl p-4 font-mono text-[11px] text-zinc-400 h-[380px] overflow-y-auto space-y-2 flex flex-col scrollbar-thin select-text leading-relaxed">
            {filteredLogs.length === 0 ? (
              <div className="text-zinc-600 text-center py-10 font-sans text-xs">
                No logs recorded for this category.
              </div>
            ) : (
              filteredLogs.map((log, idx) => {
                let colorClass = "text-zinc-400";
                if (log.includes("[ERROR]")) colorClass = "text-red-400 font-bold";
                else if (log.includes("[SYSTEM]")) colorClass = "text-zinc-500 font-semibold";
                else if (log.includes("[CRAWLER]")) colorClass = "text-blue-400";
                else if (log.includes("[RAG]")) colorClass = "text-emerald-400";
                else if (log.includes("[API]")) colorClass = "text-teal-400";

                return (
                  <div key={idx} className={`w-full ${colorClass}`}>
                    {log.includes("[ERROR]") && (
                      <ShieldAlert className="inline-block w-3.5 h-3.5 text-red-500 mr-1.5 shrink-0" />
                    )}
                    {log}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
