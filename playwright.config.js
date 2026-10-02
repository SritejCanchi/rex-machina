// End-to-end tests: the real index.html and game.js in a real browser.
//   npm run test:e2e
// Locally this uses the installed Chrome. CI installs Playwright's Chromium.
const { defineConfig } = require("@playwright/test");

const PORT = 8123;
const python = process.platform === "win32" ? "python" : "python3";

module.exports = defineConfig({
  testDir: "tests/e2e",
  timeout: 90_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    channel: process.env.CI ? undefined : "chrome",
    trace: "retain-on-failure",
  },
  webServer: {
    command: `${python} -m http.server ${PORT} --bind 127.0.0.1`,
    url: `http://127.0.0.1:${PORT}/index.html`,
    reuseExistingServer: !process.env.CI,
    timeout: 20_000,
    stdout: "ignore",
    stderr: "ignore",
  },
});
