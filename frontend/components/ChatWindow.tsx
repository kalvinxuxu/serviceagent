export type ChatMessage = {text: string; attachments?: {url: string; alt?: string}[]};
export function ChatWindow({messages}: {messages: ChatMessage[]}) {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
  return <section aria-label="conversation" style={{minHeight: 320, border: "1px solid #ddd", padding: 20}}>{messages.map((m, i)=><div key={i}><p>{m.text}</p>{m.attachments?.map((attachment, index)=><img key={index} src={`${backendUrl}${attachment.url}`} alt={attachment.alt ?? "商品图片"} style={{maxWidth: 280, display: "block", marginBottom: 8}} />)}</div>)}</section>;
}
