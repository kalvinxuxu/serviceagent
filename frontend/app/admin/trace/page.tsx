"use client";

import { FormEvent, useState } from "react";

const API = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
const ADMIN_HEADERS: HeadersInit = process.env.NEXT_PUBLIC_ADMIN_TOKEN ? {"X-Admin-Token": process.env.NEXT_PUBLIC_ADMIN_TOKEN} : {};
export default function TracePage() {
  const [sessionId, setSessionId] = useState(""); const [trace, setTrace] = useState<Record<string, unknown>>(); const [error, setError] = useState("");
  async function load(event: FormEvent) { event.preventDefault(); setError(""); const response = await fetch(`${API}/api/v1/sessions/${encodeURIComponent(sessionId)}/trace`, {headers: ADMIN_HEADERS}); if (!response.ok) { setError("找不到该会话 Trace"); return; } setTrace(await response.json()); }
  return <main style={{maxWidth: 900, margin: "32px auto", fontFamily: "sans-serif", padding: 16}}><p><a href="/admin">← 管理后台</a></p><h1>会话 Trace</h1><form onSubmit={load}><input value={sessionId} onChange={(event) => setSessionId(event.target.value)} placeholder="session_id" required /><button type="submit">查询</button></form>{error && <p>{error}</p>}{trace && <pre style={{whiteSpace: "pre-wrap"}}>{JSON.stringify(trace, null, 2)}</pre>}</main>;
}
