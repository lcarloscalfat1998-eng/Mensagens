---
name: estudo-carteira
description: Gera estudo, readequação ou proposta de carteira de cliente da assessoria (PDF + página + mensagem de WhatsApp) com o motor deste repositório. Use quando o assessor mandar uma posição consolidada (Excel, prints ou lista), pedir readequação, enquadramento/compliance, comparativo de fundos ou proposta de carteira.
---

# Estudo de carteira

O motor está em `motor/` e as regras da casa em `regras.yaml`. A documentação completa está em `MOTOR.md`.

## Fluxo

1. **Entrada.** Monte o arquivo da carteira em `clientes/<apelido>.yaml`, no formato de `exemplos/carteira_exemplo.yaml`. Fontes possíveis:
   - Excel da posição consolidada da XP ("Baixar Excel").
   - Prints da tela: transcreva nome, aplicado, posição e valor líquido de cada linha, e confira as somas por bloco com os totais da tela.

   Nunca grave dados de cliente fora de `clientes/` ou `saidas/`. Nunca coloque nome ou código de cliente no documento.
2. **Enquadramento.** Rode `python3 -m motor enquadramento clientes/<apelido>.yaml`.
   - Mostre ao assessor os estouros e os avisos.
   - Emissores fora de `regras.yaml` precisam de setor e situação. Pergunte ao assessor ou pesquise rating e alavancagem recentes, e proponha a inclusão em `regras.yaml`.
3. **Documento.** Rode o comando pedido:
   - `readequacao`: readequação e redução de risco.
   - `comparativo`: carteira de fundos proposta contra o fundo atual.
   - `proposta`: carteira nova com projeção.

   Antes de publicar, olhe o HTML em `saidas/...` uma vez.
4. **Ajustes do assessor.** Use o bloco `opcoes` da entrada para decisões só daquela carteira:
   - `manter`: ativos que não podem ser vendidos.
   - `vender`: ativos que devem sair mesmo sem regra.
   - `acao_estouro: alertar`: só sinaliza os estouros, sem sugerir venda.

   Mudanças que valem para todos os clientes vão em `regras.yaml`.
5. **Entrega.** Publique o HTML como artifact e envie o PDF. No chat, mostre o texto de `mensagem.txt`, que fica pronto para colar.

## Cuidados

- Os números vêm da CVM e do Banco Central. Não substitua por estimativas. Se um fundo não tiver cota na CVM (FIDC, FIP), o documento mostra "–".
- Fundo citado sem CNPJ: confirme com `python3 -m motor fundo "nome"` antes de usar.
- Texto de tese e projeção deve falar em "tende a" e "em tese", nunca prometer retorno.
