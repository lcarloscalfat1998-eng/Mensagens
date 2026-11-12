// Comunicação com a WhatsApp Business Cloud API (oficial da Meta).
import crypto from "node:crypto";

const LIMITE_WHATSAPP = 4096; // tamanho máximo de uma mensagem de texto

export function criarWhatsApp({ token, phoneNumberId, versao = "v21.0" }) {
  const url = `https://graph.facebook.com/${versao}/${phoneNumberId}/messages`;

  async function chamar(corpo) {
    const resp = await fetch(url, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ messaging_product: "whatsapp", ...corpo }),
    });
    if (!resp.ok) {
      throw new Error(`WhatsApp API ${resp.status}: ${await resp.text()}`);
    }
    return resp.json();
  }

  async function enviarTexto(para, texto) {
    for (const parte of dividirTexto(texto)) {
      await chamar({ to: para, type: "text", text: { body: parte, preview_url: false } });
    }
  }

  // Marca como lida (dois tiques azuis) e mostra "digitando..." enquanto a IA pensa.
  async function marcarLidaEDigitando(messageId) {
    try {
      await chamar({
        status: "read",
        message_id: messageId,
        typing_indicator: { type: "text" },
      });
    } catch (err) {
      console.warn("Não consegui marcar como lida:", err.message);
    }
  }

  return { enviarTexto, marcarLidaEDigitando };
}

export function dividirTexto(texto, limite = LIMITE_WHATSAPP) {
  const partes = [];
  let resto = texto.trim();
  while (resto.length > limite) {
    let corte = resto.lastIndexOf("\n", limite);
    if (corte < limite / 2) corte = resto.lastIndexOf(" ", limite);
    if (corte < limite / 2) corte = limite;
    partes.push(resto.slice(0, corte).trim());
    resto = resto.slice(corte).trim();
  }
  if (resto) partes.push(resto);
  return partes;
}

// Confere se a requisição veio mesmo da Meta (assinatura X-Hub-Signature-256).
export function assinaturaValida(corpoBruto, assinatura, appSecret) {
  if (!assinatura || !assinatura.startsWith("sha256=")) return false;
  const esperado = crypto.createHmac("sha256", appSecret).update(corpoBruto).digest("hex");
  const recebido = assinatura.slice("sha256=".length);
  if (recebido.length !== esperado.length) return false;
  return crypto.timingSafeEqual(Buffer.from(recebido), Buffer.from(esperado));
}

// Extrai as mensagens recebidas do formato do webhook da Meta.
export function extrairMensagens(payload) {
  const resultado = [];
  for (const entry of payload?.entry ?? []) {
    for (const change of entry.changes ?? []) {
      const valor = change.value ?? {};
      const nomes = Object.fromEntries(
        (valor.contacts ?? []).map((c) => [c.wa_id, c.profile?.name]),
      );
      for (const m of valor.messages ?? []) {
        resultado.push({
          id: m.id,
          de: m.from,
          nome: nomes[m.from],
          tipo: m.type,
          texto: m.type === "text" ? m.text?.body : m.type === "button" ? m.button?.text : null,
        });
      }
    }
  }
  return resultado;
}
