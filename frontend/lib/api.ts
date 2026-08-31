export type Inspector = { goal?: unknown; next_action?: unknown; reason_code?: string; status?: string };
export async function createSession(customerId = "CUS001", groupMemberIds: string[] = []) {
  const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"}/api/v1/sessions`, {method: "POST", headers: {"content-type":"application/json"}, body: JSON.stringify({customer_id: customerId, group_member_ids: groupMemberIds})});
  return response.json();
}

export async function sendMessage(sessionId: string, customerId: string, message: string, confirmed = false, attachments: File[] = [], ownerId = "CUS001") {
  const body = new FormData();
  body.append("message", message);
  body.append("customer_id", customerId);
  body.append("confirmed", String(confirmed));
  attachments.forEach((file) => body.append("attachments", file));
  const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"}/api/v1/sessions/${sessionId}/messages`, {method: "POST", headers: {"X-Session-Owner": ownerId}, body});
  return response.json();
}

export async function confirmOrder(sessionId: string, customerId: string, ownerId = "CUS001") {
  const response = await fetch(`${backendUrl()}/api/v1/sessions/${encodeURIComponent(sessionId)}/confirmations?customer_id=${encodeURIComponent(customerId)}&confirmed=true`, {method: "POST", headers: {"X-Session-Owner": ownerId}});
  if (!response.ok) throw new Error("ORDER_CONFIRMATION_FAILED");
  return response.json();
}

const backendUrl = () => process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export async function getCustomerMemory(customerId: string) {
  const response = await fetch(`${backendUrl()}/api/v1/customers/${encodeURIComponent(customerId)}/memory`);
  if (!response.ok) throw new Error("MEMORY_READ_FAILED");
  return response.json() as Promise<{items: {memory_key: string; memory_value: unknown; memory_type: string}[]}>;
}

export async function deleteCustomerMemory(customerId: string, key: string) {
  const response = await fetch(`${backendUrl()}/api/v1/customers/${encodeURIComponent(customerId)}/memory/${encodeURIComponent(key)}`, {method: "DELETE"});
  if (!response.ok) throw new Error("MEMORY_DELETE_FAILED");
  return response.json();
}
