import { create } from "zustand";

export interface Project {
  id: string;
  name: string;
  description: string;
  user_id: string;
}

export interface UIComponent {
  id: string;
  project_id: string;
  name: string;
  code: string;
  type: string;
}

export interface Execution {
  id: string;
  project_id: string;
  date: string;
  status: "COMPLETED" | "RUNNING" | "FAILED";
  crawler_type: string;
  url: string;
}

interface ProviderKeys {
  gemini: string;
  openai: string;
  anthropic: string;
}

interface DashboardState {
  activeTab: string;
  projects: Project[];
  selectedProjectId: string;
  components: UIComponent[];
  selectedComponentId: string;
  executions: Execution[];
  logs: string[];
  prompt: string;
  apiBaseUrl: string;
  mockMode: boolean;
  keys: ProviderKeys;
  
  setActiveTab: (tab: string) => void;
  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  setSelectedProjectId: (id: string) => void;
  setComponents: (components: UIComponent[]) => void;
  updateComponentCode: (id: string, code: string) => void;
  setSelectedComponentId: (id: string) => void;
  setExecutions: (executions: Execution[]) => void;
  addExecution: (execution: Execution) => void;
  addLog: (log: string) => void;
  clearLogs: () => void;
  setPrompt: (prompt: string) => void;
  setApiBaseUrl: (url: string) => void;
  setMockMode: (mode: boolean) => void;
  setKeys: (keys: Partial<ProviderKeys>) => void;
}

export const useStore = create<DashboardState>((set) => ({
  activeTab: "projects",
  projects: [
    {
      id: "mock-project-id-1",
      name: "E-Commerce Landing Page",
      description: "Responsive hero, products grid, and interactive cart button layout.",
      user_id: "default-user"
    },
    {
      id: "mock-project-id-2",
      name: "SaaS Admin Dashboard",
      description: "Sidebar, headers, charts, and dark style layout panels.",
      user_id: "default-user"
    }
  ],
  selectedProjectId: "mock-project-id-1",
  components: [
    {
      id: "mock-component-id-1",
      project_id: "mock-project-id-1",
      name: "HeroSection",
      code: `import React from 'react';

export default function HeroSection() {
  return (
    <section className="w-full py-20 px-6 flex flex-col items-center justify-center text-center bg-zinc-950 text-white font-sans">
      <div className="max-w-4xl w-full flex flex-col items-center">
        <span className="text-emerald-500 font-semibold tracking-wider uppercase text-sm mb-3">Next-Generation UI Builder</span>
        <h1 className="text-5xl font-extrabold tracking-tight mb-6 leading-tight">
          Design Beautiful Websites <br />
          <span className="bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">Using AI Orchestration</span>
        </h1>
        <p className="text-zinc-400 text-lg max-w-2xl mb-8 leading-relaxed">
          Instantly crawl existing layout styles and synthesize React components styled with utility Tailwind classes and design parameters.
        </p>
        <div className="flex gap-4">
          <button className="px-6 py-3 rounded-lg font-semibold bg-emerald-500 hover:bg-emerald-600 text-black transition-colors duration-200" onClick={() => alert('Getting Started')}>
            Get Started
          </button>
          <button className="px-6 py-3 rounded-lg font-semibold bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700 transition-colors duration-200">
            Learn More
          </button>
        </div>
      </div>
    </section>
  );
}`,
      type: "landing"
    },
    {
      id: "mock-component-id-2",
      project_id: "mock-project-id-1",
      name: "ProductGrid",
      code: `import React from 'react';

export default function ProductGrid() {
  const products = [
    { id: 1, name: 'Minimalist Chair', price: '$120', img: 'https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=400' },
    { id: 2, name: 'Ceramic Vase', price: '$45', img: 'https://images.unsplash.com/photo-1578500494198-246f612d3b3d?w=400' },
    { id: 3, name: 'Concrete Planter', price: '$30', img: 'https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=400' }
  ];

  return (
    <section className="w-full py-16 px-6 bg-zinc-900 text-white font-sans">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold mb-8 text-center sm:text-left">Featured Products</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-8">
          {products.map(p => (
            <div key={p.id} className="bg-zinc-800 border border-zinc-700 rounded-xl overflow-hidden group hover:scale-[1.02] transition-transform duration-200">
              <div className="h-64 bg-zinc-700 relative overflow-hidden">
                <img src={p.img} alt={p.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
              </div>
              <div className="p-5 flex justify-between items-center">
                <div>
                  <h3 className="font-semibold text-lg">{p.name}</h3>
                  <p className="text-emerald-500 font-medium mt-1">{p.price}</p>
                </div>
                <button className="px-4 py-2 rounded bg-zinc-700 hover:bg-emerald-500 hover:text-black font-semibold text-sm transition-colors" onClick={() => alert('Added to Cart')}>
                  Add
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}`,
      type: "grid"
    },
    {
      id: "mock-component-id-3",
      project_id: "mock-project-id-2",
      name: "DashboardLayout",
      code: `import React from 'react';

export default function DashboardLayout() {
  return (
    <div className="flex h-screen bg-zinc-950 text-white font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-zinc-900 border-r border-zinc-800 p-6 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center font-bold text-black text-lg">U</div>
            <span className="text-xl font-bold tracking-tight">UI AI BUILDER</span>
          </div>
          <nav className="space-y-2">
            <a href="#" className="flex items-center gap-3 px-4 py-2 rounded-lg bg-zinc-800 text-white font-medium">
              <span>Dashboard</span>
            </a>
            <a href="#" className="flex items-center gap-3 px-4 py-2 rounded-lg text-zinc-400 hover:bg-zinc-800 hover:text-white font-medium transition-colors">
              <span>Projects</span>
            </a>
            <a href="#" className="flex items-center gap-3 px-4 py-2 rounded-lg text-zinc-400 hover:bg-zinc-800 hover:text-white font-medium transition-colors">
              <span>Settings</span>
            </a>
          </nav>
        </div>
        <div className="text-sm text-zinc-500">v1.0.0</div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 p-8 overflow-y-auto">
        <header className="flex justify-between items-center mb-8 border-b border-zinc-800 pb-4">
          <h1 className="text-2xl font-bold">Workspace Overview</h1>
          <button className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-black font-semibold transition-colors" onClick={() => alert('New Component')}>
            Generate Component
          </button>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-xl">
            <div className="text-zinc-400 text-sm font-medium mb-1">Total Crawled Sites</div>
            <div className="text-3xl font-extrabold">24</div>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-xl">
            <div className="text-zinc-400 text-sm font-medium mb-1">Generated Components</div>
            <div className="text-3xl font-extrabold">85</div>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-xl">
            <div className="text-zinc-400 text-sm font-medium mb-1">Active Worker Jobs</div>
            <div className="text-3xl font-extrabold text-emerald-500">Idle</div>
          </div>
        </div>
      </main>
    </div>
  );
}`,
      type: "layout"
    }
  ],
  selectedComponentId: "mock-component-id-1",
  executions: [
    {
      id: "exec_001",
      project_id: "mock-project-id-1",
      date: "2026-06-22 15:40:02",
      status: "COMPLETED",
      crawler_type: "Playwright",
      url: "https://example.com"
    },
    {
      id: "exec_002",
      project_id: "mock-project-id-2",
      date: "2026-06-22 16:30:15",
      status: "COMPLETED",
      crawler_type: "Crawl4AI",
      url: "https://another-domain.com"
    }
  ],
  logs: [
    "[SYSTEM] Starting dashboard client workspace...",
    "[SYSTEM] Zustand store loaded with default mocked states.",
    "[API] Fallback offline modes initialized for development."
  ],
  prompt: "Add a dark mode card grid block section with emerald accent buttons and visual density spacing profile",
  apiBaseUrl: "http://localhost:8000",
  mockMode: true,
  keys: {
    gemini: "",
    openai: "",
    anthropic: ""
  },
  
  setActiveTab: (tab) => set({ activeTab: tab }),
  setProjects: (projects) => set({ projects }),
  addProject: (project) => set((state) => ({ projects: [...state.projects, project] })),
  setSelectedProjectId: (id) => set({ selectedProjectId: id }),
  setComponents: (components) => set({ components }),
  updateComponentCode: (id, code) => set((state) => ({
    components: state.components.map(c => c.id === id ? { ...c, code } : c)
  })),
  setSelectedComponentId: (id) => set({ selectedComponentId: id }),
  setExecutions: (executions) => set({ executions }),
  addExecution: (execution) => set((state) => ({ executions: [execution, ...state.executions] })),
  addLog: (log) => set((state) => ({ logs: [...state.logs, log] })),
  clearLogs: () => set({ logs: [] }),
  setPrompt: (prompt) => set({ prompt }),
  setApiBaseUrl: (url) => set({ apiBaseUrl: url }),
  setMockMode: (mode) => set({ mockMode: mode }),
  setKeys: (keys) => set((state) => ({ keys: { ...state.keys, ...keys } }))
}));
