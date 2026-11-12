import { test } from "node:test";
import assert from "node:assert/strict";
import crypto from "node:crypto";
import { dividirTexto, assinaturaValida, extrairMensagens } from "../lib/whatsapp.js";
import { criarMemoria, criarDeduplicador } from "../lib/memoria.js";

test("divide textos longos em partes de até 4096 caracteres", () => {
  const texto = ("palavra ".repeat(1000)).trim();
  const partes = dividirTexto(texto);
  assert.ok(partes.length > 1);
  assert.ok(partes.every((p) => p.length <= 4096));
  assert.equal(partes.join(" "), texto);
});

test("confere a assinatura da Meta", () => {
  const corpo = Buffer.from('{"a":1}');
  const sig = "sha256=" + crypto.createHmac("sha256", "segredo").update(corpo).digest("hex");
  assert.equal(assinaturaValida(corpo, sig, "segredo"), true);
  assert.equal(assinaturaValida(corpo, sig, "outro"), false);
  assert.equal(assinaturaValida(corpo, undefined, "segredo"), false);
});

test("extrai mensagens do webhook", () => {
  const payload = {
    entry: [{ changes: [{ value: {
      contacts: [{ wa_id: "5511999990000", profile: { name: "Ana" } }],
      messages: [{ id: "m1", from: "5511999990000", type: "text", text: { body: "Oi" } }],
    } }] }],
  };
  assert.deepEqual(extrairMensagens(payload), [
    { id: "m1", de: "5511999990000", nome: "Ana", tipo: "text", texto: "Oi" },
  ]);
  assert.deepEqual(extrairMensagens({ entry: [{ changes: [{ value: { statuses: [{}] } }] }] }), []);
});

test("memória guarda histórico limitado começando pelo cliente", () => {
  const m = criarMemoria({ maxMensagens: 3 });
  m.adicionar("1", "user", "a");
  m.adicionar("1", "assistant", "b");
  m.adicionar("1", "user", "c");
  m.adicionar("1", "assistant", "d");
  const h = m.historico("1");
  assert.equal(h[0].role, "user");
  assert.ok(h.length <= 3);
  assert.deepEqual(m.historico("2"), []);
});

test("deduplicador ignora ids repetidos", () => {
  const jaVisto = criarDeduplicador();
  assert.equal(jaVisto("x"), false);
  assert.equal(jaVisto("x"), true);
});
