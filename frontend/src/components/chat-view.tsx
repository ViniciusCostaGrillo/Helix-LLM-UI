"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useStore, ChatMessage, UIComponent } from "../lib/store";
import {
  Send,
  Bot,
  User,
  Sparkles,
  Terminal,
  Code,
  FolderGit2,
  Layers,
  Settings as SettingsIcon,
  Play,
  CheckCircle2,
  AlertCircle,
  FileCode,
  Globe,
  Database,
  Trash2,
  Paperclip
} from "lucide-react";

export default function ChatView() {
  const {
    apiBaseUrl,
    mockMode,
    chatMessages,
    addChatMessage,
    updateChatMessage,
    clearChatMessages,
    projects,
    selectedProjectId,
    setSelectedProjectId,
    components,
    setComponents,
    setSelectedComponentId,
    setActiveTab,
    addLog
  } = useStore();

  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [attachedUrl, setAttachedUrl] = useState("");
  const [crawlMode, setCrawlMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const activeProject = projects.find((p) => p.id === selectedProjectId) || projects[0];

  const handleSuggestionClick = (actionType: "crawl" | "generate" | "search") => {
    if (actionType === "crawl") {
      setInput("Extrair estilos do site: https://linear.app");
      setCrawlMode(true);
    } else if (actionType === "generate") {
      setInput("Criar uma seção Hero minimalista com fundo escuro, texto em gradiente esmeralda e botão com micro-animação");
      setCrawlMode(false);
    } else if (actionType === "search") {
      setInput("Buscar no banco de dados vetorial padrões de cores e fontes para design premium");
      setCrawlMode(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;

    const userMessageContent = input.trim();
    setInput("");
    setIsSending(true);

    const userMsgId = `msg_${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: "user",
      content: userMessageContent,
      timestamp: new Date().toLocaleTimeString().slice(0, 5)
    };

    addChatMessage(userMsg);

    const assistantMsgId = `msg_${Date.now() + 1}`;
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: "assistant",
      content: "Analisando sua solicitação...",
      timestamp: new Date().toLocaleTimeString().slice(0, 5),
      status: "pending",
      logs: []
    };

    addChatMessage(assistantMsg);

    // Detect if user wants to crawl a URL
    const extractUrl = (text: string): string | null => {
      const explicitRegex = /(https?:\/\/[^\s]+)/g;
      const matches = text.match(explicitRegex);
      if (matches && matches.length > 0) return matches[0];
      
      const domainRegex = /([a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}(?:\/[^\s]*)?)/g;
      const domainMatches = text.match(domainRegex);
      if (domainMatches && domainMatches.length > 0) {
        const candidate = domainMatches[0];
        if (candidate.includes(".") && !candidate.endsWith(".") && !candidate.startsWith(".") && candidate.length > 4) {
          return `https://${candidate}`;
        }
      }
      return null;
    };

    const detectedUrl = extractUrl(userMessageContent);
    const isCrawlRequest = crawlMode || detectedUrl !== null || userMessageContent.toLowerCase().includes("extrair") || userMessageContent.toLowerCase().includes("crawl");

    if (isCrawlRequest) {
      let targetUrl = detectedUrl;
      if (!targetUrl && crawlMode) {
        targetUrl = userMessageContent.trim().startsWith("http") 
          ? userMessageContent.trim() 
          : `https://${userMessageContent.trim()}`;
      }
      if (!targetUrl) {
        targetUrl = "https://linear.app";
      }
      await runCrawlWorkflow(assistantMsgId, targetUrl);
    } else if (userMessageContent.toLowerCase().includes("buscar") || userMessageContent.toLowerCase().includes("rag") || userMessageContent.toLowerCase().includes("pesquisar")) {
      await runRAGQueryWorkflow(assistantMsgId, userMessageContent);
    } else {
      await runCodegenWorkflow(assistantMsgId, userMessageContent);
    }

    setIsSending(false);
    setCrawlMode(false);
  };

  // 1. CRAWL WORKFLOW
  const runCrawlWorkflow = async (assistantMsgId: string, url: string) => {
    updateChatMessage(assistantMsgId, {
      content: `Iniciando o pipeline de extração e análise visual para o site: **${url}**...`,
      status: "running",
      logs: ["[SYSTEM] Solicitando importação da URL no backend..."]
    });

    if (mockMode) {
      const steps = [
        "[CRAWLER] Iniciando navegador headless Chrome via Playwright...",
        "[CRAWLER] Capturando captura de tela e extraindo código HTML/CSS bruto...",
        "[EXTRACTOR] Analisando hierarquia DOM e árvores de estilos CSS...",
        "[EXTRACTOR] Árvore DOM analisada. Fontes detectadas: [JetBrains Mono, Inter], Cores: [#09090b, #10b981].",
        "[VISION] Calculando densidade visual e perfis de espaçamento...",
        "[ANALYZER] Gerando guidelines de tokens de design via modelo de IA...",
        "[CODEGEN] Convertendo especificações visuais em componentes estruturados...",
        "[DATASET] Compactando manifesto do site e componentes gerados...",
        "[RAG] Vetorizando layout e inserindo embeddings na coleção ChromaDB...",
        "[SYSTEM] Importação e vetorização concluídas com sucesso!"
      ];

      let currentLogs: string[] = ["[SYSTEM] Solicitando importação da URL no backend..."];
      for (const step of steps) {
        await new Promise((resolve) => setTimeout(resolve, 800));
        currentLogs = [...currentLogs, step];
        updateChatMessage(assistantMsgId, { logs: currentLogs });
      }

      updateChatMessage(assistantMsgId, {
        content: `O site **${url}** foi processado e vetorizado no ChromaDB com sucesso!\n\nOs estilos visuais, fontes, cores e grids foram indexados no banco de dados RAG da Helix. Você já pode pedir para criar componentes baseados nessa referência no chat!`,
        status: "completed"
      });
      addLog(`[SYSTEM] URL enqueued & crawled successfully: ${url}`);
    } else {
      try {
        const response = await fetch(`${apiBaseUrl}/importer/url`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: url,
            promote_to_masterpiece: true,
            category: "saas"
          })
        });

        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        const jobId = data.job_id;

        updateChatMessage(assistantMsgId, {
          logs: [`[SYSTEM] Job enfileirado no backend. ID: ${jobId}. Monitorando progresso...`]
        });

        // Poll queue status
        let completed = false;
        let elapsed = 0;
        while (!completed && elapsed < 30) {
          await new Promise((resolve) => setTimeout(resolve, 2000));
          elapsed += 2;

          const queueRes = await fetch(`${apiBaseUrl}/importer/queue`);
          if (queueRes.ok) {
            const queue = await queueRes.json();
            const currentJob = queue.find((j: any) => j.id === jobId);
            if (currentJob) {
              const progressLogs = currentJob.logs || [];
              updateChatMessage(assistantMsgId, {
                logs: [`[SYSTEM] Progresso: ${currentJob.progress}% | Estágio: ${currentJob.stage}`, ...progressLogs]
              });

              if (currentJob.status === "completed" || currentJob.status === "success") {
                completed = true;
              } else if (currentJob.status === "failed") {
                throw new Error(currentJob.error_message || "Erro desconhecido no processamento do crawler.");
              }
            } else {
              completed = true; // Job finished and left the queue
            }
          }
        }

        updateChatMessage(assistantMsgId, {
          content: `Extração concluída para **${url}**!\n\nOs metadados visuais do site foram extraídos, categorizados e indexados no ChromaDB.`,
          status: "completed"
        });
      } catch (err: any) {
        updateChatMessage(assistantMsgId, {
          content: `Falha ao processar o crawler de importação: ${err.message}`,
          status: "failed",
          logs: [`[ERROR] ${err.message}`]
        });
      }
    }
  };

  // 2. RAG WORKFLOW
  const runRAGQueryWorkflow = async (assistantMsgId: string, prompt: string) => {
    updateChatMessage(assistantMsgId, {
      content: `Consultando o banco vetorial ChromaDB para buscar padrões relacionados à sua requisição...`,
      status: "running",
      logs: ["[SYSTEM] Realizando busca por similaridade de cosseno..."]
    });

    if (mockMode) {
      await new Promise((resolve) => setTimeout(resolve, 1200));
      updateChatMessage(assistantMsgId, {
        content: `Aqui estão as sugestões recuperadas do banco vetorial RAG para a sua consulta:\n\n` +
          `1. **Paleta de Cores**: Recomendado usar fundo escuro \`#09090b\` com bordas suaves \`#1e293b\` e realces em verde esmeralda \`#10b981\` para um visual premium.\n` +
          `2. **Tipografia**: Utilizar \`JetBrains Mono\` para títulos pequenos com estilo uppercase e \`Inter\` para o conteúdo, garantindo alta legibilidade.\n` +
          `3. **Espaçamento**: Margens largas com \`py-20\` ou \`py-24\` para seções principais, mantendo um perfil de densidade de layout limpo e minimalista.`,
        status: "completed",
        logs: [
          "[RAG] Consulta realizada com sucesso na coleção 'Masterpieces'.",
          "[RAG] Documento correspondente: 'style_rag_test_999' (Score: 0.985)",
          "[RAG] Documento correspondente: 'components_rag_test_124' (Score: 1.042)"
        ]
      });
    } else {
      try {
        const response = await fetch(`${apiBaseUrl}/rag/query`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: prompt, limit: 3 })
        });

        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();

        const contextLogs = data.retrieved_contexts.map(
          (c: any) => `[RAG] ID: ${c.id} | Coleção: ${c.collection} | Distância: ${c.distance.toFixed(4)}`
        );

        updateChatMessage(assistantMsgId, {
          content: `### Resultados do Banco Vetorial RAG\n\n${data.answer}`,
          status: "completed",
          logs: contextLogs
        });
      } catch (err: any) {
        updateChatMessage(assistantMsgId, {
          content: `Erro ao realizar a busca RAG: ${err.message}`,
          status: "failed",
          logs: [`[ERROR] ${err.message}`]
        });
      }
    }
  };

  // 3. CODEGEN WORKFLOW
  const runCodegenWorkflow = async (assistantMsgId: string, prompt: string) => {
    updateChatMessage(assistantMsgId, {
      content: `Planejando e gerando o código do componente baseado no prompt fornecido...`,
      status: "running",
      logs: ["[SYSTEM] Inicializando pipeline de geração no backend..."]
    });

    if (mockMode) {
      const steps = [
        "[CRAWLER] Verificando referências locais indexadas no ChromaDB...",
        "[ANALYZER] Estruturando plano visual para o componente solicitado...",
        "[CODEGEN] Gerando módulo React TSX estruturado...",
        "[CODEGEN] Validando classes utilitárias do TailwindCSS...",
        "[SYSTEM] Código do componente gerado com sucesso!"
      ];

      let currentLogs: string[] = ["[SYSTEM] Inicializando pipeline de geração no backend..."];
      for (const step of steps) {
        await new Promise((resolve) => setTimeout(resolve, 850));
        currentLogs = [...currentLogs, step];
        updateChatMessage(assistantMsgId, { logs: currentLogs });
      }

      const generatedCode = `import React from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';

export default function MinimalHero() {
  return (
    <section className="w-full py-28 px-8 bg-zinc-950 text-white font-mono flex flex-col items-center justify-center text-center border-b border-zinc-900">
      <div className="max-w-3xl flex flex-col items-center">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-widest mb-8 hover:scale-105 transition-transform duration-300">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Next Gen UI Generation</span>
        </div>
        
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight mb-6 leading-tight select-none">
          Code Beautiful Frontends <br />
          <span className="bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">
            Driven by Orchestration
          </span>
        </h1>
        
        <p className="text-zinc-400 text-sm max-w-xl mb-10 leading-relaxed font-sans">
          Crawl layout visual metrics, build layout vector databases, and construct ready-to-use clean React code components.
        </p>
        
        <div className="flex gap-4">
          <button className="px-6 py-3 rounded-lg font-bold bg-emerald-500 hover:bg-emerald-600 text-black transition-all duration-300 transform hover:-translate-y-0.5 flex items-center gap-2 shadow-lg shadow-emerald-500/15 cursor-pointer">
            <span>Iniciar Projeto</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <button className="px-6 py-3 rounded-lg font-bold bg-zinc-900 hover:bg-zinc-800 text-white border border-zinc-800 transition-all duration-300 transform hover:-translate-y-0.5 cursor-pointer">
            Documentação
          </button>
        </div>
      </div>
    </section>
  );
}`;

      const componentName = "MinimalHero";
      const componentId = `comp_${Date.now()}`;
      const newComponent: UIComponent = {
        id: componentId,
        project_id: selectedProjectId,
        name: componentName,
        code: generatedCode,
        type: "landing"
      };

      // Add component to state components list
      setComponents([newComponent, ...components]);
      setSelectedComponentId(componentId);

      updateChatMessage(assistantMsgId, {
        content: `O componente **${componentName}.tsx** foi gerado com sucesso para o projeto **${activeProject?.name}**!\n\nVocê pode visualizá-lo e editá-lo no editor ou abrir clicando no botão abaixo.`,
        status: "completed",
        code: generatedCode
      });
    } else {
      try {
        const response = await fetch(`${apiBaseUrl}/generation/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_id: selectedProjectId,
            prompt: prompt
          })
        });

        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();

        updateChatMessage(assistantMsgId, {
          logs: [`[SYSTEM] Execução de geração iniciada. ID: ${data.execution_id}.`]
        });

        // Polling loop to wait for execution to finish
        // We will fetch the components of the project to check if a new one is added
        await new Promise((resolve) => setTimeout(resolve, 8000));

        updateChatMessage(assistantMsgId, {
          content: `Componente gerado com sucesso via API do Helix!\n\nO novo arquivo foi criado no seu workspace. Clique abaixo para abri-lo no editor de código.`,
          status: "completed"
        });
      } catch (err: any) {
        updateChatMessage(assistantMsgId, {
          content: `Falha na geração de código: ${err.message}`,
          status: "failed",
          logs: [`[ERROR] ${err.message}`]
        });
      }
    }
  };

  const handleOpenInWorkspace = () => {
    setActiveTab("editor");
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] relative select-none font-mono">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto pr-2 space-y-6 pb-24 scrollbar-thin scrollbar-thumb-zinc-800">
        <AnimatePresence initial={false}>
          {chatMessages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className={`flex gap-4 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role !== "user" && (
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className="space-y-2 max-w-[80%]">
                <div
                  className={`p-4 rounded-2xl border text-xs leading-relaxed ${
                    msg.role === "user"
                      ? "bg-zinc-900 border-zinc-800 text-white rounded-tr-none font-sans"
                      : "bg-zinc-900/40 border-white/5 text-zinc-300 rounded-tl-none font-sans"
                  }`}
                >
                  <div className="markdown-content whitespace-pre-line">{msg.content}</div>

                  {/* Attachment - generated code preview snippet */}
                  {msg.code && (
                    <div className="mt-4 border border-zinc-800 rounded-lg overflow-hidden bg-zinc-950 font-mono text-[10px]">
                      <div className="bg-zinc-900 px-4 py-2 border-b border-zinc-800 flex justify-between items-center text-zinc-400">
                        <span>Código Gerado</span>
                        <Code className="w-3.5 h-3.5 text-emerald-400" />
                      </div>
                      <pre className="p-4 max-h-48 overflow-y-auto text-zinc-300 text-left scrollbar-thin scrollbar-thumb-zinc-850">
                        {msg.code}
                      </pre>
                      <div className="bg-zinc-900/60 p-2 border-t border-zinc-800 flex justify-end">
                        <button
                          onClick={handleOpenInWorkspace}
                          className="px-3 py-1.5 rounded bg-emerald-500 hover:bg-emerald-600 text-black font-bold text-[10px] cursor-pointer flex items-center gap-1.5 transition-colors"
                        >
                          <Play className="w-3 h-3 fill-current" />
                          <span>Abrir no Workspace</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Sub logs terminal for background pipelines */}
                {msg.logs && msg.logs.length > 0 && (
                  <div className="border border-zinc-900 bg-zinc-950/80 rounded-xl p-3.5 max-h-44 overflow-y-auto font-mono text-[9px] text-zinc-550 space-y-1.5 scrollbar-thin scrollbar-thumb-zinc-900">
                    <div className="flex items-center gap-1.5 text-zinc-400 font-bold mb-1 border-b border-zinc-900 pb-1 uppercase tracking-wider">
                      <Terminal className="w-3 h-3 text-emerald-400 animate-pulse" />
                      <span>Pipeline Logs</span>
                    </div>
                    {msg.logs.map((log, idx) => {
                      let color = "text-zinc-500";
                      if (log.includes("[SUCCESS]") || log.includes("sucesso")) color = "text-emerald-500";
                      if (log.includes("[ERROR]") || log.includes("Falha")) color = "text-rose-500";
                      if (log.includes("[CRAWLER]") || log.includes("[CODEGEN]")) color = "text-zinc-400";
                      return (
                        <div key={idx} className={color}>
                          {log}
                        </div>
                      );
                    })}
                  </div>
                )}

                <div
                  className={`text-[9px] text-zinc-650 flex items-center gap-1.5 ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <span>{msg.timestamp}</span>
                  {msg.role === "assistant" && msg.status === "running" && (
                    <span className="flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                      <span className="text-emerald-500 italic">Executando...</span>
                    </span>
                  )}
                  {msg.role === "assistant" && msg.status === "completed" && (
                    <span className="text-emerald-500 font-semibold flex items-center gap-0.5">
                      <CheckCircle2 className="w-2.5 h-2.5" /> Pronto
                    </span>
                  )}
                </div>
              </div>

              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Suggestion cards when chat is empty or fresh */}
        {chatMessages.length <= 1 && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
            className="flex flex-col items-center justify-center py-8 text-center space-y-6 max-w-2xl mx-auto"
          >
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-400 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/10 text-black font-extrabold text-2xl">
              H
            </div>
            <div>
              <h2 className="text-sm font-extrabold text-white uppercase tracking-wider">
                Helix UI Orchestrator
              </h2>
              <p className="text-[11px] text-zinc-500 mt-1 max-w-md font-sans">
                Seu assistente de design modular e código. Inicie um projeto, extraia estilos de qualquer site ou gere blocos de layouts com RAG.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full pt-4">
              <button
                onClick={() => handleSuggestionClick("crawl")}
                className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 hover:border-emerald-500/40 text-left hover:bg-zinc-950 transition-all duration-200 cursor-pointer flex flex-col justify-between h-32 group"
              >
                <Globe className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                <div>
                  <span className="text-[10px] font-bold text-white block">Extrair Estilos</span>
                  <span className="text-[9px] text-zinc-550 font-sans block mt-0.5 leading-relaxed">
                    Importe o design e cores de uma URL referência.
                  </span>
                </div>
              </button>

              <button
                onClick={() => handleSuggestionClick("generate")}
                className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 hover:border-emerald-500/40 text-left hover:bg-zinc-950 transition-all duration-200 cursor-pointer flex flex-col justify-between h-32 group"
              >
                <Code className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                <div>
                  <span className="text-[10px] font-bold text-white block">Gerar Componente</span>
                  <span className="text-[9px] text-zinc-550 font-sans block mt-0.5 leading-relaxed">
                    Crie blocos React (Hero, Cards, Nav) com Tailwind.
                  </span>
                </div>
              </button>

              <button
                onClick={() => handleSuggestionClick("search")}
                className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 hover:border-emerald-500/40 text-left hover:bg-zinc-950 transition-all duration-200 cursor-pointer flex flex-col justify-between h-32 group"
              >
                <Database className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                <div>
                  <span className="text-[10px] font-bold text-white block">Consulta RAG</span>
                  <span className="text-[9px] text-zinc-550 font-sans block mt-0.5 leading-relaxed">
                    Busque elementos salvos na biblioteca vetorial.
                  </span>
                </div>
              </button>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Floating Chat Input area */}
      <div className="absolute bottom-0 left-0 right-0 py-4 bg-gradient-to-t from-zinc-950 via-zinc-950 to-transparent">
        <form
          onSubmit={handleSendMessage}
          className="bg-zinc-900 border border-zinc-800/80 rounded-2xl p-2.5 max-w-3xl mx-auto flex flex-col gap-2 shadow-2xl focus-within:border-emerald-500/60 transition-all duration-200"
        >
          {/* Quick config options inside input */}
          <div className="flex justify-between items-center px-2 pb-1.5 border-b border-zinc-800/50">
            <div className="flex items-center gap-3">
              {/* Project selector - hidden in crawlMode */}
              {!crawlMode && projects.length > 0 && (
                <div className="flex items-center gap-1.5 text-[10px] text-zinc-400">
                  <FolderGit2 className="w-3.5 h-3.5 text-emerald-500" />
                  <span className="font-bold">Projeto:</span>
                  <select
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(e.target.value)}
                    className="bg-zinc-950 border border-zinc-800 rounded px-1.5 py-0.5 focus:outline-none font-bold text-[9px] text-emerald-400 font-mono"
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              {!crawlMode && projects.length === 0 && (
                <div className="flex items-center gap-1.5 text-[10px] text-rose-500 font-bold font-mono">
                  <FolderGit2 className="w-3.5 h-3.5 text-rose-500" />
                  <span>Sem projeto ativo</span>
                </div>
              )}

              {/* Mode switch helper indicator */}
              <button
                type="button"
                onClick={() => setCrawlMode(!crawlMode)}
                className={`text-[9px] font-bold px-2 py-0.5 rounded flex items-center gap-1 transition-all cursor-pointer font-mono ${
                  crawlMode
                    ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                    : "bg-zinc-950 border border-zinc-800 text-zinc-500"
                }`}
              >
                <Globe className="w-2.5 h-2.5" />
                <span>Modo Crawler</span>
              </button>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={clearChatMessages}
                className="p-1 rounded hover:bg-zinc-800 text-zinc-550 hover:text-white transition-colors cursor-pointer"
                title="Limpar histórico"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Actual textarea input */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="p-2 rounded-xl bg-zinc-950 border border-zinc-850 hover:border-zinc-700 text-zinc-500 hover:text-white cursor-pointer transition-colors"
              title="Anexar arquivo"
              onClick={() => alert("Upload de arquivos simulado para RAG.")}
            >
              <Paperclip className="w-4 h-4" />
            </button>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={!crawlMode && projects.length === 0}
              placeholder={
                !crawlMode && projects.length === 0
                  ? "Crie ou selecione um projeto na aba Library Explorer para gerar componentes."
                  : crawlMode
                  ? "Insira o link para importar (ex: https://linear.app)"
                  : "Prompt de design (ex: Criar um cabeçalho minimalista...)"
              }
              className="flex-1 bg-transparent px-2.5 py-2 text-xs text-white focus:outline-none font-sans disabled:opacity-50"
            />

            <button
              type="submit"
              disabled={!input.trim() || isSending || (!crawlMode && projects.length === 0)}
              className={`p-2.5 rounded-xl text-black font-bold flex items-center justify-center transition-all cursor-pointer ${
                input.trim() && !isSending && (crawlMode || projects.length > 0)
                  ? "bg-emerald-500 hover:scale-105 shadow-md shadow-emerald-500/15"
                  : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
              }`}
            >
              <Send className="w-4 h-4 fill-current" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
