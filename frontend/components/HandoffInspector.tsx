export function HandoffInspector({context}: {context: unknown}) { return <aside><h2>人工接管上下文</h2><pre>{JSON.stringify(context, null, 2)}</pre></aside>; }
