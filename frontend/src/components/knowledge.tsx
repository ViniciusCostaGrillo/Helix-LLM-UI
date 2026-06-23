"use client";

import React, { useState, useEffect, useRef } from "react";
import { useStore } from "../lib/store";
import {
  FileUp,
  FolderUp,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
  FileCode,
  HardDrive,
  Palette,
  Binary,
  BookOpen,
  Eye,
  Video
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

export default function KnowledgeView() {
  const { apiBaseUrl, addLog } = useStore();
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"IDLE" | "UPLOADING" | "SUCCESS" | "ERROR">("IDLE");
  const [uploadResults, setUploadResults] = useState<any[]>([]);
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
  const [loadingFiles, setLoadingFiles] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchFiles = async () => {
    setLoadingFiles(true);
    try {
      const res = await fetch(`${apiBaseUrl}/knowledge/files`);
      if (!res.ok) throw new Error("Failed to fetch monitored files.");
      const data = await res.json();
      setGroupedFiles(data);
    } catch (err: any) {
      addLog(`[SYSTEM] Error fetching knowledge directories: ${err.message}`);
    } finally {
      setLoadingFiles(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, [apiBaseUrl]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFiles(e.dataTransfer.files);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFiles(e.target.files);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const uploadFiles = async (fileList: FileList) => {
    setUploadStatus("UPLOADING");
    setUploadResults([]);
    addLog(`[SYSTEM] Initiating upload for ${fileList.length} files...`);

    const formData = new FormData();
    for (let i = 0; i < fileList.length; i++) {
      formData.append("files", fileList[i]);
    }

    try {
      const res = await fetch(`${apiBaseUrl}/knowledge/upload`, {
        method: "POST",
        body: formData
      });

      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();

      setUploadStatus("SUCCESS");
      setUploadResults(data.uploaded_files);
      addLog(`[SYSTEM] Successfully uploaded and routed ${data.count} files.`);
      
      // Refresh database files list
      fetchFiles();
    } catch (err: any) {
      setUploadStatus("ERROR");
      addLog(`[SYSTEM] File upload failed: ${err.message}`);
    }
  };

  const getFolderIcon = (category: string) => {
    switch (category) {
      case "components":
        return <FileCode className="w-5 h-5 text-sky-400" />;
      case "design_systems":
        return <Palette className="w-5 h-5 text-emerald-400" />;
      case "skills":
        return <BookOpen className="w-5 h-5 text-indigo-400" />;
      case "prompt_templates":
        return <HardDrive className="w-5 h-5 text-teal-400" />;
      case "images":
        return <Eye className="w-5 h-5 text-purple-400" />;
      case "videos":
        return <Video className="w-5 h-5 text-pink-400" />;
      case "3d":
        return <Binary className="w-5 h-5 text-amber-400" />;
      default:
        return <FolderUp className="w-5 h-5 text-zinc-400" />;
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="space-y-8 w-full font-sans">
      {/* Upload Drag & Drop Section */}
      <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl space-y-6 relative overflow-hidden">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <FileUp className="text-emerald-500" /> Knowledge File Ingestion
            </h2>
            <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
              Drag files here. The system automatically identifies extensions and targets corresponding directories.
            </p>
          </div>
          <button
            onClick={fetchFiles}
            className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700 transition-all cursor-pointer flex items-center gap-2 text-xs font-bold"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingFiles ? "animate-spin" : ""}`} />
            Refresh Library
          </button>
        </div>

        {/* Drag and Drop Box */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={triggerFileInput}
          className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center gap-4 cursor-pointer transition-all duration-300 ${
            dragActive
              ? "border-emerald-500 bg-emerald-500/5 scale-[1.01]"
              : "border-zinc-800 hover:border-zinc-700 hover:bg-zinc-950/20"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileChange}
            className="hidden"
          />
          <div className="w-14 h-14 rounded-2xl bg-zinc-950 border border-zinc-800 flex items-center justify-center text-zinc-400 group-hover:text-white">
            <FolderUp className="w-7 h-7 text-emerald-400 animate-pulse" />
          </div>
          <div className="text-center space-y-1">
            <p className="text-sm font-bold text-white">
              Drag & drop files here, or click to browse
            </p>
            <p className="text-xs text-zinc-550 max-w-md leading-relaxed">
              Supports Components (`.tsx`, `.jsx`), 3D Assets (`.glb`), Style Sheets (`.yaml`, `.json`), Text Links (`.txt`), and Media (`.png`, `.mp4`).
            </p>
          </div>
        </div>

        {/* Upload Status Feedbacks */}
        {uploadStatus === "UPLOADING" && (
          <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-950 flex items-center gap-3 text-sm text-zinc-400">
            <Loader2 className="w-5 h-5 text-emerald-500 animate-spin" />
            <span>Processing and sorting files...</span>
          </div>
        )}

        {uploadStatus === "SUCCESS" && (
          <div className="space-y-3">
            <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 flex items-center gap-3 text-sm text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
              <span>Files successfully routed and saved. Ingestion loop triggers automatically in the background.</span>
            </div>
            <div className="max-h-48 overflow-y-auto border border-zinc-800 bg-zinc-950 rounded-xl p-3 divide-y divide-zinc-900">
              {uploadResults.map((res, idx) => (
                <div key={idx} className="py-2.5 flex justify-between items-center text-xs">
                  <div className="flex items-center gap-2.5">
                    {res.status === "success" ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-400" />
                    )}
                    <span className="font-mono text-zinc-300 font-semibold">{res.filename}</span>
                  </div>
                  <div className="flex gap-4 items-center">
                    <span className="px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-400 text-[10px] uppercase font-bold tracking-wider">
                      {res.category}
                    </span>
                    <span className="font-mono text-zinc-500">{res.target_path || res.error}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {uploadStatus === "ERROR" && (
          <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/5 flex items-center gap-3 text-sm text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span>Failed to route files. Make sure the API backend server is active.</span>
          </div>
        )}
      </div>

      {/* Folders and Files Directory Trees Grid */}
      <div className="space-y-4">
        <h3 className="text-sm font-extrabold uppercase tracking-widest text-zinc-400">
          Monitored Folders Library
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Object.entries(groupedFiles).map(([category, files]) => (
            <div key={category} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 flex flex-col justify-between h-72">
              <div>
                <div className="flex justify-between items-center mb-4 border-b border-zinc-800/60 pb-3">
                  <div className="flex items-center gap-2">
                    {getFolderIcon(category)}
                    <span className="text-sm font-extrabold capitalize text-white tracking-wide">
                      {category.replace("_", " ")}
                    </span>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-zinc-950 text-zinc-400 border border-zinc-850">
                    {files.length}
                  </span>
                </div>

                <div className="overflow-y-auto max-h-40 space-y-2 pr-1.5 scrollbar-thin scrollbar-thumb-zinc-800">
                  {files.length === 0 ? (
                    <span className="text-[11px] text-zinc-650 block text-center mt-8 italic">
                      Folder is empty
                    </span>
                  ) : (
                    (files as MonitoredFile[]).map((file: MonitoredFile, idx: number) => (
                      <div key={idx} className="flex justify-between items-center p-2 rounded-lg bg-zinc-950 border border-zinc-850 hover:border-zinc-800 transition-colors">
                        <span className="text-xs truncate font-mono text-zinc-300 font-semibold max-w-[120px] block" title={file.name}>
                          {file.name}
                        </span>
                        <span className="text-[10px] font-mono text-zinc-550">
                          {formatSize(file.size)}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
              
              <div className="border-t border-zinc-800/40 pt-3 text-[10px] font-mono text-zinc-600 uppercase flex justify-between tracking-wider">
                <span>FOLDER TARGET</span>
                <span>/knowledge_input/{category}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
