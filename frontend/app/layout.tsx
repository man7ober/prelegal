import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
	title: "Prelegal | Agreement Workspace",
	description: "Continue to your Prelegal agreement workspace.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
