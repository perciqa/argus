import type { Metadata } from "next";
import { ColorSchemeScript, MantineProvider, createTheme } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import "@mantine/core/styles.css";
import "@mantine/charts/styles.css";
import "@mantine/notifications/styles.css";
import "./globals.css";



const theme = createTheme({
  primaryColor: "blue",
  primaryShade: 6,
  fontFamily: "var(--font-inter), Inter, -apple-system, sans-serif",
  fontFamilyMonospace: "'GeistMono', 'Geist Mono', ui-monospace, monospace",
  defaultRadius: "sm",
  components: {
    Card: { defaultProps: { shadow: "xs", withBorder: true, radius: "md" } },
    Badge: { defaultProps: { radius: "sm" } },
    Table: { defaultProps: { highlightOnHover: true } },
  },
});

export const metadata: Metadata = {
  title: "Argus — Agent Reliability Engine",
  description: "Monitor, evaluate, and optimize your AI agents. Real-time trace visibility, FinOps cost tracking, and automated quality assessment.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <ColorSchemeScript defaultColorScheme="dark" />
      </head>
      <body suppressHydrationWarning>
        <MantineProvider theme={theme} defaultColorScheme="dark">
          <Notifications position="top-right" />
          {children}
        </MantineProvider>
      </body>
    </html>
  );
}
