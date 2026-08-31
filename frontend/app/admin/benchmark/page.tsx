"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
const ADMIN_HEADERS: HeadersInit = process.env.NEXT_PUBLIC_ADMIN_TOKEN ? {"X-Admin-Token": process.env.NEXT_PUBLIC_ADMIN_TOKEN} : {};
type Report = {suite?: string; run_at?: string; metrics?: Record<string, unknown>; cases?: {id: string; total: number; status: string; failure_component?: string}[]};

export default function BenchmarkPage() {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { fetch(`${API}/api/v1/admin/benchmark/latest`, {headers: ADMIN_HEADERS}).then(async (response) => { if (!response.ok) throw new Error(); setReport(await response.json()); }).catch(() => setError("暂时没有可用的 Benchmark 报告或没有管理员权限")); }, []);
  return <main style={{maxWidth: 900, margin: "32px auto", fontFamily: "sans-serif", padding: 16}}><p><a href="/admin">← 管理后台</a></p><h1>Benchmark 质量报告</h1>{error && <p>{error}</p>}{report && <><p>{report.suite} · {report.run_at}</p><pre>{JSON.stringify(report.metrics, null, 2)}</pre><h2>失败场景</h2>{(report.cases ?? []).filter((item) => item.total < 5).map((item) => <p key={item.id}>{item.id}: {item.total}/5 · {item.status} · {item.failure_component ?? "未定位"}</p>)}</>}</main>;
}
