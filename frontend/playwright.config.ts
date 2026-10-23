import { defineConfig } from "@playwright/test";

// Runs against a server that is already up: lonekrav-serve locally, or the container (BASE_URL).
export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  use: { baseURL: process.env.BASE_URL ?? "http://127.0.0.1:8000", browserName: "chromium" },
  projects: [
    { name: "phone", use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
    { name: "desktop", use: { viewport: { width: 1280, height: 800 } } },
  ],
});
