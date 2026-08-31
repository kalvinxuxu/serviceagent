"use client";

import { FormEvent, useRef, useState } from "react";
import { confirmOrder, createSession, deleteCustomerMemory, getCustomerMemory, sendMessage } from "../lib/api";
import { ChatWindow, ChatMessage } from "../components/ChatWindow";
import { AgentInspector } from "../components/AgentInspector";

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
  const [inspector, setInspector] = useState<unknown>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [attachments, setAttachments] = useState<File[]>([]);
  const [memories, setMemories] = useState<{memory_key: string; memory_value: unknown; memory_type: string}[]>([]);
  const fileInput = useRef<HTMLInputElement>(null);
  const activeUser = users.find((user) => user.id === activeUserId) ?? users[0];

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = text.trim();
    if ((!input && attachments.length === 0) || loading) return;
    setText(""); setError(undefined); setLoading(true);
    setTimeline((current) => [...current, { userId: activeUser.id, userName: activeUser.name, role: "user", text: `${activeUser.name}：${input || "（图片）"}` }]);
    try {
      const sid = groupSessionId ?? (await createSession(activeUser.id, INITIAL_USERS.map((user) => user.id))).session_id;
      if (!groupSessionId) setGroupSessionId(sid);
      const result = await sendMessage(sid, activeUser.id, input, false, attachments, INITIAL_USERS[0].id);
      const summaries = result.order_summaries ?? { [activeUser.id]: result.order_summary };
      setUsers((current) => current.map((user) => summaries[user.id] ? { ...user, summary: summaries[user.id], confirmed: summaries[user.id].status === "CONFIRMED" } : user));
      setTimeline((current) => [...current, { userId: activeUser.id, userName: activeUser.name, role: "agent", text: `Agent（${activeUser.name}）：${result.message.content}`, attachments: result.attachments }]);
      setInspector(result.inspector); setAttachments([]); if (fileInput.current) fileInput.current.value = "";
    } catch { setError("服务暂时不可用，请稍后重试或转人工。"); } finally { setLoading(false); }
  }

  async function handleConfirm(user: UserProfile) {
    if (!groupSessionId) return;
    try {
      const result = await confirmOrder(groupSessionId, user.id, INITIAL_USERS[0].id);
      const summaries = result.order_summaries ?? { [user.id]: result.order_summary };
      setUsers((current) => current.map((item) => summaries[item.id] ? { ...item, summary: summaries[item.id], confirmed: summaries[item.id].status === "CONFIRMED" } : item));
      setTimeline((current) => [...current, { userId: user.id, userName: user.name, role: "agent", text: `Agent（${user.name}）：${result.message}` }]);
    } catch { setError("订单确认失败，请检查当前用户会话。"); }
  }

  return <main style={{ maxWidth: 900, margin: "40px auto", fontFamily: "sans-serif", padding: 16 }}>
    <h1>Shanye Shop Demo</h1><p>虚拟智能客服 Agent · 多用户测试</p>
    <section aria-label="user-switcher" style={{ display: "flex", gap: 8, margin: "16px 0" }}>{users.map((user) => <button key={user.id} type="button" aria-pressed={user.id === activeUserId} onClick={() => setActiveUserId(user.id)} style={{ padding: "8px 16px", fontWeight: user.id === activeUserId ? "bold" : "normal" }}>{user.name}<small style={{ display: "block" }}>{user.id}</small></button>)}</section>
    <p role="status">当前发言用户：{activeUser.name}（{activeUser.id}）</p>
    <ChatWindow messages={timeline} />
    {loading && <p role="status">Agent 正在规划…</p>}{error && <p role="alert">{error}</p>}<AgentInspector trace={inspector} />
    <section aria-label="order-summaries" style={{ marginTop: 16, borderTop: "1px solid #ddd", paddingTop: 12 }}><h2>各用户订单确认</h2>{users.map((user) => user.summary?.items?.length ? <div key={user.id} style={{ border: "1px solid #ddd", padding: 12, marginBottom: 8 }}><strong>{user.name}（{user.id}）</strong><p>{user.summary.items.map((item) => `${item.name ?? "商品"} × ${item.quantity ?? 1}`).join("、")}</p><p>金额：{user.summary.total} 元；取货方式：{user.summary.delivery_mode === "PICKUP" ? "到店自取" : "配送/邮寄"}</p>{user.summary.requires_confirmation && !user.confirmed ? <button type="button" onClick={() => void handleConfirm(user)}>确认该用户订单</button> : <span>{user.summary.status === "CONFIRMED" || user.confirmed ? "已确认" : "等待补充信息"}</span>}</div> : null)}</section>
    <section aria-label="customer-memory" style={{ marginTop: 16, borderTop: "1px solid #ddd", paddingTop: 12 }}><label>当前客户偏好 <button type="button" onClick={async () => setMemories((await getCustomerMemory(activeUser.id)).items)}>查看已确认偏好</button></label>{memories.map((memory) => <div key={memory.memory_key}><span>{memory.memory_key}: {JSON.stringify(memory.memory_value)}</span><button type="button" onClick={async () => { await deleteCustomerMemory(activeUser.id, memory.memory_key); setMemories((current) => current.filter((item) => item.memory_key !== memory.memory_key)); }}>删除</button></div>)}</section>
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8, marginTop: 16 }}><input value={text} onChange={(event) => setText(event.target.value)} placeholder={`以${activeUser.name}身份发问…`} style={{ flex: 1, padding: 12 }} /><input ref={fileInput} type="file" accept="image/png,image/jpeg,image/webp" multiple onChange={(event) => setAttachments(Array.from(event.target.files ?? []))} aria-label="上传图片" /><button type="submit" disabled={loading}>发送</button></form>
  </main>;
}
