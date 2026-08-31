"use client";

import { useEffect, useState } from "react";
import { AdminProduct } from "./AdminProductTable";

export function AdminProductEditor({product, onClose, onSaved, api, headers}: {product: AdminProduct; onClose: () => void; onSaved: () => void; api: string; headers: HeadersInit}) {
  const [name, setName] = useState(product.name); const [price, setPrice] = useState(String(product.dine_in_price));
  const [member, setMember] = useState(product.member_price == null ? "" : String(product.member_price));
  const [promotion, setPromotion] = useState(product.promotion_price == null ? "" : String(product.promotion_price));
  const [status, setStatus] = useState(product.status); const [message, setMessage] = useState("");
  const [onHand, setOnHand] = useState(String(product.inventory.on_hand ?? "")); const [reserved, setReserved] = useState(String(product.inventory.reserved ?? 0));
  const [alias, setAlias] = useState(""); const [profile, setProfile] = useState(JSON.stringify(product.profile ?? {}, null, 2));
  useEffect(() => { setName(product.name); setPrice(String(product.dine_in_price)); setMember(product.member_price == null ? "" : String(product.member_price)); setPromotion(product.promotion_price == null ? "" : String(product.promotion_price)); setStatus(product.status); setOnHand(String(product.inventory.on_hand ?? "")); setReserved(String(product.inventory.reserved ?? 0)); setProfile(JSON.stringify(product.profile ?? {}, null, 2)); }, [product]);
  async function save() {
    let parsed: Record<string, unknown>; try { parsed = JSON.parse(profile); } catch { setMessage("保存失败：画像 JSON 格式错误"); return; }
    const response = await fetch(`${api}/api/v1/admin/products/${product.id}`, {method: "PUT", headers: {"content-type": "application/json", ...headers}, body: JSON.stringify({name, dine_in_price: Number(price), member_price: member ? Number(member) : null, promotion_price: promotion ? Number(promotion) : null, status, ...parsed})});
    if (!response.ok) { setMessage("商品保存失败，请检查输入"); return; }
    const inventoryResponse = await fetch(`${api}/api/v1/admin/inventory/${product.id}`, {method: "PUT", headers: {"content-type": "application/json", ...headers}, body: JSON.stringify({on_hand: Number(onHand), reserved: Number(reserved), reason: "admin product editor"})});
    if (!inventoryResponse.ok) { setMessage("商品已保存，但库存保存失败"); return; } setMessage("已保存"); onSaved();
  }
  async function addAlias() { if (!alias.trim()) return; const response = await fetch(`${api}/api/v1/admin/products/${product.id}/aliases`, {method: "POST", headers: {"content-type": "application/json", ...headers}, body: JSON.stringify({alias: alias.trim()})}); setMessage(response.ok ? "别名已添加" : "别名添加失败"); if (response.ok) setAlias(""); }
  async function upload(file: File) { const body = new FormData(); body.append("product_id", product.id); body.append("file", file); body.append("alt_text", product.name); const response = await fetch(`${api}/api/v1/admin/media/upload`, {method: "POST", headers, body}); setMessage(response.ok ? "图片已上传" : "图片上传失败"); }
  return <aside style={{position: "fixed", right: 0, top: 0, height: "100vh", width: 360, padding: 24, background: "#fff", boxShadow: "-2px 0 12px #999", zIndex: 2}}>
    <button type="button" onClick={onClose}>关闭</button><h2>编辑商品</h2><p>{product.id}</p>
    <label>商品名称<input value={name} onChange={(e) => setName(e.target.value)} /></label><br />
    <label>堂食新定价<input type="number" min="0" value={price} onChange={(e) => setPrice(e.target.value)} /></label><br />
    <label>会员价<input type="number" min="0" value={member} onChange={(e) => setMember(e.target.value)} placeholder="按政策计算" /></label><br />
    <label>促销价<input type="number" min="0" value={promotion} onChange={(e) => setPromotion(e.target.value)} placeholder="无" /></label><br />
    <label>状态<select value={status} onChange={(e) => setStatus(e.target.value)}><option value="ON_SALE">在售</option><option value="OFF_SALE">下架</option></select></label><br />
    <label>现有库存<input type="number" min="0" value={onHand} onChange={(e) => setOnHand(e.target.value)} /></label><br />
    <label>预留库存<input type="number" min="0" value={reserved} onChange={(e) => setReserved(e.target.value)} /></label><br />
    <label>商品画像 JSON<textarea rows={7} value={profile} onChange={(e) => setProfile(e.target.value)} /></label><br />
    <label>新增别名<input value={alias} onChange={(e) => setAlias(e.target.value)} placeholder="如：红豆烧" /></label> <button type="button" onClick={() => void addAlias()}>添加</button><p>已有别名：{(product.aliases ?? []).join("、") || "无"}</p>
    <label>上传商品图片<input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => { const file = e.target.files?.[0]; if (file) void upload(file); }} /></label><br />
    <button type="button" onClick={() => void save()}>保存</button><p>{message}</p>
  </aside>;
}
