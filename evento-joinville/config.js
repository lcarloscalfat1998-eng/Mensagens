// =====================================================================
//  CONFIGURAÇÃO DO EVENTO — edite aqui e rode:  node render.js
//  Tudo que está entre [colchetes] é placeholder para você preencher.
// =====================================================================
window.EVENTO = {
  serie: "Do Mundo à Mesa",                 // nome da série / storytelling
  // LOGO: salve o arquivo oficial (PNG/SVG com fundo transparente, versão branca
  // ou preta) nesta pasta e informe o nome, ex.: "logo-xp.png".
  // Vazio = selo tipográfico provisório "xp | <marca>".
  logo: "",
  marca: "Investimentos",                   // texto ao lado do selo provisório
  disclaimer: "Conteúdo informativo e educacional; não constitui recomendação de investimento, jurídica ou tributária. [Nome do escritório] é empresa de assessoria de investimento registrada na CVM, que atua como preposta da XP Investimentos CCTVM S.A.",
  data: "2026-12-03",
  dataExtenso: "03 de dezembro · quinta-feira",
  horario: "20h",
  cidade: "Joinville · SC",
  local: "Santa Mistura",
  endereco: "R. Otto Boehm, 722 · América",
  traje: "Esporte fino",
  vagas: 5,

  // Pessoas que estarão à mesa (anfitriões + especialistas que você vai levar).
  // foto: caminho opcional, ex. "fotos/carlos.jpg" (quadrada). Sem foto = iniciais.
  pessoas: [
    { nome: "Luiz Calfat", papel: "Anfitrião", cargo: "Banker · XP Investimentos",
      bio: "Advogado formado pelo Mackenzie, com 5 anos de carreira em M&A. Há 3 anos é banker na XP Investimentos, cuidando do patrimônio de famílias e empresários.",
      foto: "fotos/luiz-calfat.jpg" },
    { nome: "[Nome do Cliente]",     papel: "Anfitrião",         cargo: "[Cargo / empresa]",          bio: "[1 linha sobre o cliente que apresenta os convidados]", foto: "" },
    { nome: "André Torres", papel: "Cenários & Alocação", cargo: "Economista · XP Investimentos · CNPI e CGA",
      bio: "Economista pelo Insper, com mais de 11 anos de mercado. Passou pelas tesourarias do Haitong e do Scotiabank, pela Estratégia de Alocação em Renda Fixa do Bradesco Private Bank e estruturou o Research de Renda Fixa da Genial. Há mais de 3 anos na XP, desenha estratégias de alocação para investidores de alta renda.",
      foto: "fotos/especialista-cenarios.jpg" },
    { nome: "Isabella Magalhães", papel: "Wealth Planning", cargo: "Advogada · Patrimonial e Sucessório · CFP e CGA",
      bio: "Especializada em gestão de patrimônio e estruturas de investimento no Brasil e no exterior, com foco em famílias UHNW. Mestre (LL.M.) em Direito dos Mercados Financeiro e de Capitais pelo Insper e pós-graduada em Planejamento Patrimonial e Sucessório pela FGV. Atua com fundos exclusivos, offshores e trusts em múltiplas jurisdições.",
      foto: "fotos/especialista-wealth.jpg" },
  ],
};
