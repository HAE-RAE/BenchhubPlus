import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Inter as Geist substitute — Google-hosted, no extra dep needed.
const fontSans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap"
});

const fontMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap"
});

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://benchhubplus.app";
const DESCRIPTION =
  "Operational LLM evaluation workspace for benchmark planning, execution, and leaderboard governance.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "BenchHub Plus — LLM evaluation operations",
    template: "%s · BenchHub Plus"
  },
  description: DESCRIPTION,
  applicationName: "BenchHub Plus",
  keywords: [
    "LLM evaluation",
    "benchmark",
    "leaderboard",
    "Korean NLP",
    "model comparison",
    "BenchHub"
  ],
  openGraph: {
    type: "website",
    siteName: "BenchHub Plus",
    title: "BenchHub Plus — LLM evaluation operations",
    description: DESCRIPTION,
    url: SITE_URL
  },
  twitter: {
    card: "summary_large_image",
    title: "BenchHub Plus",
    description: DESCRIPTION
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-snippet": -1, "max-image-preview": "large" }
  },
  icons: {
    icon: "/favicon.ico"
  }
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0a" }
  ]
};

// Runs before paint to apply the user's stored theme preference. Inlining
// this avoids a flash-of-wrong-theme on first load.
const themeBootstrap = `(() => {
  try {
    var t = localStorage.getItem("benchhub.theme");
    if (t === "light" || t === "dark") {
      document.documentElement.setAttribute("data-theme", t);
    }
  } catch (e) {}
})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${fontSans.variable} ${fontMono.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeBootstrap }} />
      </head>
      <body className="font-sans antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
