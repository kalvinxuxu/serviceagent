"use client";

import { useEffect, useState } from "react";
import { AdminProduct, AdminProductTable } from "../../components/AdminProductTable";
import { AdminProductEditor } from "../../components/AdminProductEditor";

const API = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
const ADMIN_HEADERS: HeadersInit = process.env.NEXT_PUBLIC_ADMIN_TOKEN ? {"X-Admin-Token": process.env.NEXT_PUBLIC_ADMIN_TOKEN} : {};
type Featured = {title: string; description: string; product_ids: string[]; enabled: boolean};

export default function AdminPage() {
  const [products, setProducts] = useState<AdminProduct[]>([]); const [selected, setSelected] = useState<AdminProduct | null>(null);
  const [featured, setFeatured] = useState<Featured>({title: "", description: "", product_ids: [], enabled: true});
  const [category, setCategory] = useState(""); const [status, setStatus] = useState(""); const [message, setMessage] = useState("");
  async function load() {
    try {
      const query = new URLSearchParams(); if (category) query.set("category", category); if (status) query.set("status", status);
      const [response, featuredResponse] = await Promise.all([fetch(`${API}/api/v1/admin/product-list?${query}`, {headers: ADMIN_HEADERS}), fetch(`${API}/api/v1/admin/featured-list`, {headers: ADMIN_HEADERS})]);
      if (!response.ok) { setMessage("商品清单加载失败，请检查后端服务"); return; }
      const productData = await response.json(); setProducts(productData.items ?? []); if (featuredResponse.ok) setFeatured(await featuredResponse.json());
    } catch { setMessage("商品清单加载失败，请稍后刷新"); }
  }
  useEffect(() => { void load(); }, [category, status]);
  async function updateFeatured(product: AdminProduct) { const ids = product.featured ? featured.product_ids.filter((id) => id !== product.id) : [...featured.product_ids, product.id]; const response = await fetch(`${API}/api/v1/admin/featured-list`, {method: "PUT", headers: {"content-type": "application/json", ...ADMIN_HEADERS}, body: JSON.stringify({...featured, product_ids: ids})}); if (response.ok) { setFeatured(await response.json()); void load(); } else setMessage("必吃榜更新失败"); }
  return <main style={{maxWidth: 1280, margin: "32px auto", fontFamily: "sans-serif", padding: 16}}><h1>山也面包 · 管理后台</h1><p>{message || "商品、价格、库存、图片和必吃榜"}</p><p><a href="/admin/benchmark">Benchmark 报告</a> · <a href="/admin/trace">会话 Trace</a></p>
    <section><h2>商品清单</h2><label>品类 <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="全部" /></label> <label>状态 <select value={status} onChange={(e) => setStatus(e.target.value)}><option value="">全部</option><option value="ON_SALE">在售</option><option value="OFF_SALE">下架</option></select></label> <button type="button" onClick={() => void load()}>刷新</button><div style={{overflowX: "auto", marginTop: 12}}><AdminProductTable products={products} onEdit={setSelected} onToggleFeatured={(product) => void updateFeatured(product)} /></div></section>
    <section><h2>商品维护</h2><p>点击表格中的“编辑”维护商品、库存、画像、别名和图片。</p></section>
    {selected && <AdminProductEditor product={selected} api={API} headers={ADMIN_HEADERS} onClose={() => setSelected(null)} onSaved={() => { setSelected(null); void load(); }} />}
  </main>;
}
