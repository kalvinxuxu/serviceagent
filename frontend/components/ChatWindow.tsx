export type ChatMessage = {text: string; role?: "user" | "agent"; attachments?: {url: string; alt?: string}[]};
export function ChatWindow({messages}: {messages: ChatMessage[]}) {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
  return <section aria-label="conversation" className="conversation">
    {messages.length === 0 && <div className="empty-state"><span className="empty-icon">✦</span><h2>今天想吃点什么？</h2><p>可以问我库存、口味推荐、价格或配送方式</p></div>}
    {messages.map((m, i) => <div key={i} className={`message-row ${m.role === "user" ? "message-row-user" : "message-row-agent"}`}>
      {m.role !== "user" && <div className="agent-avatar">山</div>}
      <div className={`message-bubble ${m.role === "user" ? "message-user" : "message-agent"}`}>
        <p>{m.text.replace(/^Agent（.*?）：|^用户[ABC]：/, "")}</p>
        {m.attachments?.map((attachment, index) => <img key={index} src={`${backendUrl}${attachment.url}`} alt={attachment.alt ?? "商品图片"} className="product-image" />)}
      </div>
    </div>)}
  </section>;
}
