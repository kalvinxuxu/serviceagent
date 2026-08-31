"use client";

export type AdminProduct = {
  id: string; name: string; category: string; dine_in_price: number;
  member_price?: number | null; promotion_price?: number | null; display_discount_price?: number | null;
  inventory: {on_hand?: number | null; reserved?: number | null; available_quantity?: number | null; status: string};
  primary_media?: {media_id: string; url: string; alt: string} | null;
  display_tags: string[]; featured: boolean; status: string; profile?: Record<string, unknown>; aliases: string[];
};

export function AdminProductTable({products, onEdit, onToggleFeatured}: {products: AdminProduct[]; onEdit: (product: AdminProduct) => void; onToggleFeatured: (product: AdminProduct) => void}) {
  return <table style={{width: "100%", borderCollapse: "collapse", background: "#fff"}}>
    <thead><tr>{["商品", "品类", "堂食价", "优惠价", "库存", "图片", "标签", "适合人群", "适合场景", "特色", "必吃榜", "状态", "操作"].map((title) => <th key={title} style={{textAlign: "left", padding: 10, borderBottom: "1px solid #ddd"}}>{title}</th>)}</tr></thead>
    <tbody>{products.map((product) => <tr key={product.id}>
      <td style={{padding: 10}}>{product.name}</td><td>{product.category}</td><td>¥{product.dine_in_price}</td>
      <td>{product.display_discount_price == null ? "—" : `¥${product.display_discount_price}`}</td>
      <td>{product.inventory.available_quantity == null ? "—" : `${product.inventory.available_quantity}（${product.inventory.status}）`}</td>
      <td>{product.primary_media ? <img src={product.primary_media.url} alt={product.primary_media.alt || product.name} width={42} height={42} style={{objectFit: "cover", borderRadius: 6}} /> : "缺图"}</td>
      <td>{product.display_tags.join(" · ") || "—"}</td><td>{listProfile(product, "audience_tags")}</td><td>{listProfile(product, "scene_tags")}</td><td>{listProfile(product, "feature_tags")}</td><td><button type="button" onClick={() => onToggleFeatured(product)}>{product.featured ? "已加入" : "加入榜单"}</button></td><td>{product.status === "ON_SALE" ? "在售" : "下架"}</td>
      <td><button type="button" onClick={() => onEdit(product)}>编辑</button></td>
    </tr>)}</tbody>
  </table>;
}

function listProfile(product: AdminProduct, key: string) {
  const value = product.profile?.[key];
  return Array.isArray(value) && value.length ? value.join(" · ") : "—";
}
