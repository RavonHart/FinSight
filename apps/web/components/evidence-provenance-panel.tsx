"use client";

import React, { useState } from "react";
import {
  Link2,
  ExternalLink,
  Shield,
  FileCheck2,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  BookOpen,
  Hash,
  Database,
  Search,
} from "lucide-react";
import { Source, Evidence, Claim } from "@/lib/research";

interface EvidenceProvenancePanelProps {
  sources: Source[];
  evidence: Evidence[];
  claims: Claim[];
  activeCitation: number | null;
  onSelectCitation: (citationIndex: number) => void;
}

export const EvidenceProvenancePanel: React.FC<EvidenceProvenancePanelProps> = ({
  sources,
  evidence,
  claims,
  activeCitation,
  onSelectCitation,
}) => {
  const [activeTab, setActiveTab] = useState<"sources" | "evidence" | "claims">("sources");

  const getTrustTierBadge = (tier: number) => {
    switch (tier) {
      case 1:
        return (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold flex items-center space-x-1">
            <Shield className="h-2.5 w-2.5" />
            <span>Tier 1 Regulatory</span>
          </span>
        );
      case 2:
        return (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-semibold flex items-center space-x-1">
            <Shield className="h-2.5 w-2.5" />
            <span>Tier 2 Institutional</span>
          </span>
        );
      default:
        return (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-semibold flex items-center space-x-1">
            <Shield className="h-2.5 w-2.5" />
            <span>Tier 3 Web</span>
          </span>
        );
    }
  };

  const getClaimStatusBadge = (status: string) => {
    switch (status) {
      case "supported":
        return (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold flex items-center space-x-1">
            <CheckCircle2 className="h-2.5 w-2.5" />
            <span>Supported (Jev ≥ 0.80)</span>
          </span>
        );
      case "unverified":
        return (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 font-semibold flex items-center space-x-1">
            <AlertCircle className="h-2.5 w-2.5" />
            <span>Unverified (Jev &lt; 0.50)</span>
          </span>
        );
      default:
        return (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 font-semibold flex items-center space-x-1">
            <AlertCircle className="h-2.5 w-2.5" />
            <span>Disputed</span>
          </span>
        );
    }
  };

  const getClaimTypeBadge = (claimType: string) => {
    const colors: Record<string, string> = {
      fact: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      analysis: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      scenario: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
      uncertainty: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    };
    return (
      <span
        className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-mono font-semibold border ${
          colors[claimType] || "bg-slate-800 text-slate-400 border-slate-700"
        }`}
      >
        {claimType}
      </span>
    );
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0f1d] rounded-2xl border border-slate-800/80 shadow-xl overflow-hidden">
      {/* Panel Header & Navigation Tabs */}
      <div className="px-5 py-3 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="h-7 w-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Database className="h-4 w-4" />
          </div>
          <h2 className="text-sm font-bold text-white tracking-tight">Evidence &amp; Provenance</h2>
        </div>

        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab("sources")}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition ${
              activeTab === "sources"
                ? "bg-slate-800 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Sources ({sources.length})
          </button>
          <button
            onClick={() => setActiveTab("evidence")}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition ${
              activeTab === "evidence"
                ? "bg-slate-800 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Evidence ({evidence.length})
          </button>
          <button
            onClick={() => setActiveTab("claims")}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition ${
              activeTab === "claims"
                ? "bg-slate-800 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Claims ({claims.length})
          </button>
        </div>
      </div>

      {/* Tab Contents */}
      <div className="flex-1 p-5 overflow-y-auto space-y-3">
        {/* TAB 1: Sources */}
        {activeTab === "sources" && (
          <>
            {sources.length > 0 ? (
              sources.map((src, index) => {
                const citeNum = src.citation_index || index + 1;
                const isSelected = activeCitation === citeNum;

                return (
                  <div
                    key={src.id}
                    onClick={() => onSelectCitation(citeNum)}
                    className={`p-3.5 rounded-xl border transition cursor-pointer ${
                      isSelected
                        ? "border-blue-500 bg-blue-500/10 shadow-lg shadow-blue-500/10 ring-1 ring-blue-500"
                        : "border-slate-800/80 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/60"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center space-x-2">
                        <span className="h-5 w-5 rounded bg-blue-500/20 text-blue-400 font-mono text-[11px] font-bold flex items-center justify-center border border-blue-500/30">
                          {citeNum}
                        </span>
                        <span className="text-xs font-semibold text-slate-200">
                          {src.publisher || "Financial Source"}
                        </span>
                      </div>
                      {getTrustTierBadge(src.trust_tier)}
                    </div>

                    <h4 className="text-xs font-medium text-slate-300 line-clamp-2 mt-1">
                      {src.title || src.url}
                    </h4>

                    <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-800/60 text-[11px] text-slate-500">
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-blue-400 hover:underline flex items-center space-x-1 truncate max-w-[200px]"
                      >
                        <span className="truncate">{src.url}</span>
                        <ExternalLink className="h-3 w-3 shrink-0" />
                      </a>
                      {src.published_date && <span>{src.published_date}</span>}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                <BookOpen className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                <span>No sources recorded yet. Sources will populate as research tools run.</span>
              </div>
            )}
          </>
        )}

        {/* TAB 2: Evidence Snippets */}
        {activeTab === "evidence" && (
          <>
            {evidence.length > 0 ? (
              evidence.map((item, idx) => {
                const relevancePct = item.relevance_score
                  ? Math.round(item.relevance_score * 100)
                  : 90;

                return (
                  <div
                    key={item.id}
                    className="p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:border-slate-700 transition"
                  >
                    <div className="flex items-center justify-between text-xs mb-2">
                      <span className="text-[10px] font-mono text-slate-400 uppercase">
                        Evidence #{idx + 1}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20">
                        {relevancePct}% Relevance
                      </span>
                    </div>

                    <blockquote className="text-xs text-slate-300 italic pl-3 border-l-2 border-blue-500/50 leading-relaxed bg-blue-500/5 py-1.5 rounded-r">
                      "{item.content}"
                    </blockquote>
                  </div>
                );
              })
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                <FileCheck2 className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                <span>Evidence chunks with vector embeddings will populate here.</span>
              </div>
            )}
          </>
        )}

        {/* TAB 3: Claims */}
        {activeTab === "claims" && (
          <>
            {claims.length > 0 ? (
              claims.map((claim) => (
                <div
                  key={claim.id}
                  className="p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:border-slate-700 transition space-y-2"
                >
                  <div className="flex items-center justify-between">
                    {getClaimTypeBadge(claim.claim_type)}
                    {getClaimStatusBadge(claim.status)}
                  </div>

                  <p className="text-xs text-slate-200 leading-relaxed font-medium">
                    {claim.statement}
                  </p>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                <HelpCircle className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                <span>Atomic claims grounded against evidence will appear here.</span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
