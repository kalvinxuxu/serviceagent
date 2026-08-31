"use client";
import {useState} from "react";
import {checkOrder, confirmReply, ingestOrderEmail, sendReply} from "../../../lib/orderEmailApi";
import {OrderEmailReview} from "../../../components/OrderEmailReview";
export default function OrdersPage() { const [draft, setDraft] = useState<any>(); const [message, setMessage] = useState("");
  async function demo() { const r = await ingestOrderEmail({email_id: `ui-${Date.now()}`, sender: "buyer@example.test", subject: "订单", body: "原味贝果1个，明天送到公司"}); const checked = await checkOrder(r.draft_id); setDraft({...checked, customer: {email: "buyer@example.test"}}); }
  async function confirm() { if (!draft?.reply) return; const r = await confirmReply(draft.reply.reply_id, {draft_version: draft.version, confirmed_by: "demo-operator", idempotency_key: `${draft.draft_id}-v${draft.version}`}); setDraft({...draft, reply: r}); setMessage("草稿已确认"); }
  async function send() { if (!draft?.reply) return; const r = await sendReply(draft.reply.reply_id); setMessage(r.status === "SENT" ? "模拟邮件已发送" : "发送结果待核查"); }
  return <main style={{maxWidth: 900, margin: "32px auto", padding: 16}}><a href="/admin">← 管理后台</a><h1>订单邮件队列</h1><button type="button" onClick={() => void demo()}>载入模拟订单邮件</button>{message && <p>{message}</p>}{draft && <OrderEmailReview draft={draft} onConfirm={() => void confirm()} onSend={() => void send()} />}</main>;
}
