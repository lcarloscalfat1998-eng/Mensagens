const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa6");
const { applyTheme } = require("/root/.claude/skills/synced/eadbc07d-170b-447c-8d1a-4c1d8d4eea8c_7b97e564-f152-4f3c-b098-0fe47ff08360/pptx/scripts/apply_theme.js");

const OUT = process.argv[2] || "deck.pptx";

const HEX = {
  dark: "141414", teal: "FFC709", gold: "E0A800", light: "F3F3F3",
  white: "FFFFFF", text: "1F1F1F", muted: "5F5F5F",
};
const THEME = {
  name: "XP Fee Based",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: HEX.text, lt1: HEX.white, dk2: HEX.dark, lt2: HEX.light,
    accent1: HEX.teal, accent2: HEX.gold, accent3: "8C8C8C", accent4: HEX.muted,
    accent5: "BDBDBD", accent6: "FFC709", hlink: "B38A00", folHlink: HEX.muted,
  },
};

async function icon(Comp, color = "#141414") {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color, size: 256 }));
  const buf = await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10 x 5.625
  pres.title = "Conversão para Fee Based";
  pres.subject = "Treinamento para novos assessores";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  // ---------- Layouts ----------
  pres.defineSlideMaster({
    title: "CAPA",
    background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.5, w: 8.8, h: 1.5, fontSize: 40, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.2, w: 8.8, h: 1.0, fontSize: 18, color: C.accent5, valign: "top", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "CONTEUDO",
    background: { color: C.background1 },
    margin: [0.5, 0.5, 0.5, 0.5],
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.75, fontSize: 30, bold: true, color: C.text2, valign: "middle", margin: 0 }, text: "" } },
      { text: { text: "Treinamento Fee Based · Novos assessores", options: { x: 0.5, y: 5.2, w: 6, h: 0.3, fontSize: 10, color: C.accent4, margin: 0 } } },
    ],
    slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: C.accent4, align: "right" },
  });
  pres.defineSlideMaster({
    title: "ENCERRAMENTO",
    background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.75, fontSize: 30, bold: true, color: C.background1, valign: "middle", margin: 0 }, text: "" } },
    ],
    slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: C.accent5, align: "right" },
  });

  const flag = (s, x, y, w = 1.0) =>
    s.addText("REVISAR", { x, y, w, h: 0.26, fontSize: 9, bold: true, color: C.text2, fill: { color: C.accent1 }, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Marcador revisar" });

  const circleIcon = (s, data, x, y, d, fillColor) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fillColor }, line: { type: "none" }, objectName: "Círculo ícone" });
    const p = d * 0.25;
    s.addImage({ data, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, altText: "ícone" });
  };

  const ic = {
    chart: await icon(fa.FaChartLine), users: await icon(fa.FaUsers), coins: await icon(fa.FaCoins),
    scale: await icon(fa.FaScaleBalanced), handshake: await icon(fa.FaHandshake), unlock: await icon(fa.FaLockOpen),
    clipboard: await icon(fa.FaClipboardList), compass: await icon(fa.FaCompass), comments: await icon(fa.FaComments),
    calendar: await icon(fa.FaCalendarCheck), check: await icon(fa.FaCheck), quote: await icon(fa.FaQuoteLeft),
    phone: await icon(fa.FaHeadset),
  };

  // ---------- Seções ----------
  // 1. Capa
  pres.addSection({ title: "Abertura" });
  let s = pres.addSlide({ masterName: "CAPA", sectionTitle: "Abertura" });
  s.addText("Conversão para Fee Based: da filosofia à prática", { placeholder: "title" });
  s.addText("Treinamento para novos assessores · Case real da Alta Renda", { placeholder: "body" });
  s.addText("Novembro de 2026", { x: 0.6, y: 4.7, w: 5, h: 0.35, fontSize: 14, color: C.accent6, margin: 0, isTextBox: true });
  s.addNotes(
    "Abertura (1 min).\n" +
    "Objetivo do treinamento: mostrar, a partir de um case real da Alta Renda, como conduzir a conversa de migração de clientes para Fee Based.\n" +
    "Mensagem central: Fee Based não é cobrar mais, é mudar a forma de alinhamento entre cliente e assessor.\n" +
    "Fonte: ata da reunião de 16/11/2026 (transcrição não revisada).\n" +
    "[REVISAR] Se quiser citar o assessor do case pelo nome, confirme a grafia (a ata cita Matheus Pohlmann e João, mas não deixa claro quem é o assessor e quem é o gestor)."
  );

  // 2. O case em números
  pres.addSection({ title: "O case" });
  s = pres.addSlide({ masterName: "CONTEUDO", sectionTitle: "O case" });
  s.addText("O case em números: um mês de conversões", { placeholder: "title" });
  const stats = [
    { n: "R$ 12,5 mi", l: "convertidos para Fee Based em um mês", i: ic.chart, rev: false },
    { n: "12 a 13", l: "clientes migrados", i: ic.users, rev: false },
    { n: "~R$ 131 mil", l: "receita do mês reportada", i: ic.coins, rev: true },
  ];
  stats.forEach((st, k) => {
    const x = 0.5 + k * 3.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.3, w: 2.8, h: 2.5, rectRadius: 0.12, fill: { color: C.background2 }, line: { type: "none" }, objectName: "Card número " + (k + 1) });
    circleIcon(s, st.i, x + 0.3, 1.55, 0.6, C.accent1);
    s.addText(st.n, { x: x + 0.3, y: 2.3, w: 2.3, h: 0.7, fontSize: 30, bold: true, color: C.text2, fontFace: "Cambria", margin: 0, isTextBox: true, fit: "shrink" });
    s.addText(st.l, { x: x + 0.3, y: 3.0, w: 2.3, h: 0.6, fontSize: 14, color: C.accent4, margin: 0, valign: "top", isTextBox: true });
    if (st.rev) flag(s, x + 1.5, 1.7);
  });
  s.addText("Volume diferenciado na Alta Renda, construído sem abrir mão da experiência do cliente, e com efeito na receita recorrente dos próximos meses.", {
    x: 0.5, y: 4.1, w: 9.0, h: 0.7, fontSize: 15, italic: true, color: C.text2, margin: 0, isTextBox: true,
  });
  s.addNotes(
    "O case (2 min).\n" +
    "Em cerca de um mês, o assessor converteu aproximadamente R$ 12,5 milhões, distribuídos em 12 a 13 clientes.\n" +
    "Ponto importante: esse movimento ainda não aparece inteiro nos indicadores de receita. O efeito vem nos meses seguintes, porque a receita passa a ser recorrente.\n" +
    "O gestor destacou que o volume é diferenciado dentro da Alta Renda e sugeriu transformar a prática em case interno, que é este treinamento.\n" +
    "O assessor tinha receio de como a estratégia seria vista internamente (menos receita de curto prazo), mas a convicção é que a base Fee Based gera resultado superior no longo prazo.\n" +
    "[REVISAR] Receita do mês de ~R$ 131 mil: a ata não deixa claro se é a receita total do assessor ou só a parte gerada pelo Fee Based. Confirme antes de apresentar."
  );

  // 3. Mudança de postura
  pres.addSection({ title: "Filosofia" });
  s = pres.addSlide({ masterName: "CONTEUDO", sectionTitle: "Filosofia" });
  s.addText("A virada: de neutro a recomendador", { placeholder: "title" });
  // Antes
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 1.3, w: 4.1, h: 3.5, rectRadius: 0.12, fill: { color: C.background2 }, line: { type: "none" }, objectName: "Card antes" });
  s.addText("ANTES", { x: 0.8, y: 1.5, w: 3.5, h: 0.35, fontSize: 14, bold: true, color: C.accent4, charSpacing: 2, margin: 0, isTextBox: true });
  s.addText("Postura extremamente neutra", { x: 0.8, y: 1.9, w: 3.5, h: 0.5, fontSize: 20, bold: true, color: C.text2, fontFace: "Cambria", margin: 0, isTextBox: true });
  s.addText([
    { text: "Apresentava transacional e Fee Based lado a lado", options: { bullet: true, breakLine: true } },
    { text: "Sem direcionamento claro", options: { bullet: true, breakLine: true } },
    { text: "Decisão 100% nas mãos do cliente", options: { bullet: true } },
  ], { x: 0.8, y: 2.8, w: 3.6, h: 1.8, fontSize: 15, color: C.text1, paraSpaceAfter: 8, valign: "top", margin: 0, isTextBox: true });
  // seta
  s.addShape(pres.shapes.RIGHT_ARROW, { x: 4.75, y: 2.8, w: 0.5, h: 0.5, fill: { color: C.accent2 }, line: { type: "none" }, objectName: "Seta" });
  // Agora
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.4, y: 1.3, w: 4.1, h: 3.5, rectRadius: 0.12, fill: { color: C.text2 }, line: { type: "none" }, objectName: "Card agora" });
  s.addText("AGORA", { x: 5.7, y: 1.5, w: 3.5, h: 0.35, fontSize: 14, bold: true, color: C.accent6, charSpacing: 2, margin: 0, isTextBox: true });
  s.addText("Opcionalidade + opinião profissional", { x: 5.7, y: 1.9, w: 3.6, h: 0.5, fontSize: 20, bold: true, color: C.background1, fontFace: "Cambria", margin: 0, isTextBox: true, fit: "shrink" });
  s.addText([
    { text: "O cliente continua escolhendo", options: { bullet: true, breakLine: true } },
    { text: "O assessor diz qual formato considera melhor para a construção patrimonial de longo prazo", options: { bullet: true, breakLine: true } },
    { text: "E explica por quê", options: { bullet: true } },
  ], { x: 5.7, y: 2.8, w: 3.6, h: 1.8, fontSize: 15, color: C.background1, paraSpaceAfter: 8, valign: "top", margin: 0, isTextBox: true });
  s.addNotes(
    "A virada de postura (2 min).\n" +
    "Antes, o assessor apresentava os dois modelos sem direcionamento e deixava a decisão inteira com o cliente.\n" +
    "Ele percebeu que neutralidade total não ajuda o cliente a decidir. Passou a manter a escolha com o cliente, mas dando sua visão profissional sobre o formato mais adequado.\n" +
    "Para os novos assessores: ter opinião não é pressionar. A escolha continua sendo do cliente."
  );

  // 4. Por que Fee Based
  s = pres.addSlide({ masterName: "CONTEUDO", sectionTitle: "Filosofia" });
  s.addText("Por que defendemos o Fee Based", { placeholder: "title" });
  const pilares = [
    { i: ic.scale, t: "Menos conflito econômico", d: "A remuneração não depende do produto escolhido." },
    { i: ic.handshake, t: "Mais alinhamento", d: "Assessor e cliente ganham juntos quando o patrimônio cresce." },
    { i: ic.unlock, t: "Liberdade na carteira", d: "Dá para recomendar o mais eficiente, inclusive produtos de baixo custo." },
  ];
  pilares.forEach((p, k) => {
    const y = 1.3 + k * 1.2;
    circleIcon(s, p.i, 0.6, y, 0.8, C.accent1);
    s.addText(p.t, { x: 1.7, y: y, w: 7.5, h: 0.4, fontSize: 20, bold: true, color: C.text2, fontFace: "Cambria", margin: 0, isTextBox: true });
    s.addText(p.d, { x: 1.7, y: y + 0.42, w: 7.5, h: 0.4, fontSize: 15, color: C.text1, margin: 0, isTextBox: true });
  });
  s.addNotes(
    "Racional central (2 min).\n" +
    "1. Reduz conflitos econômicos: no transacional, a remuneração do assessor depende do produto, e isso pode influenciar a recomendação.\n" +
    "2. Aumenta o alinhamento: no Fee Based a taxa incide sobre o patrimônio, então assessor e cliente querem a mesma coisa.\n" +
    "3. Dá liberdade na construção da carteira: o assessor pode usar produtos mais eficientes e baratos (ex.: ETFs) sem que isso derrube sua remuneração."
  );

  // 5. Estrutura da reunião
  pres.addSection({ title: "Reunião de conversão" });
  s = pres.addSlide({ masterName: "CONTEUDO", sectionTitle: "Reunião de conversão" });
  s.addText("Roteiro da reunião de conversão: 3 blocos", { placeholder: "title" });
  const blocos = [
    { n: "1", i: ic.clipboard, t: "Planejamento financeiro", items: ["Objetivos do cliente", "Atualização patrimonial", "Evolução vs. metas", "Liquidez e necessidades futuras"] },
    { n: "2", i: ic.compass, t: "Estratégia de investimentos", items: ["Agir como se o cliente já fosse Fee Based", "Recomendar sem pensar na remuneração", "Foco só na melhor solução"] },
    { n: "3", i: ic.comments, t: "Modelo de atendimento", items: ["Só agora entra o Fee Based", "Relacionamento e frequência de reuniões", "Acompanhamento contínuo"] },
  ];
  blocos.forEach((b, k) => {
    const x = 0.5 + k * 3.1;
    const isLast = k === 2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.3, w: 2.8, h: 3.6, rectRadius: 0.12, fill: { color: isLast ? C.text2 : C.background2 }, line: { type: "none" }, objectName: "Bloco " + b.n });
    circleIcon(s, b.i, x + 0.25, 1.5, 0.6, isLast ? C.accent2 : C.accent1);
    s.addText("BLOCO " + b.n, { x: x + 1.0, y: 1.55, w: 1.6, h: 0.5, fontSize: 14, bold: true, color: isLast ? C.accent6 : C.accent4, valign: "middle", charSpacing: 2, margin: 0, isTextBox: true });
    s.addText(b.t, { x: x + 0.25, y: 2.25, w: 2.35, h: 0.7, fontSize: 17, bold: true, color: isLast ? C.background1 : C.text2, fontFace: "Cambria", valign: "top", margin: 0, isTextBox: true });
    s.addText(b.items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < b.items.length - 1 } })), {
      x: x + 0.25, y: 3.0, w: 2.4, h: 1.8, fontSize: 14, color: isLast ? C.background1 : C.text1, paraSpaceAfter: 4, valign: "top", margin: 0, isTextBox: true,
    });
    if (k < 2) s.addShape(pres.shapes.CHEVRON, { x: x + 2.85, y: 2.95, w: 0.2, h: 0.35, fill: { color: C.accent2 }, line: { type: "none" }, objectName: "Seta" });
  });
  s.addNotes(
    "Estrutura da reunião (3 min). A ordem importa.\n" +
    "Bloco 1 – Planejamento financeiro: revisar objetivos, atualizar o patrimônio, ver a evolução em relação ao que foi combinado, revisar liquidez e necessidades futuras.\n" +
    "Bloco 2 – Estratégia de investimentos: o assessor age exatamente como agiria se o cliente já estivesse em Fee Based. A recomendação é feita sem considerar impacto comercial ou remuneração.\n" +
    "Bloco 3 – Modelo de atendimento: só depois de entregar valor nos dois primeiros blocos o tema Fee Based entra. Apresenta-se o relacionamento, a frequência das reuniões e a lógica de acompanhamento contínuo.\n" +
    "Dica: o cliente já viu, na prática, como é ser atendido no modelo antes de ouvir falar dele."
  );

  // 6. Speeches 1-3
  pres.addSection({ title: "Argumentação" });
  s = pres.addSlide({ masterName: "CONTEUDO", sectionTitle: "Argumentação" });
  s.addText("Speeches que funcionam (1/2)", { placeholder: "title" });
  const q1 = [
    { t: "Liberdade de escolha", q: "“Existem dois modelos no mercado e a XP é uma das poucas instituições que permite ao cliente escolher. A decisão é sua.”" },
    { t: "Não é sobre cobrar mais", q: "“Essa conversa não é para aumentar ou diminuir custo. É para entender qual filosofia de atendimento faz mais sentido para você.”" },
    { t: "Imparcialidade", q: "“Prefiro trabalhar via Fee Based: posso recomendar o que considero mais adequado sem que a remuneração do produto influencie a carteira.”" },
  ];
  q1.forEach((q, k) => {
    const y = 1.25 + k * 1.3;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 9.0, h: 1.15, rectRadius: 0.1, fill: { color: C.background2 }, line: { type: "none" }, objectName: "Speech " + (k + 1) });
    circleIcon(s, ic.quote, 0.7, y + 0.3, 0.55, C.accent1);
    s.addText(q.t, { x: 1.45, y: y + 0.1, w: 7.8, h: 0.35, fontSize: 15, bold: true, color: C.text2, margin: 0, isTextBox: true });
    s.addText(q.q, { x: 1.45, y: y + 0.45, w: 7.8, h: 0.65, fontSize: 14, italic: true, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  });
  s.addNotes(
    "Speeches 1 a 3 (3 min).\n" +
    "1. Liberdade de escolha: 'Existem dois modelos no mercado e a XP é uma das poucas instituições que permite ao cliente escolher qual deles faz mais sentido para ele.' 'Você pode continuar no transacional ou migrar para Fee Based. A decisão é sua.'\n" +
    "2. Não é sobre cobrar mais: 'Eu não quero trazer a sensação de que estou te onerando. O objetivo não é cobrar mais. O objetivo é mudar a forma de alinhamento entre cliente e assessor.'\n" +
    "3. Imparcialidade: 'Minha opinião pessoal é que prefiro trabalhar via Fee Based.' 'Ele gera mais imparcialidade no atendimento.'\n" +
    "Atenção de compliance: frases sobre a XP e o mercado devem estar alinhadas com o material oficial da casa."
  );

  // 7. Speeches 4-7
  s = pres.addSlide({ masterName: "CONTEUDO", sectionTitle: "Argumentação" });
  s.addText("Speeches que funcionam (2/2)", { placeholder: "title" });
  const q2 = [
    { t: "O exemplo dos ETFs", q: "“Se eu tiver cem clientes só em ETFs, praticamente não consigo ser remunerado por esse trabalho.”" },
    { t: "Transparência de custos", q: "“Qualquer dúvida sobre custo eu respondo de maneira brutalmente transparente.”" },
    { t: "Sem pressão", q: "“Não precisa decidir agora. Pode decidir no ano que vem, sem problema.”" },
    { t: "Estudo da Vanguard", q: "“O maior valor do assessor está na otimização fiscal, na disciplina e na prevenção de erros.”" },
  ];
  q2.forEach((q, k) => {
    const x = 0.5 + (k % 2) * 4.6;
    const y = 1.25 + Math.floor(k / 2) * 1.85;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 4.4, h: 1.7, rectRadius: 0.1, fill: { color: C.background2 }, line: { type: "none" }, objectName: "Speech " + (k + 4) });
    s.addText(String(k + 4), { x: x + 0.2, y: y + 0.2, w: 0.45, h: 0.45, shape: pres.shapes.OVAL, fill: { color: C.accent1 }, color: C.text2, fontSize: 15, bold: true, align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(q.t, { x: x + 0.8, y: y + 0.2, w: 3.4, h: 0.45, fontSize: 15, bold: true, color: C.text2, valign: "middle", margin: 0, isTextBox: true });
    s.addText(q.q, { x: x + 0.2, y: y + 0.8, w: 4.0, h: 0.8, fontSize: 14, italic: true, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  });
  s.addNotes(
    "Speeches 4 a 7 (3 min).\n" +
    "4. Exemplo dos ETFs: mostra o conflito do modelo transacional. Recomendações de baixo custo, ótimas para o cliente, ficam economicamente difíceis de sustentar quando a remuneração depende só do produto. O Fee Based resolve isso.\n" +
    "5. Transparência de custos: 'Se optar pelo modelo transacional, sempre vou mostrar exatamente quanto cada produto remunera.'\n" +
    "6. Construção de confiança: 'Quero apenas ter uma conversa franca sobre os modelos.' A ausência de pressão comercial aumentou muito a receptividade dos clientes.\n" +
    "7. Estudo da Vanguard sobre o valor gerado pelo assessor (conhecido como 'Advisor's Alpha'): 'O maior valor de um assessor não está na indicação de um produto específico, e sim na otimização fiscal, na disciplina de investimentos, na prevenção de erros e na construção patrimonial de longo prazo. O Fee Based viabiliza esse acompanhamento de forma mais eficiente.'\n" +
    "[REVISAR] Confirme o nome e os números do estudo da Vanguard antes de citá-los ao cliente."
  );

  // 8. Modelo de atendimento
  pres.addSection({ title: "Modelo e preço" });
  s = pres.addSlide({ masterName: "CONTEUDO", sectionTitle: "Modelo e preço" });
  s.addText("O que o cliente recebe: 3 encontros por ano", { placeholder: "title" });
  // linha do tempo
  s.addShape(pres.shapes.LINE, { x: 1.1, y: 1.85, w: 7.8, h: 0, line: { color: C.accent5, width: 2 }, objectName: "Linha do tempo" });
  const enc = [
    { t: "Planejamento financeiro", items: ["Revisão patrimonial", "Avaliação de objetivos"] },
    { t: "Estratégia de investimentos", items: ["Alocação de carteira", "Discussão de cenários"] },
    { t: "Rebalanceamento", items: ["Ajustes patrimoniais", "Revisão das estratégias"] },
  ];
  enc.forEach((e, k) => {
    const cx = 1.1 + k * 3.9;
    const x = 0.5 + k * 3.1;
    s.addText(String(k + 1), { x: x + 1.1, y: 1.45, w: 0.8, h: 0.8, shape: pres.shapes.OVAL, fill: { color: C.accent1 }, color: C.text2, fontSize: 22, bold: true, fontFace: "Cambria", align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText("Encontro " + (k + 1), { x, y: 2.4, w: 2.8, h: 0.3, fontSize: 12, bold: true, color: C.accent4, align: "center", charSpacing: 1, margin: 0, isTextBox: true });
    s.addText(e.t, { x, y: 2.7, w: 2.8, h: 0.4, fontSize: 15, bold: true, color: C.text2, fontFace: "Cambria", align: "center", margin: 0, isTextBox: true });
    s.addText(e.items.join(" · "), { x: x + 0.1, y: 3.1, w: 2.6, h: 0.5, fontSize: 14, color: C.text1, align: "center", valign: "top", margin: 0, isTextBox: true });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 3.95, w: 9.0, h: 0.95, rectRadius: 0.1, fill: { color: C.text2 }, line: { type: "none" }, objectName: "Atendimento contínuo" });
  circleIcon(s, ic.phone, 0.75, 4.1, 0.65, C.accent2);
  s.addText([
    { text: "Entre os encontros: ", options: { bold: true, color: C.accent6 } },
    { text: "atendimento contínuo para eventos relevantes, dúvidas e mudanças de cenário.", options: { color: C.background1 } },
  ], { x: 1.6, y: 3.95, w: 7.7, h: 0.95, fontSize: 15, valign: "middle", margin: 0, isTextBox: true });
  s.addNotes(
    "Modelo de atendimento vendido ao cliente (2 min).\n" +
    "O relacionamento é estruturado em três encontros formais por ano:\n" +
    "Encontro 1 – Planejamento financeiro, revisão patrimonial e avaliação de objetivos.\n" +
    "Encontro 2 – Estratégia de investimentos, alocação de carteira e discussão de cenários.\n" +
    "Encontro 3 – Rebalanceamento, ajustes patrimoniais e revisão das estratégias.\n" +
    "Além disso, o assessor fica disponível para eventos relevantes, dúvidas e mudanças de cenário.\n" +
    "Isso torna concreto o que o cliente 'compra' com a taxa: método e frequência, não produto."
  );

  // 9. Precificação
  s = pres.addSlide({ masterName: "CONTEUDO", sectionTitle: "Modelo e preço" });
  s.addText("Política de precificação", { placeholder: "title" });
  const hdr = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: 15 } });
  const cell = (t, b = false) => ({ text: t, options: { color: C.text1, bold: b, fontSize: 15 } });
  s.addTable([
    [hdr("Perfil do cliente"), hdr("Taxa anual")],
    [cell("Até R$ 500 mil"), cell("0,9% a 1,0%", true)],
    [cell("De R$ 500 mil a R$ 3 milhões"), cell("0,8%", true)],
    [cell("Patrimônio elevado / perfil Unique"), cell("0,7%", true)],
  ], {
    x: 0.5, y: 1.3, w: 5.2, colW: [3.4, 1.8], rowH: 0.6, valign: "middle", margin: [0, 0.15, 0, 0.15],
    border: { type: "solid", pt: 0.75, color: "D0D0D0" }, fill: { color: C.background1 }, objectName: "Tabela de taxas",
  });
  s.addText("[REVISAR] Confirme se as taxas são anuais e se a tabela é a vigente.", { x: 0.5, y: 3.85, w: 5.2, h: 0.5, fontSize: 11, italic: true, bold: true, color: C.accent4, margin: 0, isTextBox: true });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.0, y: 1.3, w: 3.5, h: 2.95, rectRadius: 0.12, fill: { color: C.background2 }, line: { type: "none" }, objectName: "Regra de ouro" });
  s.addText("Regra de ouro", { x: 6.25, y: 1.5, w: 3.0, h: 0.4, fontSize: 18, bold: true, color: C.text2, fontFace: "Cambria", margin: 0, isTextBox: true });
  s.addText("A referência é a média de remuneração que a carteira atual do cliente já gera.", { x: 6.25, y: 2.0, w: 3.05, h: 1.1, fontSize: 15, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  s.addText("Assim o cliente não sente aumento de custo: muda a filosofia de atendimento, não a cobrança.", { x: 6.25, y: 3.15, w: 3.05, h: 1.4, fontSize: 15, italic: true, color: C.text2, valign: "top", margin: 0, isTextBox: true });
  s.addNotes(
    "Precificação (2 min).\n" +
    "Até R$ 500 mil: 0,9% a 1,0%. De R$ 500 mil a R$ 3 milhões: 0,8%. Patrimônio elevado / perfil Unique: 0,7%.\n" +
    "Regra principal: a referência é a média de remuneração que a carteira atual do cliente já gera. Isso evita a percepção de aumento de custo e reforça que a mudança é de filosofia, não de cobrança.\n" +
    "[REVISAR] A ata não diz se as taxas são anuais nem se a tabela é oficial ou uma prática do assessor. Confirme com a gestão antes de usar em treinamento."
  );

  // 10. Como aplicar
  pres.addSection({ title: "Aplicação" });
  s = pres.addSlide({ masterName: "ENCERRAMENTO", sectionTitle: "Aplicação" });
  s.addText("Na sua próxima reunião", { placeholder: "title" });
  const passos = [
    "Comece pelo planejamento, não pelo produto",
    "Recomende como se o cliente já fosse Fee Based",
    "Só no fim apresente o modelo de atendimento",
    "Dê sua opinião, mas deixe a escolha com o cliente",
    "Use a remuneração atual como referência de taxa",
    "Zero pressão: \"pode decidir no ano que vem\"",
  ];
  passos.forEach((p, k) => {
    const x = 0.5 + (k % 2) * 4.6;
    const y = 1.3 + Math.floor(k / 2) * 1.05;
    circleIcon(s, ic.check, x, y, 0.55, C.accent1);
    s.addText(p, { x: x + 0.75, y: y - 0.1, w: 3.7, h: 0.75, fontSize: 15, color: C.background1, valign: "middle", margin: 0, isTextBox: true });
  });
  s.addText("Fee Based não é cobrar mais. É mudar o alinhamento entre cliente e assessor.", {
    x: 0.5, y: 4.55, w: 8.4, h: 0.5, fontSize: 16, italic: true, bold: true, color: C.accent6, margin: 0, isTextBox: true,
  });
  s.addNotes(
    "Encerramento (2 min) + perguntas.\n" +
    "Recapitule o checklist e proponha um exercício: cada novo assessor escolhe 2 ou 3 clientes da base para aplicar o roteiro de 3 blocos na próxima revisão.\n" +
    "Sugestão: acompanhar a evolução da receita recorrente da carteira mês a mês, já que o efeito das conversões aparece nos meses seguintes.\n" +
    "Observação: a ata cita 'próximos passos' no tema central, mas não detalha quais. Este checklist foi montado a partir do conteúdo da reunião. Ajuste se houver próximos passos combinados."
  );

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("ok", OUT);
})();
