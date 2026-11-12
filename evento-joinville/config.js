// =====================================================================
//  CONFIGURAÇÃO DO EVENTO — edite aqui e rode:  node render.js
// =====================================================================
window.EVENTO = {
  serie: "Do Mundo à Mesa",                 // nome da série / storytelling
  // LOGO: salve o arquivo oficial (PNG/SVG com fundo transparente, versão branca
  // ou preta) nesta pasta e informe o nome, ex.: "logo-xp.png".
  // Vazio = selo tipográfico provisório "xp | <marca>".
  logo: "",
  marca: "Investimentos",                   // texto ao lado do selo provisório
  disclaimer: "Conteúdo informativo e educacional; não constitui recomendação de investimento, jurídica ou tributária.",
  data: "2026-12-03",
  dataExtenso: "03 de dezembro · quinta-feira",
  horario: "20h",
  cidade: "Joinville · SC",
  local: "Santa Mistura",
  endereco: "R. Otto Boehm, 722 · América · Joinville",
  traje: "Esporte fino",
  vagas: 5,

  // Pessoas à mesa. titulo = rótulo principal; papel = tema que conduz; slug = nome do arquivo.
  pessoas: [
    { nome: "Luiz Calfat", titulo: "Anfitrião", papel: "Anfitrião", cargo: "Banker · XP Investimentos", slug: "luiz-calfat",
      bio: "Advogado formado pelo Mackenzie, com 5 anos de carreira em M&A. Há 3 anos é banker na XP Investimentos, cuidando do patrimônio de famílias e empresários.",
      foto: "fotos/luiz-calfat.jpg" },
    { nome: "Glaucio Gonçalves", titulo: "Anfitrião · Abertura", papel: "Anfitrião", cargo: "Diretor Comercial · Softdata Hub de Tecnologia", slug: "glaucio-goncalves",
      bio: "", foto: "fotos/glaucio-goncalves.jpg" },
    { nome: "André Torres", titulo: "Economista", papel: "Cenários & Alocação", cargo: "XP Investimentos · CNPI e CGA", slug: "economista-andre-torres",
      bio: "Formado pelo Insper, com mais de 11 anos de mercado. Passou pelas tesourarias do Haitong e do Scotiabank, pela Estratégia de Alocação em Renda Fixa do Bradesco Private Bank e estruturou o Research de Renda Fixa da Genial. Há mais de 3 anos na XP, desenha estratégias de alocação para investidores de alta renda.",
      foto: "fotos/andre-torres.jpg" },
    { nome: "Isabella Magalhães", titulo: "Advogada", papel: "Wealth Planning", cargo: "Patrimonial e Sucessório · CFP e CGA", slug: "advogada-isabella-magalhaes",
      bio: "Especializada em gestão de patrimônio e estruturas de investimento no Brasil e no exterior, com foco em famílias UHNW. Mestre (LL.M.) em Direito dos Mercados Financeiro e de Capitais pelo Insper e pós-graduada em Planejamento Patrimonial e Sucessório pela FGV. Atua com fundos exclusivos, offshores e trusts em múltiplas jurisdições.",
      foto: "fotos/isabella-magalhaes.jpg" },
  ],
};
