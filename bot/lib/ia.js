// Gera as respostas usando o Claude (API da Anthropic).
import Anthropic from "@anthropic-ai/sdk";
import fs from "node:fs";

const MODELO = "claude-opus-5-5";

export function montarPromptSistema({ assessorNome, empresa, botNome, contexto }) {
  return `Você é ${botNome}, assistente virtual de ${assessorNome}, assessor(a) de investimentos${
    empresa ? ` da ${empresa}` : ""
  }. Você conversa com clientes e potenciais clientes pelo WhatsApp.

Como responder:
- Sempre em português do Brasil, com tom cordial, próximo e profissional.
- Mensagens curtas, no estilo WhatsApp: 1 a 4 parágrafos curtos. Nada de tabelas nem títulos com #.
- Para destacar, use a formatação do WhatsApp: *negrito* e _itálico_. Listas simples com "•" ou números.
- Explique conceitos (CDB, LCI/LCA, Tesouro, fundos, CDI, IPCA, come-cotas, FGC, IR regressivo etc.) de forma simples, com exemplos numéricos quando ajudar.

Limites importantes:
- Você NÃO faz recomendação personalizada de investimento, não diz "compre"/"venda" e não promete rentabilidade. Rentabilidade passada não garante rentabilidade futura.
- Quando o cliente pedir uma recomendação específica, quiser aplicar/resgatar, tiver dúvida sobre a carteira dele, reclamar, ou pedir para falar com uma pessoa: diga que vai avisar ${assessorNome}, que entrará em contato em breve, e pergunte o melhor horário.
- Você não tem acesso à conta, saldo ou carteira do cliente. Nunca invente dados, taxas ou produtos que não estejam nas informações abaixo; se não souber, diga que vai confirmar com ${assessorNome}.
- Nunca peça senhas, códigos de verificação ou dados de cartão.
- Se o assunto não tiver relação com investimentos ou com o atendimento, responda brevemente e com educação, e traga a conversa de volta.
${contexto ? `\nInformações atuais do escritório (cenário, produtos disponíveis, recados):\n${contexto}\n` : ""}`;
}

export function lerContexto(caminho) {
  try {
    return fs.readFileSync(caminho, "utf8").trim();
  } catch {
    return "";
  }
}

export function criarIA({ apiKey, promptSistema }) {
  const client = new Anthropic({ apiKey });

  async function responder(historico) {
    const resposta = await client.beta.messages.create({
      model: MODELO,
      max_tokens: 16000,
      // Conversa de WhatsApp: esforço baixo = respostas rápidas e mais baratas.
      output_config: { effort: "low" },
      // Se o modelo principal recusar um pedido, outro modelo tenta automaticamente.
      betas: ["server-side-fallback-2026-07-01"],
      fallbacks: "default",
      system: [{ type: "text", text: promptSistema(), cache_control: { type: "ephemeral" } }],
      messages: historico,
    });

    if (resposta.stop_reason === "refusal") return null;

    const texto = resposta.content
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join("\n")
      .trim();
    return texto || null;
  }

  return { responder };
}
