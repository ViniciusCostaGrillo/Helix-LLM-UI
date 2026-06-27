"use client";

import React from "react";
import { useStore } from "../lib/store";
import ChatView from "../components/chat-view";
import EditorPreview from "../components/editor-preview";
import LibraryView from "../components/library";
import SettingsView from "../components/settings";
import { MessageSquare, Code2, Database, Settings } from "lucide-react";

export default function DashboardHome() {
  const { activeTab, setActiveTab } = useStore();

  const menuItems = [
    { id: "chat", label: "Assistente Chat", icon: MessageSquare },
    { id: "editor", label: "Component Workspace", icon: Code2 },
    { id: "library", label: "Library Explorer", icon: Database },
    { id: "settings", label: "Control Settings", icon: Settings }
  ];

  const renderActiveView = () => {
    switch (activeTab) {
      case "chat":
        return <ChatView />;
      case "editor":
        return <EditorPreview />;
      case "library":
        return <LibraryView />;
      case "settings":
        return <SettingsView />;
      default:
        return <ChatView />;
    }
  };

  return (
    <div className="flex h-screen bg-zinc-950 text-white overflow-hidden font-sans select-none antialiased">
      {/* Navigation Sidebar */}
      <aside className="w-64 bg-zinc-950 border-r border-white/5 p-6 flex flex-col justify-between shrink-0">
        <div className="space-y-8">
          {/* Logo brand branding */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-400 to-teal-500 flex items-center justify-center font-extrabold text-black text-lg shadow-md shadow-emerald-500/10 font-mono">
              H
            </div>
            <div>
              <span className="text-sm font-bold tracking-wider text-white block font-mono">HELIX UI</span>
              <span className="text-[8px] font-bold text-emerald-500 uppercase tracking-widest block mt-0.5 font-mono">
                AI Orchestrator
              </span>
            </div>
          </div>

          {/* Nav menu links */}
          <nav className="space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-bold text-xs transition-all duration-200 cursor-pointer ${
                    isActive
                      ? "bg-white/5 border border-white/10 text-emerald-450 shadow-sm"
                      : "text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.02]"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-emerald-400" : "text-zinc-550"}`} />
                  <span className="font-mono">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Footer info */}
        <div className="text-[9px] text-zinc-650 font-mono tracking-wider border-t border-white/5 pt-4 flex justify-between items-center">
          <span>WORKSPACE</span>
          <span className="text-emerald-500/80 font-bold">v1.1.0</span>
        </div>
      </aside>

      {/* Main Workspace Frame Container */}
      <main className="flex-1 flex flex-col overflow-hidden bg-zinc-950">
        {/* Topbar status display */}
        <header className="h-14 border-b border-white/5 px-8 flex justify-between items-center bg-zinc-950 shrink-0">
          <h1 className="text-[10px] font-bold tracking-widest uppercase text-zinc-400 font-mono">
            {menuItems.find((m) => m.id === activeTab)?.label || "Workspace"}
          </h1>
          
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5 font-bold text-[10px] text-zinc-500">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Local Workers Active
            </span>
          </div>
        </header>

        {/* Dynamic Inner Panel Workspace scroll viewport */}
        <div className="flex-1 overflow-y-auto p-8 bg-zinc-950">
          {renderActiveView()}
        </div>
      </main>
    </div>
  );
}
