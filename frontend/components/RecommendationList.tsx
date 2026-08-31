export function RecommendationList({items}: {items: {name: string; price: number}[]}) { return <ul>{items.map(item=><li key={item.name}>{item.name}（{item.price}元）</li>)}</ul>; }
