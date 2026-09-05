"use client";

import { FormEvent, useRef, useState } from "react";
import { createSession, sendMessage } from "../lib/api";
import { ChatWindow, ChatMessage } from "../components/ChatWindow";
import { ProactiveQuestions } from "../components/ProactiveQuestions";
import { getProactiveQuestions, PQGResponse } from "../lib/pqgApi";

type OrderSummary = { customer_id: string; items: { name?: string; quantity?: number; subtotal?: number }[]; subtotal: number; discount: number; shipping: number; total: number; delivery_mode: "PICKUP" | "SHIPPING"; status: string; requires_confirmation: boolean };
type UserProfile = { id: string; name: string; summary?: OrderSummary; confirmed?: boolean };
type TimelineMessage = ChatMessage & { userId: string; userName: string; role: "user" | "agent" };

const INITIAL_USERS: UserProfile[] = [{ id: "CUS001", name: "用户A" }, { id: "CUS002", name: "用户B" }, { id: "CUS003", name: "用户C" }];

export default function Home() {
  const [text, setText] = useState("");
  const [users, setUsers] = useState(INITIAL_USERS);
  const [groupSessionId, setGroupSessionId] = useState<string>();
  const [activeUserId, setActiveUserId] = useState("CUS001");
  const [timeline, setTimeline] = useState<TimelineMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [attachments, setAttachments] = useState<File[]>([]);
  const [proactiveQuestions, setProactiveQuestions] = useState<PQGResponse>();
  const [handoffOffer, setHandoffOffer] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const activeUser = users.find((user) => user.id === activeUserId) ?? users[0];

  async function sendUserMessage(input: string, files: File[] = []) {
    if ((!input && files.length === 0) || loading) return;
    setText(""); setError(undefined); setLoading(true); setProactiveQuestions(undefined);
    setTimeline((current) => [...current, { userId: activeUser.id, userName: activeUser.name, role: "user", text: `${activeUser.name}：${input || "（图片）"}` }]);
    try {
      const sid = groupSessionId ?? (await createSession(activeUser.id, INITIAL_USERS.map((user) => user.id))).session_id;
      if (!groupSessionId) setGroupSessionId(sid);
      const result = await sendMessage(sid, activeUser.id, input, false, files, INITIAL_USERS[0].id);
      setHandoffOffer(Boolean(result.handoff_offer));
      const summaries = result.order_summaries ?? { [activeUser.id]: result.order_summary };
      setUsers((current) => current.map((user) => summaries[user.id] ? { ...user, summary: summaries[user.id], confirmed: summaries[user.id].status === "CONFIRMED" } : user));
      setTimeline((current) => [...current, { userId: activeUser.id, userName: activeUser.name, role: "agent", text: `Agent（${activeUser.name}）：${result.message.content}`, attachments: result.attachments }]);
      setAttachments([]); if (fileInput.current) fileInput.current.value = "";
      const assistantMessageId = `msg_${Date.now()}`;
      void getProactiveQuestions(sid, assistantMessageId, input, result.message.content, INITIAL_USERS[0].id).then(setProactiveQuestions).catch(() => setProactiveQuestions(undefined));
    } catch { setError("服务暂时不可用，请稍后重试或转人工。"); } finally { setLoading(false); }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await sendUserMessage(text.trim(), attachments);
  }

  async function handleSuggestedQuestion(question: string) {
    setText(question);
    await sendUserMessage(question);
  }

  return <main className="app-shell">
    <header className="app-header"><div className="brand-mark">山</div><div><h1>山也面包</h1><p>新鲜出炉 · 每日手作</p></div><span className="online-status"><i />在线客服</span></header>
    <section aria-label="user-switcher" className="user-switcher"><span>测试客户</span>{users.map((user) => <button key={user.id} type="button" aria-pressed={user.id === activeUserId} onClick={() => setActiveUserId(user.id)}>{user.name}</button>)}</section>
    <section className="welcome-card"><div><span className="eyebrow">SHANYE BAKERY</span><h2>您好，{activeUser.name} 👋</h2><p>我是山也面包的专属客服，很高兴为您服务。</p></div><div className="bread-illustration">🥐</div></section>
    <ChatWindow messages={timeline} />
    {handoffOffer && <div className="handoff-offer" role="group" aria-label="人工客服选项"><span>还需要帮助吗？</span><button type="button" onClick={() => sendUserMessage("转人工")}>转人工</button><button type="button" onClick={() => setHandoffOffer(false)}>继续补充</button></div>}
    <ProactiveQuestions sessionId={groupSessionId} result={proactiveQuestions} onSelect={handleSuggestedQuestion} />
    {loading && <p role="status" className="typing"><span />客服正在思考…</p>}{error && <p role="alert" className="error-banner">{error}</p>}
    <form onSubmit={handleSubmit} className="composer"><label className="icon-button" aria-label="添加图片"><span>＋</span><input ref={fileInput} type="file" accept="image/png,image/jpeg,image/webp" multiple onChange={(event) => setAttachments(Array.from(event.target.files ?? []))} /></label><input value={text} onChange={(event) => setText(event.target.value)} placeholder="输入您想了解的内容…" aria-label="消息" /><button type="submit" disabled={loading || (!text.trim() && attachments.length === 0)}>发送</button></form>
    {attachments.length > 0 && <p className="attachment-hint">已选择 {attachments.length} 张图片</p>}
    <footer className="privacy-note">山也面包客服 · 您的对话内容将被安全保护</footer>
  </main>;
}
