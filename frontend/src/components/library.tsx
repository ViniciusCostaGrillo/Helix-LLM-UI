"use client";

import React, { useState, useEffect } from "react";
import { useStore, Project } from "../lib/store";
import {
  FolderGit2,
  Plus,
  Search,
  Filter,
  FileCode,
  Palette,
  BookOpen,
  HardDrive,
  Eye,
  Video,
  Binary,
  FolderUp,
  Award,
  Activity,
  Database,
  Trash2,
  RefreshCw,
  Clock,
  ArrowUpRight
} from "lucide-react";

interface MonitoredFile {
  name: string;
  size: number;
  modified: number;
  relative_path: string;
}

interface GroupedFiles {
  components: MonitoredFile[];
  design_systems: MonitoredFile[];
  skills: MonitoredFile[];
  prompt_templates: MonitoredFile[];
  images: MonitoredFile[];
  videos: MonitoredFile[];
  "3d": MonitoredFile[];
  references: MonitoredFile[];
}

export default function LibraryView() {
  const {
    apiBaseUrl,
    projects,
    selectedProjectId,
    setSelectedProjectId,
    addProject,
    addLog
  } = useStore();

  const [activeSubTab, setActiveSubTab] = useState<"files" | "masterpieces" | "jobs">("files");

  // Project state
  const [newProjName, setNewProjName] = useState("");
  const [newProjDesc, setNewProjDesc] = useState("");

  // Files state
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [fileSearch, setFileSearch] = useState("");
  const [fileCategoryFilter, setFileCategoryFilter] = useState<string>("all");
  const [groupedFiles, setGroupedFiles] = useState<GroupedFiles>({
    components: [],
    design_systems: [],
    skills: [],
    prompt_templates: [],
    images: [],
    videos: [],
    "3d": [],
    references: []
  });

  // Masterpieces state
  const [masterpieces, setMasterpieces] = useState<any[]>([]);
  const [newMpName, setNewMpName] = useState("");
  const [newMpUrl, setNewMpUrl] = useState("");
  const [newMpCategory, setNewMpCategory] = useState("luxury");

  // Ingestion Queue state
  const [queueJobs, setQueueJobs] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({
    websites: 0,
    masterpieces: 0,
    components: 0,
    assets: 0
  });

  const fetchFiles = async () => {
    setLoadingFiles(true);
    try {
      const res = await fetch(`${apiBaseUrl}/knowledge/files`);
      if (res.ok) {
        const data = await res.json();
        setGroupedFiles(data);
      }
    } catch (err: any) {
      addLog(`[SYSTEM] Error fetching library files: ${err.message}`);
    } finally {
      setLoadingFiles(false);
    }
  };

  const fetchStatsAndHistory = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/importer/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats({
          websites: data.websites_count,
          masterpieces: data.masterpieces_count,
          components: data.components_count,
          assets: data.assets_count
        });
      }

      const historyRes = await fetch(`${apiBaseUrl}/importer/history`);
      if (historyRes.ok) {
        const historyData = await historyRes.json();
        const mps = historyData.filter((d: any) => d.is_masterpiece);
        if (mps.length > 0) {
          setMasterpieces(mps.map((m: any, idx: number) => ({
            id: m.id || idx.toString(),
            name: m.metadata?.title || m.url.replace("https://", "").split("/")[0],
            url: m.url,
            score: m.masterpiece_score || 95.0,
            category: m.metadata?.colors ? ["design"] : ["general"]
          })));
        } else {
          // Fallback static masterpieces for beautiful presentation
          setMasterpieces([
            { id: "1", name: "Linear App Style", url: "https://linear.app", score: 98.4, category: ["saas", "minimal"] },
            { id: "2", name: "Stripe Checkout", url: "https://stripe.com", score: 97.2, category: ["fintech", "design"] },
            { id: "3", name: "Vercel Deployments", url: "https://vercel.com", score: 96.5, category: ["developer", "dashboard"] }
          ]);
        }
      }
    } catch (err) {}
  };

  const fetchQueue = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/importer/queue`);
      if (res.ok) {
        const data = await res.json();
        setQueueJobs(data);
      }
    } catch (err) {}
  };

  useEffect(() => {
    fetchFiles();
    fetchStatsAndHistory();
    fetchQueue();

    const interval = setInterval(() => {
      fetchQueue();
      fetchStatsAndHistory();
    }, 5000);

    return () => clearInterval(interval);
  }, [apiBaseUrl]);

  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjName.trim()) return;

    const newProj: Project = {
      id: `proj_${Date.now()}`,
      name: newProjName,
      description: newProjDesc || "Nenhuma descrição fornecida.",
      user_id: "default-user"
    };

    addProject(newProj);
    setSelectedProjectId(newProj.id);
    addLog(`[PROJECT] Projeto criado: ${newProj.name}`);
    setNewProjName("");
    setNewProjDesc("");
  };

  const handlePromoteMasterpiece = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMpName || !newMpUrl) return;

    try {
      const res = await fetch(`${apiBaseUrl}/importer/promote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newMpName,
          url: newMpUrl,
          category: [newMpCategory]
        })
      });

      if (res.ok) {
        addLog(`[SYSTEM] Referência promovida para MASTERPIECE: ${newMpName}`);
        setNewMpName("");
        setNewMpUrl("");
        fetchStatsAndHistory();
      }
    } catch (err) {}
  };

  const handleDemoteMasterpiece = async (url: string) => {
    try {
      const res = await fetch(`${apiBaseUrl}/importer/demote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
      });
      if (res.ok) {
        addLog(`[SYSTEM] Referência removida de masterpieces: ${url}`);
        fetchStatsAndHistory();
      }
    } catch (err) {}
  };

  const getFolderIcon = (category: string) => {
    switch (category) {
      case "components":
        return <FileCode className="w-4 h-4 text-emerald-400" />;
      case "design_systems":
        return <Palette className="w-4 h-4 text-emerald-400" />;
      case "skills":
        return <BookOpen className="w-4 h-4 text-emerald-400" />;
      case "prompt_templates":
        return <HardDrive className="w-4 h-4 text-emerald-400" />;
      case "images":
        return <Eye className="w-4 h-4 text-emerald-400" />;
      case "videos":
        return <Video className="w-4 h-4 text-emerald-400" />;
      case "3d":
        return <Binary className="w-4 h-4 text-emerald-400" />;
      default:
        return <FolderUp className="w-4 h-4 text-zinc-400" />;
    }
  };

  // Process and filter files
  const allFilesList: { cat: string; file: MonitoredFile }[] = [];
  Object.keys(groupedFiles).forEach((cat) => {
    const files = (groupedFiles as any)[cat] || [];
    files.forEach((f: MonitoredFile) => {
      allFilesList.push({ cat, file: f });
    });
  });

  const filteredFiles = allFilesList.filter((item) => {
    const matchesSearch = item.file.name.toLowerCase().includes(fileSearch.toLowerCase()) ||
                          item.file.relative_path.toLowerCase().includes(fileSearch.toLowerCase());
    const matchesCat = fileCategoryFilter === "all" || item.cat === fileCategoryFilter;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 select-none font-sans">
      
      {/* Left panel: Projects control */}
      <div className="lg:col-span-4 space-y-6">
        <div className="bg-zinc-900/40 border border-white/5 rounded-2xl p-6 space-y-5">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <FolderGit2 className="w-4 h-4 text-emerald-500" /> Projetos Ativos
          </h3>

          <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-zinc-800">
            {projects.length === 0 ? (
              <div className="py-8 px-4 text-center border border-dashed border-zinc-800 rounded-xl text-zinc-500 text-xs font-sans leading-relaxed">
                Nenhum projeto ativo.<br />Crie um projeto abaixo para iniciar a geração de componentes.
              </div>
            ) : (
              projects.map((proj) => {
                const isSelected = proj.id === selectedProjectId;
                return (
                  <div
                    key={proj.id}
                    onClick={() => setSelectedProjectId(proj.id)}
                    className={`p-4 rounded-xl border text-left cursor-pointer transition-all ${
                      isSelected
                        ? "bg-zinc-900 border-emerald-500/80 shadow-md shadow-emerald-500/5 scale-[1.01]"
                        : "bg-zinc-950/40 border-zinc-800 hover:border-zinc-700"
                    }`}
                  >
                    <span className={`text-xs font-bold block ${isSelected ? "text-emerald-400" : "text-white"}`}>
                      {proj.name}
                    </span>
                    <span className="text-[10px] text-zinc-500 mt-1 block leading-relaxed line-clamp-2">
                      {proj.description}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Initialize project form */}
        <div className="bg-zinc-900/40 border border-white/5 rounded-2xl p-6">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-4">
            <Plus className="w-4 h-4 text-emerald-500" /> Novo Projeto
          </h3>
          <form onSubmit={handleCreateProject} className="space-y-3.5">
            <div>
              <input
                type="text"
                required
                placeholder="Nome do Projeto"
                value={newProjName}
                onChange={(e) => setNewProjName(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono font-medium"
              />
            </div>
            <div>
              <input
                type="text"
                placeholder="Descrição (ex: Landing Page SaaS)"
                value={newProjDesc}
                onChange={(e) => setNewProjDesc(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono font-medium"
              />
            </div>
            <button
              type="submit"
              className="w-full py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-black font-bold text-xs cursor-pointer transition-colors"
            >
              Criar Projeto
            </button>
          </form>
        </div>
      </div>

      {/* Right panel: Library tabs */}
      <div className="lg:col-span-8 space-y-6">
        
        {/* Navigation tabs */}
        <div className="flex justify-between items-center border-b border-zinc-800/80 pb-3">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveSubTab("files")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                activeSubTab === "files" ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400" : "text-zinc-450 hover:text-white"
              }`}
            >
              Arquivos Monitorados
            </button>
            <button
              onClick={() => setActiveSubTab("masterpieces")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                activeSubTab === "masterpieces" ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400" : "text-zinc-450 hover:text-white"
              }`}
            >
              Masterpieces ⭐
            </button>
            <button
              onClick={() => setActiveSubTab("jobs")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                activeSubTab === "jobs" ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400" : "text-zinc-450 hover:text-white"
              }`}
            >
              Fila de Ingestão
            </button>
          </div>

          <span className="text-[10px] font-mono text-zinc-550 flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5" />
            <span>ChromaDB Ativo</span>
          </span>
        </div>

        {/* SUBTAB 1: Monitored files */}
        {activeSubTab === "files" && (
          <div className="bg-zinc-900/20 border border-white/5 rounded-2xl p-6 space-y-5">
            
            {/* Search and filters */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="w-3.5 h-3.5 text-zinc-550 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Pesquisar arquivos..."
                  value={fileSearch}
                  onChange={(e) => setFileSearch(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-9 pr-4 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-sans"
                />
              </div>

              <div className="flex items-center gap-2">
                <Filter className="w-3.5 h-3.5 text-zinc-500" />
                <select
                  value={fileCategoryFilter}
                  onChange={(e) => setFileCategoryFilter(e.target.value)}
                  className="bg-zinc-950 border border-zinc-800 text-zinc-400 text-xs rounded-lg px-2.5 py-2 focus:outline-none"
                >
                  <option value="all">Todas categorias</option>
                  <option value="components">Components</option>
                  <option value="design_systems">Design Systems</option>
                  <option value="skills">Skills</option>
                  <option value="references">References</option>
                </select>
              </div>
            </div>

            {/* List */}
            {loadingFiles ? (
              <div className="py-12 flex justify-center text-zinc-500 text-xs gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-emerald-400" /> Carregando diretório de knowledge...
              </div>
            ) : filteredFiles.length === 0 ? (
              <div className="py-12 border border-dashed border-zinc-800/80 rounded-xl text-center text-zinc-550 text-xs font-sans">
                Nenhum arquivo indexado na pasta `knowledge_input/` ainda.
              </div>
            ) : (
              <div className="border border-zinc-800 rounded-xl overflow-hidden bg-zinc-950/40">
                <table className="w-full text-left text-xs font-sans border-collapse">
                  <thead>
                    <tr className="bg-zinc-900/60 border-b border-zinc-800 text-zinc-450 uppercase font-mono text-[9px] tracking-wider">
                      <th className="px-4 py-3">Arquivo</th>
                      <th className="px-4 py-3">Categoria</th>
                      <th className="px-4 py-3 text-right">Tamanho</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFiles.map((item, idx) => (
                      <tr key={idx} className="border-b border-zinc-850 hover:bg-white/5 transition-colors">
                        <td className="px-4 py-3 flex items-center gap-2">
                          {getFolderIcon(item.cat)}
                          <span className="font-mono text-zinc-300 font-semibold">{item.file.name}</span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-900 border border-zinc-850 text-zinc-400 uppercase tracking-widest font-mono">
                            {item.cat}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-zinc-500">
                          {(item.file.size / 1024).toFixed(1)} KB
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* SUBTAB 2: Masterpieces */}
        {activeSubTab === "masterpieces" && (
          <div className="space-y-6">
            
            {/* Promote form */}
            <div className="bg-zinc-900/20 border border-white/5 rounded-2xl p-6">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-3">
                <Award className="w-4 h-4 text-emerald-500" /> Promover Referência a Masterpiece
              </h4>
              <form onSubmit={handlePromoteMasterpiece} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <input
                  type="text"
                  required
                  placeholder="Nome (ex: Linear UI)"
                  value={newMpName}
                  onChange={(e) => setNewMpName(e.target.value)}
                  className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono font-medium"
                />
                <input
                  type="url"
                  required
                  placeholder="URL (ex: https://linear.app)"
                  value={newMpUrl}
                  onChange={(e) => setNewMpUrl(e.target.value)}
                  className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono font-medium"
                />
                <div className="flex gap-2">
                  <select
                    value={newMpCategory}
                    onChange={(e) => setNewMpCategory(e.target.value)}
                    className="bg-zinc-950 border border-zinc-800 text-zinc-450 text-xs rounded-lg px-2 py-2 focus:outline-none flex-1"
                  >
                    <option value="luxury">Luxury UI</option>
                    <option value="saas">SaaS UI</option>
                    <option value="minimal">Minimalist</option>
                  </select>
                  <button
                    type="submit"
                    className="px-4 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-black font-bold text-xs cursor-pointer transition-colors"
                  >
                    Promover
                  </button>
                </div>
              </form>
            </div>

            {/* List */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {masterpieces.map((mp) => (
                <div
                  key={mp.id}
                  className="bg-zinc-900/20 border border-white/5 p-4 rounded-xl flex flex-col justify-between h-36 relative overflow-hidden group hover:border-emerald-500/20 transition-all duration-200"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 uppercase tracking-widest">
                        Masterpiece
                      </span>
                      <h4 className="text-xs font-bold text-white mt-2 group-hover:text-emerald-400 transition-colors">
                        {mp.name}
                      </h4>
                      <span className="text-[10px] text-zinc-500 font-mono block mt-0.5 truncate">
                        {mp.url}
                      </span>
                    </div>

                    <button
                      onClick={() => handleDemoteMasterpiece(mp.url)}
                      className="p-1 rounded hover:bg-zinc-800 text-zinc-550 hover:text-rose-500 transition-colors cursor-pointer"
                      title="Remover"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="flex justify-between items-center border-t border-zinc-800/40 pt-2 text-[10px] font-mono text-zinc-500">
                    <span className="flex items-center gap-1">
                      Score: <span className="text-emerald-400 font-bold">{mp.score}</span>
                    </span>
                    <a
                      href={mp.url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-0.5 hover:text-white transition-colors"
                    >
                      Visitar <ArrowUpRight className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SUBTAB 3: Crawler Jobs Queue */}
        {activeSubTab === "jobs" && (
          <div className="bg-zinc-900/20 border border-white/5 rounded-2xl p-6 space-y-5">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-500 animate-pulse" /> Tarefas Ativas de Ingestão
            </h4>

            {queueJobs.length === 0 ? (
              <div className="py-12 border border-dashed border-zinc-800/80 rounded-xl text-center text-zinc-550 text-xs font-sans">
                Nenhuma tarefa ativa no momento. Inicie um crawler enviando uma URL no Chat!
              </div>
            ) : (
              <div className="space-y-4">
                {queueJobs.map((job) => (
                  <div key={job.id} className="border border-zinc-800 bg-zinc-950 p-4 rounded-xl space-y-2.5">
                    <div className="flex justify-between items-start text-xs">
                      <div>
                        <span className="font-mono text-zinc-300 font-semibold block truncate max-w-md">
                          {job.url}
                        </span>
                        <span className="text-[10px] text-zinc-650 font-mono">
                          ID: {job.id} • Criado em: {job.created_at}
                        </span>
                      </div>
                      <span className="px-2.5 py-0.5 rounded bg-zinc-900 border border-zinc-850 text-emerald-400 text-[10px] uppercase font-bold tracking-wider">
                        {job.status}
                      </span>
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between text-[9px] font-mono text-zinc-500">
                        <span>Estágio: {job.stage}</span>
                        <span>{job.progress}% • Decorrido: {job.elapsed}s</span>
                      </div>
                      <div className="w-full h-1 bg-zinc-900 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
