import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import "@radix-ui/themes/styles.css";
import { Suspense } from "react";
import AuthProvider from "@/utils/auth";
import { Theme } from "@radix-ui/themes";
import { PublicEnvScript } from "next-runtime-env";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Experimentation Engine",
  description: "A platform for running experiments by IDinsight",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <head>
        <meta name="viewport" content="initial-scale=1, width=device-width" />
        <script src="https://accounts.google.com/gsi/client" async></script>
        <PublicEnvScript />
      </head>
      <body className={"font-sans antialiased"}>
        <Suspense>
          <Theme>
            <AuthProvider>{children}</AuthProvider>
          </Theme>
        </Suspense>
      </body>
    </html>
  );
}
