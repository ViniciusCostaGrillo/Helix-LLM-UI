"use client";

import React from "react";
import { useStore } from "../lib/store";
import ProjectsView from "../components/projects";
import EditorPreview from "../components/editor-preview";
import HistoryLogsView from "../components/history-logs";
import RagConsoleView from "../components/rag-console";
import SettingsView from "../components/settings";
import KnowledgeView from "../components/knowledge";
import { FolderGit2, Code2, History, Database, Settings, FileUp } from "lucide-react";

export default function DashboardHome() {
  const { activeTab, setActiveTab } = useStore();

  const menuItems = [
    { id: "projects", label: "Projects Explorer", icon: FolderGit2 },
    { id: "editor", label: "Editor & Preview", icon: Code2 },
    { id: "history", label: "Execution History", icon: History },
    { id: "rag", label: "Vector RAG Console", icon: Database },
    { id: "knowledge", label: "Knowledge Ingest", icon: FileUp },
    { id: "settings", label: "Control Settings", icon: Settings }
  ];

  const renderActiveView = () => {
    switch (activeTab) {
      case "projects":
        return <ProjectsView />;
      case "editor":
        return <EditorPreview />;
      case "history":
        return <HistoryLogsView />;
      case "rag":
        return <RagConsoleView />;
      case "knowledge":
        return <KnowledgeView />;
      case "settings":
        return <SettingsView />;
      default:
        return <ProjectsView />;
    }
  };

  return (
    <div className="flex h-screen bg-zinc-950 text-white overflow-hidden font-sans">
      {/* Navigation Sidebar */}
      <aside className="w-72 bg-zinc-900 border-r border-zinc-800 p-6 flex flex-col justify-between shrink-0">
        <div>
          {/* Logo brand branding */}
          <div className="flex items-center gap-3 mb-8">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-400 to-teal-500 flex items-center justify-center font-extrabold text-black text-xl shadow-md shadow-emerald-500/10">
              U
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white block">UI AI ECOSYSTEM</span>
              <span className="text-[9px] font-bold text-zinc-550 uppercase tracking-widest block mt-0.5">Automated Builder</span>
            </div>
          </div>

          {/* Nav menu links */}
          <nav className="space-y-1.5">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3.5 px-4.5 py-3 rounded-xl font-bold text-sm transition-all duration-200 cursor-pointer ${
                    isActive
                      ? "bg-emerald-500 text-black shadow-lg shadow-emerald-500/10 scale-[1.01]"
                      : "text-zinc-400 hover:bg-zinc-800 hover:text-white hover:scale-[1.01]"
                  }`}
                >
                  <Icon className={`w-5 h-5 ${isActive ? "text-black" : "text-zinc-400 group-hover:text-white"}`} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Footer info */}
        <div className="text-[10px] text-zinc-650 font-mono tracking-wider border-t border-zinc-800/60 pt-4 flex justify-between items-center">
          <span>WORKSPACE CLIENT</span>
          <span>v1.0.0</span>
        </div>
      </aside>

      {/* Main Workspace Frame Container */}
      <main className="flex-1 flex flex-col overflow-hidden bg-zinc-950">
        {/* Topbar status display */}
        <header className="h-16 border-b border-zinc-800/80 px-8 flex justify-between items-center bg-zinc-900/20 shrink-0">
          <h1 className="text-sm font-extrabold tracking-wide uppercase text-zinc-400">
            {menuItems.find((m) => m.id === activeTab)?.label || "Workspace"}
          </h1>
          
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5 font-bold text-zinc-400">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Local Workers Active
            </span>
          </div>
        </header>

        {/* Dynamic Inner Panel Workspace scroll viewport */}
        <div className="flex-1 overflow-y-auto p-8 bg-zinc-950 select-none">
          {renderActiveView()}
        </div>
      </main>
    </div>
  );
}
