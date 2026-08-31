import { ReactNode } from "react";

export const metadata = { title: "Shanye Shop Demo", description: "虚拟智能客服 Agent" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
