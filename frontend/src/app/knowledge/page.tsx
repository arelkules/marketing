"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import useSWR from "swr";
import { apiFetch, apiUpload, fetcher } from "@/lib/api";
import type { KnowledgeDocument } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function KnowledgePage() {
  const { data: docs, mutate } = useSWR<KnowledgeDocument[]>("/ingest/documents", fetcher, { refreshInterval: 3000 });
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
    } catch (e: any) {
      setUploadError(e.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  }, [mutate]);

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
  };

  const totalChunks = docs?.filter((d) => d.status === "completed").reduce((s, d) => s + d.chunk_count, 0) || 0;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white">Knowledge Base</h1>
        <p className="text-gray-400 mt-1">Upload your NotebookLM conversation exports. The AI agents use this to give advice specific to YOUR business.</p>
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all mb-8 ${
          isDragActive ? "border-indigo-500 bg-indigo-900/20" : "border-gray-700 hover:border-gray-500 bg-gray-900/50"
        }`}
      >
        <input {...getInputProps()} />
        <div className="text-5xl mb-4">🧠</div>
        {uploading ? (
          <p className="text-indigo-400 font-medium">Uploading...</p>
        ) : isDragActive ? (
          <p className="text-indigo-400 font-medium">Drop files here</p>
        ) : (
          <>
            <p className="text-white font-medium mb-1">Drag & drop your files here</p>
            <p className="text-gray-400 text-sm">PDF, TXT, DOCX — up to 50MB each</p>
            <p className="text-gray-500 text-xs mt-2">NotebookLM exports, strategy docs, conversation transcripts</p>
          </>
        )}
        {uploadError && <p className="text-red-400 text-sm mt-3">{uploadError}</p>}
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Ingested Documents</h2>
        <span className="text-sm text-gray-500">{totalChunks} total knowledge chunks</span>
      </div>

      <div className="space-y-3">
        {(docs || []).map((doc) => (
          <div key={doc.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center gap-4">
            <div className="text-2xl">
              {doc.file_type === "pdf" ? "📄" : doc.file_type === "docx" ? "📝" : "📃"}
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
          <p className="text-center text-gray-600 py-10 text-sm">No documents yet. Upload your NotebookLM exports above.</p>
        )}
      </div>
    </div>
  );
}
