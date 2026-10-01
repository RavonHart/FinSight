"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  Copy,
  Check,
  ExternalLink,
  ShieldAlert,
  Info,
  Layers,
} from "lucide-react";
import { Source } from "@/lib/research";

interface MarkdownReportProps {
  markdown: string;
  status: "queued" | "running" | "completed" | "completed_partial" | "failed" | "cancelled";
  partialReason?: string | null;
  sources?: Source[];
  activeCitation?: number | null;
  onSelectCitation?: (citationIndex: number) => void;
  runIterations?: number;
  toolCallsUsed?: number;
}

export const MarkdownReport: React.FC<MarkdownReportProps> = ({
  markdown,
  status,
  partialReason,
  sources = [],
  activeCitation,
  onSelectCitation,
  runIterations = 1,
  toolCallsUsed = 0,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Convert raw text into styled blocks, parsing citations [1], [2] etc.
  const renderFormattedText = (text: string) => {
    // Regex for [1], [2], [1, 2]
    const citationRegex = /\[(\d+)\]/g;
    const elements: React.ReactNode[] = [];
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = citationRegex.exec(text)) !== null) {
      const matchIndex = match.index;
      const citationNum = parseInt(match[1], 10);

      // Push text before match
      if (matchIndex > lastIndex) {
        elements.push(
          <span key={`text-${lastIndex}`}>{text.substring(lastIndex, matchIndex)}</span>
        );
      }

      // Check if source exists for this citation (1-indexed)
      const matchedSource = sources[citationNum - 1];
      const isActive = activeCitation === citationNum;

      elements.push(
        <button
          key={`cite-${matchIndex}`}
          type="button"
          onClick={() => onSelectCitation?.(citationNum)}
          title={matchedSource ? `${matchedSource.publisher || "Source"}: ${matchedSource.title || matchedSource.url}` : `Source #${citationNum}`}
          className={`inline-flex items-center px-1.5 py-0.2 mx-0.5 text-[11px] font-mono font-bold rounded transition transform hover:scale-105 ${
            isActive
              ? "bg-blue-600 text-white shadow-md shadow-blue-500/30 ring-2 ring-blue-400"
              : "bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 border border-blue-500/30"
          }`}
        >
          [{citationNum}]
        </button>
      );

      lastIndex = citationRegex.lastIndex;
    }

    if (lastIndex < text.length) {
      elements.push(<span key={`text-tail`}>{text.substring(lastIndex)}</span>);
    }

    return elements;
  };

  const renderContentLines = (rawMarkdown: string) => {
    const lines = rawMarkdown.split("\n");
    const rendered: React.ReactNode[] = [];
    let inList = false;
    let listItems: React.ReactNode[] = [];

    const flushList = (key: string) => {
      if (inList) {
        rendered.push(
          <ul key={key} className="space-y-1.5 my-3 pl-5 list-disc text-slate-300 text-sm">
            {listItems}
          </ul>
        );
        listItems = [];
        inList = false;
      }
    };

    lines.forEach((line, idx) => {
      const trimmed = line.trim();

      if (trimmed.startsWith("# ")) {
        flushList(`flush-${idx}`);
        rendered.push(
          <h1
            key={`h1-${idx}`}
            className="text-2xl font-black tracking-tight text-white mt-6 mb-3 pb-2 border-b border-slate-800"
          >
            {trimmed.substring(2)}
          </h1>
        );
      } else if (trimmed.startsWith("## ")) {
        flushList(`flush-${idx}`);
        const headingText = trimmed.substring(3);
        const isUncertainty =
          headingText.toLowerCase().includes("uncertaint") ||
          headingText.toLowerCase().includes("risk") ||
          headingText.toLowerCase().includes("gap");

        rendered.push(
          <h2
            key={`h2-${idx}`}
            className={`text-lg font-bold tracking-tight mt-6 mb-2 flex items-center space-x-2 ${
              isUncertainty ? "text-amber-400" : "text-slate-100"
            }`}
          >
            {isUncertainty && <AlertTriangle className="h-4 w-4 text-amber-400 inline shrink-0" />}
            <span>{headingText}</span>
          </h2>
        );
      } else if (trimmed.startsWith("### ")) {
        flushList(`flush-${idx}`);
        rendered.push(
          <h3 key={`h3-${idx}`} className="text-sm font-semibold uppercase tracking-wider text-slate-400 mt-4 mb-1">
            {trimmed.substring(4)}
          </h3>
        );
      } else if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        inList = true;
        listItems.push(
          <li key={`li-${idx}`} className="leading-relaxed">
            {renderFormattedText(trimmed.substring(2))}
          </li>
        );
      } else if (trimmed === "") {
        flushList(`flush-${idx}`);
      } else {
        flushList(`flush-${idx}`);
        // Paragraph
        rendered.push(
          <p key={`p-${idx}`} className="text-sm text-slate-300 leading-relaxed my-2">
            {renderFormattedText(trimmed)}
          </p>
        );
      }
    });

    flushList(`flush-final`);
    return rendered;
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0f1d] rounded-2xl border border-slate-800/80 shadow-xl overflow-hidden">
      {/* Report Header Bar */}
      <div className="px-6 py-4 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="h-8 w-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <FileText className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-tight flex items-center space-x-2">
              <span>Synthesized Research Report</span>
              {status === "completed" && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold flex items-center space-x-1">
                  <CheckCircle2 className="h-3 w-3" />
                  <span>Fully Verified</span>
                </span>
              )}
              {status === "completed_partial" && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 font-semibold flex items-center space-x-1">
                  <AlertTriangle className="h-3 w-3" />
                  <span>Completed with Gaps</span>
                </span>
              )}
            </h2>
            <div className="flex items-center space-x-3 text-[11px] text-slate-400 mt-0.5">
              <span>Iterations: {runIterations}</span>
              <span>&bull;</span>
              <span>Tool Calls: {toolCallsUsed}</span>
              <span>&bull;</span>
              <span>Sources Cited: {sources.length}</span>
            </div>
          </div>
        </div>

        <button
          onClick={handleCopy}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-xs font-medium text-slate-300 hover:text-white transition"
        >
          {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
          <span>{copied ? "Copied" : "Copy Report"}</span>
        </button>
      </div>

      {/* UX HONESTY: Prominent Warning Banner for completed_partial runs (§26) */}
      {status === "completed_partial" && (
        <div className="mx-6 mt-4 p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-200 shadow-lg shadow-amber-500/5">
          <div className="flex items-start space-x-3">
            <div className="h-8 w-8 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center shrink-0 text-amber-400 mt-0.5">
              <ShieldAlert className="h-4 w-4" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="font-bold text-xs uppercase tracking-wider text-amber-400">
                  Partial Verification Notice
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-400/20 text-amber-300 font-semibold">
                  Bounded Run
                </span>
              </div>
              <p className="text-xs text-amber-200/90 leading-relaxed">
                {partialReason ||
                  "This report reached the maximum iteration budget or tool deadline before all claims could be fully corroborated. Findings are presented with explicit uncertainty disclosures."}
              </p>
              <div className="pt-1 flex items-center space-x-2 text-[11px] text-amber-300/80 font-mono">
                <span>&bull; Single loop ceiling enforced</span>
                <span>&bull; Unverified claims flagged in provenance panel</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Report Body */}
      <div className="flex-1 p-6 overflow-y-auto">
        {markdown ? (
          <div className="max-w-3xl mx-auto space-y-2">{renderContentLines(markdown)}</div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-8">
            <FileText className="h-10 w-10 text-slate-600 mb-3" />
            <h3 className="text-sm font-semibold text-slate-300">Awaiting Synthesis</h3>
            <p className="text-xs text-slate-500 max-w-sm mt-1">
              The synthesized markdown report will appear here once agents gather evidence, execute Jev System One analysis, and pass quality checks.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
