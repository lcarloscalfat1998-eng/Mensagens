// Gera um PNG (1080x1350) para cada pílula em ./png
// Uso:  node render.js
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
(async () => {
  const out = path.join(__dirname, "png");
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 1500 } });
  await page.goto("file://" + path.join(__dirname, "cards.html"), { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  for (const card of await page.$$(".card")) {
    const id = await card.getAttribute("data-id");
    await card.screenshot({ path: path.join(out, id + ".png") });
    console.log("ok", id);
  }
  await browser.close();
})();
