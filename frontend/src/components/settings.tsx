"use client";

import React, { useState } from "react";
import { useStore } from "../lib/store";
import { Settings, Server, Key, Eye, EyeOff, ShieldCheck, ShieldAlert } from "lucide-react";

export default function SettingsView() {
  const {
    apiBaseUrl,
    setApiBaseUrl,
    mockMode,
    setMockMode,
    keys,
    setKeys,
    addLog
  } = useStore();

  const [showKeys, setShowKeys] = useState(false);
  const [healthStatus, setHealthStatus] = useState<"IDLE" | "SUCCESS" | "ERROR">("IDLE");
  const [healthMsg, setHealthMsg] = useState("");

  const handleTestConnection = async () => {
    setHealthStatus("IDLE");
    addLog("[SYSTEM] Pinging backend API health check endpoint...");
    
    try {
      const res = await fetch(`${apiBaseUrl}/health`);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      
      setHealthStatus("SUCCESS");
      setHealthMsg(`Connected successfully. Status: ${data.status}, Service: ${data.service}`);
      addLog(`[SYSTEM] Backend API health check returned success: ${data.status}`);
    } catch (err: any) {
      setHealthStatus("ERROR");
      setHealthMsg(`Connection failed: ${err.message}. Ensure the backend server is running.`);
      addLog(`[SYSTEM] Connection error reaching API at ${apiBaseUrl}`);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 w-full">
      {/* Backend connection setup */}
      <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl space-y-6">
        <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <Server className="text-emerald-500" /> Connection Parameters
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
              API Server Base URL
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                value={apiBaseUrl}
                onChange={(e) => setApiBaseUrl(e.target.value)}
                placeholder="http://localhost:8000"
                className="flex-1 bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
              />
              <button
                onClick={handleTestConnection}
                className="px-4 py-2.5 rounded-lg bg-zinc-950 border border-zinc-850 hover:border-zinc-750 text-xs font-bold text-emerald-400 hover:text-emerald-300 transition-colors cursor-pointer"
              >
                Test URL
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between p-4 bg-zinc-950 rounded-xl border border-zinc-850">
            <div>
              <span className="text-sm font-bold text-white block">Offline Mock Sandbox Fallback</span>
              <span className="text-xs text-zinc-550 block mt-0.5 leading-relaxed">
                Processes pipelines locally without active LLM/crawler API keys using mock models.
              </span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer select-none">
              <input
                type="checkbox"
                checked={mockMode}
                onChange={(e) => {
                  setMockMode(e.target.checked);
                  addLog(`[SYSTEM] Mock Sandbox mode toggled to: ${e.target.checked}`);
                }}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-zinc-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-zinc-400 after:border-zinc-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500 peer-checked:after:bg-black peer-checked:after:border-black"></div>
            </label>
          </div>
        </div>

        {healthStatus !== "IDLE" && (
          <div
            className={`p-4 rounded-xl border flex gap-3 text-xs leading-relaxed ${
              healthStatus === "SUCCESS"
                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                : "bg-red-500/10 border-red-500/20 text-red-400"
            }`}
          >
            {healthStatus === "SUCCESS" ? (
              <ShieldCheck className="shrink-0 w-5 h-5" />
            ) : (
              <ShieldAlert className="shrink-0 w-5 h-5" />
            )}
            <span>{healthMsg}</span>
          </div>
        )}
      </div>

      {/* Model keys setup */}
      <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Key className="text-emerald-500" /> LLM Key Configuration
          </h2>
          <button
            onClick={() => setShowKeys(!showKeys)}
            className="p-2 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-400 hover:text-white cursor-pointer"
          >
            {showKeys ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
              Gemini API Key
            </label>
            <input
              type={showKeys ? "text" : "password"}
              value={keys.gemini}
              onChange={(e) => setKeys({ gemini: e.target.value })}
              placeholder={keys.gemini ? "••••••••••••••••" : "AIzaSy..."}
              className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
              OpenAI API Key
            </label>
            <input
              type={showKeys ? "text" : "password"}
              value={keys.openai}
              onChange={(e) => setKeys({ openai: e.target.value })}
              placeholder={keys.openai ? "••••••••••••••••" : "sk-..."}
              className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
              Anthropic API Key
            </label>
            <input
              type={showKeys ? "text" : "password"}
              value={keys.anthropic}
              onChange={(e) => setKeys({ anthropic: e.target.value })}
              placeholder={keys.anthropic ? "••••••••••••••••" : "sk-ant-..."}
              className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
