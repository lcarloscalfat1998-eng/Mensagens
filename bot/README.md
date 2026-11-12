# Chatbot de WhatsApp com IA

Este bot responde automaticamente os clientes no WhatsApp. Ele usa a **API oficial da Meta** para receber e enviar mensagens e o **Claude** (IA da Anthropic) para escrever as respostas.

**O que ele faz**
- Tira dúvidas sobre investimentos (CDB, LCI/LCA, Tesouro, fundos, IR, FGC…) em linguagem simples.
- Lembra da conversa de cada cliente (últimas 20 mensagens, por até 24h).
- **Não** faz recomendação personalizada nem promete rentabilidade. Se o cliente quiser aplicar, resgatar, falar da carteira dele ou falar com uma pessoa, o bot diz que vai avisar você.
- Usa as informações do arquivo [`contexto.md`](contexto.md), que você edita com o cenário, os produtos da semana e o horário de atendimento.
- Se o cliente escrever `/reiniciar`, a conversa começa do zero.

---

## Passo a passo

### 1. Chave da IA (Anthropic)
1. Entre em **console.anthropic.com** e crie uma conta.
2. Em **Billing**, coloque créditos (o uso é cobrado por mensagem; uma conversa curta custa centavos).
3. Em **API Keys**, clique em **Create Key** e guarde a chave (`sk-ant-...`).

### 2. App na Meta (WhatsApp Cloud API)
1. Entre em **developers.facebook.com**, clique em **Meus apps → Criar app → Outro → Empresa**.
2. No painel do app, adicione o produto **WhatsApp**.
3. Em **WhatsApp → Configuração da API**:
   - Anote o **Phone number ID** (identificação do número de telefone).
   - Para testar, use o número de teste da Meta e cadastre o seu celular em "Para".
   - Para produção, clique em **Adicionar número de telefone**. Use um número que **não** esteja ativo no app do WhatsApp.
4. **Token permanente** (o token temporário dura só 24h):
   - Abra **business.facebook.com → Configurações → Usuários do sistema**.
   - Crie um usuário do sistema do tipo Admin.
   - Clique em **Gerar token**, escolha o app e marque `whatsapp_business_messaging` e `whatsapp_business_management`.
5. Em **Configurações do app → Básico**, copie a **Chave secreta do app** (App Secret).

### 3. Publicar o bot no Render (grátis)
1. Crie uma conta em **render.com** entrando com o GitHub.
2. Clique em **New → Blueprint** e escolha o repositório **Mensagens**. O arquivo `render.yaml` já configura tudo.
3. Preencha as variáveis quando o Render pedir:

| Variável | O que é |
|---|---|
| `ANTHROPIC_API_KEY` | Chave do passo 1 |
| `WHATSAPP_TOKEN` | Token permanente do passo 2.4 |
| `WHATSAPP_PHONE_NUMBER_ID` | Phone number ID do passo 2.3 |
| `WHATSAPP_APP_SECRET` | Chave secreta do app do passo 2.5 |
| `WHATSAPP_VERIFY_TOKEN` | Uma senha que **você inventa**, por exemplo `minhasenha123` |
| `ASSESSOR_NOME` | Seu nome, como o bot vai te chamar |
| `EMPRESA_NOME` | Nome do escritório (opcional) |

4. Quando terminar, o Render mostra um endereço parecido com `https://whatsapp-bot-xxxx.onrender.com`. Abra no navegador: deve aparecer "Bot de WhatsApp no ar ✅".

> ⚠️ **Plano grátis do Render:** o servidor "dorme" depois de 15 minutos sem uso. A primeira mensagem depois disso pode demorar uns 50 segundos. Para atender clientes de verdade, use o plano pago mais barato (Starter), que fica sempre ligado.

### 4. Ligar o webhook (Meta → bot)
1. No app da Meta, abra **WhatsApp → Configuração → Webhook → Editar**.
2. Em **URL de retorno de chamada**, coloque `https://SEU-ENDERECO.onrender.com/webhook`.
3. Em **Token de verificação**, coloque a mesma senha de `WHATSAPP_VERIFY_TOKEN`.
4. Clique em **Verificar e salvar** e depois **assine** o campo **messages**.
5. Mande um "Oi" para o número do bot. Pronto! 🎉

---

## Personalizar
- **Informações que o bot usa:** edite `contexto.md` (cenário, produtos, horários) e faça commit. O Render atualiza sozinho.
- **Jeito de responder e regras:** estão em `lib/ia.js`, na função `montarPromptSistema`.

## Testar no computador (opcional)
```bash
cd bot
cp .env.example .env   # preencha os valores
npm install
npm run dev
npm test               # testes automáticos
```
Para a Meta conseguir chamar o seu computador, use um túnel como o `ngrok http 3000` e cadastre a URL dele no webhook.

## Limitações atuais
- Só lê mensagens de texto. Para áudio, foto ou documento, o bot pede que o cliente escreva.
- O histórico fica na memória do servidor e se perde quando ele reinicia.
- O bot **não** te avisa quando o cliente pede para falar com você, e você ainda não tem uma tela para ler as conversas: os registros (logs) do Render só mostram que houve uma mensagem. Essas duas funções podem ser adicionadas depois.
- A Meta só permite que o bot responda dentro de 24h desde a última mensagem do cliente. Mensagens iniciadas por você precisam de modelos (templates) aprovados.
