// Guarda o histórico recente de cada conversa em memória.
// Atenção: se o servidor reiniciar, o histórico é perdido (o bot continua
// funcionando, só "esquece" o que foi falado antes).

const MAX_MENSAGENS = 20; // últimas 20 mensagens (10 idas e voltas)
const EXPIRA_MS = 24 * 60 * 60 * 1000; // conversa parada há 24h recomeça do zero

export function criarMemoria({ maxMensagens = MAX_MENSAGENS, expiraMs = EXPIRA_MS } = {}) {
  const conversas = new Map();

  function historico(numero) {
    const c = conversas.get(numero);
    if (!c) return [];
    if (Date.now() - c.atualizadoEm > expiraMs) {
      conversas.delete(numero);
      return [];
    }
    return c.mensagens;
  }

  function adicionar(numero, role, content) {
    const mensagens = [...historico(numero), { role, content }];
    // Mantém só as mais recentes, sempre começando com uma mensagem do cliente.
    let inicio = Math.max(0, mensagens.length - maxMensagens);
    while (inicio < mensagens.length && mensagens[inicio].role !== "user") inicio++;
    conversas.set(numero, { mensagens: mensagens.slice(inicio), atualizadoEm: Date.now() });
  }

  function limpar(numero) {
    conversas.delete(numero);
  }

  return { historico, adicionar, limpar };
}

// Evita responder duas vezes a mesma mensagem (a Meta às vezes reenvia o webhook).
export function criarDeduplicador(limite = 1000) {
  const vistos = new Set();
  return function jaVisto(id) {
    if (vistos.has(id)) return true;
    vistos.add(id);
    if (vistos.size > limite) vistos.delete(vistos.values().next().value);
    return false;
  };
}
