// Chatbot de WhatsApp com IA para assessoria de investimentos.
// Recebe mensagens pela API oficial da Meta e responde usando o Claude.
import express from "express";
import Anthropic from "@anthropic-ai/sdk";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { criarMemoria, criarDeduplicador } from "./lib/memoria.js";
import { criarWhatsApp, assinaturaValida, extrairMensagens } from "./lib/whatsapp.js";
import { criarIA, montarPromptSistema, lerContexto } from "./lib/ia.js";

const pasta = path.dirname(fileURLToPath(import.meta.url));

const env = process.env;
const obrigatorias = [
  "ANTHROPIC_API_KEY",
  "WHATSAPP_TOKEN",
  "WHATSAPP_PHONE_NUMBER_ID",
  "WHATSAPP_VERIFY_TOKEN",
  "WHATSAPP_APP_SECRET",
];
const faltando = obrigatorias.filter((v) => !env[v]);
if (faltando.length) {
  console.error(`Faltam variáveis de ambiente: ${faltando.join(", ")}. Veja o .env.example.`);
  process.exit(1);
}

const ASSESSOR = env.ASSESSOR_NOME || "seu assessor";
const caminhoContexto = path.join(pasta, "contexto.md");

const whatsapp = criarWhatsApp({
  token: env.WHATSAPP_TOKEN,
  phoneNumberId: env.WHATSAPP_PHONE_NUMBER_ID,
  versao: env.GRAPH_API_VERSION || "v21.0",
});
const ia = criarIA({
  apiKey: env.ANTHROPIC_API_KEY,
  promptSistema: () =>
    montarPromptSistema({
      assessorNome: ASSESSOR,
      empresa: env.EMPRESA_NOME,
      botNome: env.BOT_NOME || "Assistente",
      contexto: lerContexto(caminhoContexto),
    }),
});
const memoria = criarMemoria();
const jaVisto = criarDeduplicador();

// Fila por cliente: se ele mandar várias mensagens seguidas, respondemos em ordem.
const filas = new Map();
function enfileirar(numero, tarefa) {
  const anterior = filas.get(numero) ?? Promise.resolve();
  const atual = anterior.then(tarefa).catch((e) => console.error(e));
  filas.set(numero, atual);
  atual.finally(() => {
    if (filas.get(numero) === atual) filas.delete(numero);
  });
}

async function atender(msg) {
  if (msg.tipo !== "text" && msg.tipo !== "button") {
    await whatsapp.enviarTexto(
      msg.de,
      "Por enquanto só consigo ler mensagens de texto 🙂 Pode escrever sua dúvida?",
    );
    return;
  }

  if (msg.texto.trim().toLowerCase() === "/reiniciar") {
    memoria.limpar(msg.de);
    await whatsapp.enviarTexto(msg.de, "Conversa reiniciada. Como posso ajudar?");
    return;
  }

  await whatsapp.marcarLidaEDigitando(msg.id);
  memoria.adicionar(msg.de, "user", msg.texto);

  let resposta;
  try {
    resposta = await ia.responder(memoria.historico(msg.de));
  } catch (err) {
    if (err instanceof Anthropic.RateLimitError) console.error("IA: limite de uso atingido", err.message);
    else if (err instanceof Anthropic.AuthenticationError) console.error("IA: API key inválida");
    else if (err instanceof Anthropic.APIError) console.error(`IA: erro ${err.status}`, err.message);
    else console.error("IA: erro inesperado", err);
  }

  if (!resposta) {
    resposta = `Desculpe, não consegui responder agora. Vou avisar ${ASSESSOR} para falar com você em breve.`;
  } else {
    memoria.adicionar(msg.de, "assistant", resposta);
  }
  await whatsapp.enviarTexto(msg.de, resposta);
  console.log(`Respondi ${mascarar(msg.de)} (${resposta.length} caracteres)`);
}

function mascarar(numero) {
  return numero ? `***${numero.slice(-4)}` : "?";
}

const app = express();
// Guarda o corpo bruto para conferir a assinatura da Meta.
app.use(express.json({ verify: (req, _res, buf) => (req.corpoBruto = buf) }));

app.get("/", (_req, res) => res.send("Bot de WhatsApp no ar ✅"));

// Passo de verificação feito pela Meta ao cadastrar o webhook.
app.get("/webhook", (req, res) => {
  const { "hub.mode": modo, "hub.verify_token": token, "hub.challenge": desafio } = req.query;
  if (modo === "subscribe" && token === env.WHATSAPP_VERIFY_TOKEN) {
    console.log("Webhook verificado pela Meta");
    return res.status(200).send(desafio);
  }
  res.sendStatus(403);
});

// Mensagens chegando.
app.post("/webhook", (req, res) => {
  if (!assinaturaValida(req.corpoBruto ?? Buffer.alloc(0), req.get("x-hub-signature-256"), env.WHATSAPP_APP_SECRET)) {
    return res.sendStatus(401);
  }
  // Responde 200 na hora; a Meta reenvia se demorarmos.
  res.sendStatus(200);

  for (const msg of extrairMensagens(req.body)) {
    if (jaVisto(msg.id)) continue;
    console.log(`Mensagem de ${mascarar(msg.de)} (${msg.tipo})`);
    enfileirar(msg.de, () => atender(msg));
  }
});

const porta = Number(env.PORT) || 3000;
app.listen(porta, () => console.log(`Bot rodando na porta ${porta}`));
