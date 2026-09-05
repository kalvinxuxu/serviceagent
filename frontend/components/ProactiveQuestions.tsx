import { PQGResponse, recordProactiveQuestionEvent } from "../lib/pqgApi";

export function ProactiveQuestions({ sessionId, result, onSelect }: { sessionId?: string; result?: PQGResponse; onSelect: (text: string) => void | Promise<void> }) {
  if (!result || result.status === "EMPTY" || result.status === "SUPPRESSED") return null;
  if (!result.questions.length) return null;
  return <section aria-label="proactive-questions" className="suggestions"><span className="suggestions-label">您可能还想了解</span><div className="suggestion-list">{result.questions.map((question) => <button className="suggestion-chip" key={question.candidate_id} type="button" disabled={!sessionId} onClick={() => { if (sessionId) void recordProactiveQuestionEvent(sessionId, { request_id: result.request_id, candidate_id: question.candidate_id, event_type: "CLICK" }); void onSelect(question.text); }}>{question.text}<span>›</span></button>)}</div></section>;
}
