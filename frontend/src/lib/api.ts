const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// SWR-compatible fetcher: useSWR(key, fetcher) where key is the path
export const fetcher = (path: string) => apiFetch<any>(path);

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { method: "POST", body: formData });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

export function apiStream(path: string, body: object): EventSource {
  // Returns a ReadableStream via fetch for SSE
  return new EventSource(`${API_URL}${path}`);
}

export async function streamChat(
  body: { message: string; agent_type?: string; conversation_id?: string },
  onToken: (text: string) => void,
  onMeta: (meta: { conversation_id: string; message_id: string; agent_type: string }) => void,
  onDone: (data: { cost_usd?: number; cache_read_tokens?: number }) => void,
): Promise<void> {
  const res = await fetch(`${API_URL}/agents/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        const data = JSON.parse(line.slice(6));
        if (data.type === "token") onToken(data.text);
        else if (data.type === "conversation_id") onMeta(data);
        else if (data.type === "done") onDone(data);
      } catch {}
    }
  }
}
