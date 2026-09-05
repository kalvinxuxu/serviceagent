const backendUrl = () => process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export type PQGQuestion = { candidate_id: string; text: string; source: "RETRIEVAL" | "LLM" | "HYBRID"; rank: number; relevance_score?: number; confidence?: number };
export type PQGResponse = { status: "READY" | "EMPTY" | "SUPPRESSED" | "DEGRADED"; request_id: string; assistant_message_id: string; questions: PQGQuestion[]; latency_ms: number; error_code?: string };

export async function getProactiveQuestions(sessionId: string, assistantMessageId: string, context: string, reply: string, ownerId = "CUS001") {
  const response = await fetch(`${backendUrl()}/api/v1/sessions/${encodeURIComponent(sessionId)}/proactive-questions`, { method: "POST", headers: { "content-type": "application/json", "X-Session-Owner": ownerId }, body: JSON.stringify({ session_id: sessionId, assistant_message_id: assistantMessageId, context, reply }) });
  if (!response.ok) throw new Error("PQG_UNAVAILABLE");
  return response.json() as Promise<PQGResponse>;
}

export async function recordProactiveQuestionEvent(sessionId: string, event: { request_id: string; candidate_id: string; event_type: string }, ownerId = "CUS001") {
  await fetch(`${backendUrl()}/api/v1/sessions/${encodeURIComponent(sessionId)}/proactive-questions/events`, { method: "POST", headers: { "content-type": "application/json", "X-Session-Owner": ownerId }, body: JSON.stringify(event) });
}
