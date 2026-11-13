// Converte um HTML local em PDF A4 com fundo. Uso: node pdf.js entrada.html saida.pdf
const { chromium } = require('playwright');
(async () => {
  const [entrada, saida] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1000, height: 1400 } });
  await page.goto('file://' + require('path').resolve(entrada), { waitUntil: 'networkidle' }).catch(() => {});
  await page.waitForTimeout(1200);
  await page.emulateMedia({ media: 'screen' });
  await page.pdf({ path: saida, format: 'A4', printBackground: true, scale: 0.78,
                   margin: { top: '0', bottom: '0', left: '0', right: '0' } });
  await browser.close();
})();
