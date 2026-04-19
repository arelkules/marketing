"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import useSWR from "swr";
import { apiFetch, apiUpload, fetcher } from "@/lib/api";
import type { KnowledgeDocument } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import Link from "next/link";

interface NotebookStatus {
  name: string;
  icon: string;
  advisor: string;
  notebook_source: string;
  chunks: number;
  status: string;
  last_synced?: string;
  documents: { filename: string; status: string; chunks: number }[];
}

interface NotebooksData {
  loaded: NotebookStatus[];
  missing: NotebookStatus[];
  total_chunks: number;
}

export default function KnowledgePage() {
  const { data: docs, mutate } = useSWR<KnowledgeDocument[]>("/ingest/documents", fetcher, { refreshInterval: 3000 });
  const { data: notebooks, mutate: mutateNotebooks } = useSWR<NotebooksData>("/ingest/notebooks", fetcher, { refreshInterval: 5000 });
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const onDrop = useCallback(async (accepted: File[]) => {
    if (accepted.length === 0) return;
    setUploading(true);
    setUploadError("");
    try {
      for (const file of accepted) {
        const form = new FormData();
        form.append("file", file);
        await apiUpload("/ingest/upload", form);
      }
      mutate();
      mutateNotebooks();
    } catch (e: any) {
      setUploadError(e.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  }, [mutate, mutateNotebooks]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    multiple: true,
  });

  const deleteDoc = async (id: string) => {
    await apiFetch(`/ingest/documents/${id}`, { method: "DELETE" });
    mutate();
    mutateNotebooks();
  };

  const totalChunks = notebooks?.total_chunks || 0;

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <span>🧠</span> Knowledge Base
        </h1>
        <p className="text-gray-400 mt-1">
          The brains of your advisory team — each advisor reads their own NotebookLM notebook.
        </p>
      </div>

      {/* Advisor brain status */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white font-semibold">Advisor Brains Status</h2>
          <span className="text-gray-500 text-xs">{totalChunks.toLocaleString()} total knowledge chunks</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
          {(notebooks?.loaded || []).map((nb) => (
            <div key={nb.notebook_source} className="bg-gray-800 rounded-xl p-3 border border-gray-700">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{nb.icon}</span>
                <span className="text-white text-sm font-medium truncate">{nb.name}</span>
              </div>
              <p className="text-green-400 text-xs font-medium">✅ {nb.chunks.toLocaleString()} chunks loaded</p>
              <p className="text-gray-600 text-xs mt-0.5">Used by: {nb.advisor}</p>
            </div>
          ))}
          {(notebooks?.missing || []).map((nb) => (
            <div key={nb.notebook_source} className="bg-gray-900 rounded-xl p-3 border border-dashed border-gray-700">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg grayscale opacity-50">{nb.icon}</span>
                <span className="text-gray-500 text-sm font-medium truncate">{nb.name}</span>
              </div>
              <p className="text-yellow-600 text-xs">⚠ Not synced yet</p>
              <p className="text-gray-600 text-xs mt-0.5">Used by: {nb.advisor}</p>
            </div>
          ))}
        </div>

        {(notebooks?.missing || []).length > 0 && (
          <div className="bg-indigo-950/40 border border-indigo-800 rounded-xl p-4 text-sm">
            <p className="text-indigo-300 font-semibold mb-2">📋 How to sync your NotebookLM notebooks:</p>
            <ol className="text-gray-300 space-y-1 list-decimal list-inside text-xs">
              <li>Make sure the backend is running (<code className="text-indigo-400">localhost:8000</code>)</li>
              <li>On your local machine: <code className="text-indigo-400">python notebooklm_sync.py</code></li>
              <li>The script will extract all notebooks and upload them automatically</li>
              <li>Come back here — you'll see all advisor brains turn green ✅</li>
            </ol>
            <p className="text-gray-500 text-xs mt-2">
              Or use the{" "}
              <Link href="/notebooklm" className="text-indigo-400 hover:text-indigo-300">
                NotebookLM Sync page →
              </Link>
            </p>
          </div>
        )}
      </div>

      {/* Upload zone */}
      <div>
        <h2 className="text-white font-semibold mb-3">Upload Documents Manually</h2>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${
            isDragActive ? "border-indigo-500 bg-indigo-900/20" : "border-gray-700 hover:border-gray-500 bg-gray-900/50"
          }`}
        >
          <input {...getInputProps()} />
          <div className="text-4xl mb-3">📄</div>
          {uploading ? (
            <p className="text-indigo-400 font-medium">Uploading...</p>
          ) : isDragActive ? (
            <p className="text-indigo-400 font-medium">Drop files here</p>
          ) : (
            <>
              <p className="text-white font-medium mb-1">Drag & drop your files here</p>
              <p className="text-gray-400 text-sm">PDF, TXT, DOCX — up to 50MB each</p>
            </>
          )}
          {uploadError && <p className="text-red-400 text-sm mt-3">{uploadError}</p>}
        </div>
      </div>

      {/* Document list */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">All Documents</h2>
        <div className="space-y-2">
          {(docs || []).map((doc) => (
            <div key={doc.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center gap-4">
              <div className="text-xl">
                {doc.filename.startsWith("notebooklm_") ? "🧠" : doc.file_type === "pdf" ? "📄" : "📝"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-medium truncate">{doc.filename}</p>
                <p className="text-gray-500 text-xs mt-0.5">
                  {formatDate(doc.created_at)} · {(doc.file_size / 1024).toFixed(0)} KB
                </p>
              </div>
              <div className="text-right shrink-0">
                {doc.status === "completed" && (
                  <span className="text-green-400 text-xs font-medium">{doc.chunk_count} chunks</span>
                )}
                {doc.status === "processing" && (
                  <span className="text-yellow-400 text-xs animate-pulse">Processing...</span>
                )}
                {doc.status === "pending" && (
                  <span className="text-gray-500 text-xs">Pending</span>
                )}
                {doc.status === "error" && (
                  <span className="text-red-400 text-xs" title={doc.error_msg || ""}>Error</span>
                )}
              </div>
              <button
                onClick={() => deleteDoc(doc.id)}
                className="text-gray-600 hover:text-red-400 text-sm transition-colors px-2 py-1 rounded"
              >
                ✕
              </button>
            </div>
          ))}
          {docs?.length === 0 && (
            <p className="text-center text-gray-600 py-10 text-sm">No documents yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
