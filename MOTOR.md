# Motor de estudo e readequação de carteiras

Gera, a partir da posição de um cliente, os documentos da assessoria em PDF e página web, mais um texto curto para WhatsApp ou e-mail:

| Comando | Documento | Entrada |
|---|---|---|
| `readequacao` | Readequação da carteira: fundos que saem, revisão de crédito, enquadramento, antes e depois, estratégia | posição do cliente (`exemplos/carteira_exemplo.yaml`) |
| `enquadramento` | Só a verificação dos limites de compliance, no terminal | posição do cliente |
| `comparativo` | Estudo comparativo: carteira de fundos proposta × fundo atual, últimos 12 meses | `exemplos/comparativo_previdencia.yaml` |
| `proposta` | Proposta de carteira nova com projeção líquida por cenário de CDI | `exemplos/proposta_renda_fixa.yaml` |
| `fundo` | Consulta rápida de um fundo (nome ou CNPJ): cadastro e 12 meses | texto |

```bash
python3 -m motor readequacao clientes/joao.yaml
python3 -m motor enquadramento clientes/joao.yaml
python3 -m motor comparativo exemplos/comparativo_previdencia.yaml
python3 -m motor proposta exemplos/proposta_renda_fixa.yaml
python3 -m motor fundo "arx everest"
```

Os arquivos saem em `saidas/<data>-<tipo>-<nome>/` (HTML, PDF e `mensagem.txt`). Use `--sem-pdf` para gerar só o HTML.

## Regras da casa: `regras.yaml`

Tudo o que é decisão da assessoria fica neste arquivo. Mudou a regra, vale para todas as próximas carteiras:

- **compliance**: crédito privado até 5% por emissor, até 15% por nicho (setor do devedor) e fundos fechados até 10% cada, sobre o patrimônio total. Títulos públicos, bancários com FGC (até R$ 250 mil por banco), LCD BNDES e fundos abertos ficam fora do limite por emissor. Estouros geram sugestão de venda do excesso, exceto em ativos sem liquidez. COE é ignorado.
- **destino_padrao**: fundo que recebe resgates e vendas (XP Referenciado DI).
- **fundos_substituir**: fundos que saem sempre, com o motivo que aparece no documento.
- **fundos_conhecidos**: reconhecimento de fundos pelo nome, quando a posição não traz CNPJ.
- **emissores**: setor e situação de cada emissor de crédito (`manter`, `monitorar`, `vender`, `sem_liquidez`), com a nota que aparece no documento.
- **textos**: frases-padrão (exposição global, título sem liquidez, etapa 3, aviso legal).

Emissor que não está na lista aparece como "Classificar" no documento e gera um aviso no terminal.

## Fontes de dados

- **CVM**: cotas diárias (Informe Diário) e cadastro de fundos, em `dados.cvm.gov.br`.
- **Banco Central**: CDI diário (SGS 12), Selic meta (SGS 432) e IPCA (SGS 433).

Os dados ficam em cache em `.cache/`. O primeiro uso baixa cerca de 13 meses de cotas da CVM (alguns minutos); depois, cada documento sai em segundos. O ambiente precisa de acesso a `dados.cvm.gov.br` e `api.bcb.gov.br`.

## Privacidade

Posições de clientes ficam em `clientes/` e os documentos em `saidas/`. As duas pastas estão no `.gitignore` e não vão para o GitHub. Os documentos não trazem nome nem código de cliente.

## Requisitos

Python 3.11+ com `pandas`, `pyyaml` e `jinja2`. Para o PDF: Node com Playwright e Chromium.
