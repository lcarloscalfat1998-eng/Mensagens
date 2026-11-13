// Gera a foto do grupo do WhatsApp (1080x1080) em duas versões: piloto/capa-grupo-*.png
// Uso: node capa.js
const { chromium } = require("playwright");
const path = require("path");
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 2400, height: 1200 } });
  await p.goto("file://" + path.join(__dirname, "capa-grupo.html"), { waitUntil: "networkidle" });
  await p.evaluate(() => document.fonts.ready);
  for (const c of await p.$$(".capa")) {
    const id = await c.getAttribute("data-id");
    await c.screenshot({ path: path.join(__dirname, "piloto", id + ".png") });
    console.log("ok", id);
  }
  await b.close();
})();
