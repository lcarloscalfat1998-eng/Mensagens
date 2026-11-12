// Gera o pacote piloto para aprovação:
//   piloto/Piloto_Jantar_03-12_Joinville.pdf  (capa + calendário + peça a peça com o texto de WhatsApp)
//   piloto/00_calendario.png                  (resumo visual do calendário, para mandar no WhatsApp)
// Uso: node render.js && node piloto.js
const { chromium } = require("playwright");
const fs = require("fs"), path = require("path");
const D = __dirname, OUT = path.join(D, "piloto");
fs.mkdirSync(OUT, { recursive: true });

const pngs = fs.readdirSync(path.join(D, "png")).filter(f => f.endsWith(".png")).sort();
const md = fs.readFileSync(path.join(D, "ROTEIRO.md"), "utf8");
const msgs = {};
for (const m of md.matchAll(/\*\*(\d{2}) · ([^·]+)· ([^*]+)\*\*\n((?:> .*\n?)+)/g))
  msgs[m[1]] = { data: m[2].trim(), titulo: m[3].trim(), texto: m[4].replace(/^> /gm, "").trim() };
const dias = { "13/11":"sex","16/11":"seg","18/11":"qua","20/11":"sex","23/11":"seg","24/11":"ter","25/11":"qua","26/11":"qui","27/11":"sex","30/11":"seg","01/12":"ter","02/12":"qua","03/12":"qui","04/12":"sex" };
const esc = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/\*\*(.+?)\*\*/g,"<b>$1</b>").replace(/\[([^\]]+)\]/g,'<span class="tbd">$1</span>');
const items = pngs.map(f => { const n = f.slice(0,2); return { f, n, ...(msgs[n]||{data:"",titulo:f,texto:""}) }; });

const css = `
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Inter,sans-serif;background:#000;color:#fff}
.pg{width:1080px;height:1920px;padding:90px 90px;position:relative;overflow:hidden;page-break-after:always;display:flex;flex-direction:column}
.y{background:#FFC709;color:#000}
.mk{font-weight:900;font-size:64px;letter-spacing:-.04em}
.k{font-size:24px;letter-spacing:.24em;text-transform:uppercase;font-weight:700;color:#FFC709}
.y .k{color:#000}
h1{font-size:120px;font-weight:900;letter-spacing:-.05em;line-height:.95}
h2{font-size:64px;font-weight:800;letter-spacing:-.03em;line-height:1.05}
p{font-size:32px;line-height:1.45}
.tbd{border:2px dashed currentColor;border-radius:6px;padding:0 .2em;opacity:.8}
.row{display:grid;grid-template-columns:170px 90px 1fr;align-items:center;padding:24px 0;border-bottom:1px solid #2a2a2a;font-size:38px;font-weight:600}
.row .d{font-weight:800;color:#FFC709;font-size:40px}.row .w{color:#8a8a8a;text-transform:uppercase;font-size:24px;letter-spacing:.1em}
.row.ev{background:#FFC709;color:#000;margin:0 -24px;padding:20px 24px;border:0}.row.ev .d,.row.ev .w{color:#000}
.img{width:900px;height:1125px;margin:40px auto 0;display:block;box-shadow:0 0 0 1px #2a2a2a}
.bubble{margin-top:40px;background:#1f2c33;border-radius:18px;padding:28px 32px;font-size:28px;line-height:1.45;color:#e9edef;position:relative}
.bubble small{display:block;color:#8696a0;font-size:20px;margin-bottom:10px;letter-spacing:.06em;text-transform:uppercase}
.hd{display:flex;justify-content:space-between;align-items:baseline}
.hd .n{font-size:22px;color:#8a8a8a;letter-spacing:.14em;text-transform:uppercase;font-weight:600}
.arc{display:flex;gap:10px;margin-top:40px}.arc div{flex:1;border-top:6px solid #000;padding-top:16px;font-size:24px;font-weight:600;line-height:1.3}
`;
const capa = `<section class="pg y">
  <div class="mk">xp</div>
  <div style="margin-top:auto">
    <div class="k">Piloto para aprovação</div>
    <h1 style="margin-top:30px">Do Mundo<br>à Mesa</h1>
    <p style="margin-top:40px;font-size:40px;font-weight:600">Jantar reservado · 5 convidados<br>03 de dezembro · Joinville/SC</p>
    <p style="margin-top:50px;max-width:820px">Série de ${items.length} pílulas enviadas pelo WhatsApp de 13/11 a 04/12. A narrativa vai do mundo ao Brasil, do Brasil à família, e da família à mesa.</p>
    <div class="arc"><div>Cenários</div><div>Wealth Planning</div><div>Ecossistema</div><div>A mesa</div></div>
    <p style="margin-top:60px;font-size:26px;font-weight:600">Anfitriões: Luiz Calfat e Glaucio Gonçalves<br>Santa Mistura · 20h</p>
  </div></section>`;
const cal = `<section class="pg" id="cal">
  <div class="k">Arquitetura de datas</div>
  <h2 style="margin-top:20px">${items.length} toques até a mesa</h2>
  <div style="display:flex;gap:30px;margin-top:24px;font-size:24px;color:#8a8a8a"><span>Cenários: 18 e 20/11</span><span>Wealth: 23 a 26/11</span><span>Pessoas: 27/11 a 01/12</span></div>
  <div style="margin-top:50px">${items.map(i=>`<div class="row ${i.data==="03/12"?"ev":""}"><span class="d">${i.data}</span><span class="w">${dias[i.data]||""}</span><span>${esc(i.titulo)}</span></div>`).join("")}</div>
</section>`;
const pages = items.map(i => `<section class="pg">
  <div class="hd"><div class="k">${i.data} · ${dias[i.data]||""}</div><div class="n">${i.n} / ${items.length}</div></div>
  <h2 style="margin-top:18px;font-size:54px">${esc(i.titulo)}</h2>
  <img class="img" src="png/${i.f}">
  <div class="bubble"><small>Texto do WhatsApp</small>${esc(i.texto).replace(/\n/g,"<br>")}</div>
</section>`).join("");

const html = `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>${css}@page{size:1080px 1920px;margin:0}</style></head><body>${capa}${cal}${pages}</body></html>`;
fs.writeFileSync(path.join(D, "piloto.html"), html);

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto("file://" + path.join(D, "piloto.html"), { waitUntil: "networkidle" });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: path.join(OUT, "Piloto_Jantar_03-12_Joinville.pdf"), width: "1080px", height: "1920px", printBackground: true });
  await (await p.$("#cal")).screenshot({ path: path.join(OUT, "00_calendario.png") });
  await b.close();
  console.log("ok", items.length, "peças;", Object.keys(msgs).length, "textos");
})();
