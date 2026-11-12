// =====================================================================
//  CONFIGURAÇÃO DO EVENTO — edite aqui e rode:  node render.js
//  Tudo que está entre [colchetes] é placeholder para você preencher.
// =====================================================================
window.EVENTO = {
  serie: "Do Mundo à Mesa",                 // nome da série / storytelling
  marca: "[Sua Empresa]",                   // aparece no rodapé de todas as peças
  data: "2026-12-03",
  dataExtenso: "03 de dezembro · quinta-feira",
  horario: "20h",
  cidade: "Joinville · SC",
  local: "[Nome do Restaurante]",
  endereco: "[Endereço completo]",
  traje: "Esporte fino",
  vagas: 5,

  // Pessoas que estarão à mesa (anfitriões + especialistas que você vai levar).
  // foto: caminho opcional, ex. "fotos/carlos.jpg" (quadrada). Sem foto = iniciais.
  pessoas: [
    { nome: "[Seu Nome]",            papel: "Anfitrião",         cargo: "[Seu cargo]",                bio: "[1 linha: experiência e foco de atuação]", foto: "" },
    { nome: "[Nome do Cliente]",     papel: "Anfitrião",         cargo: "[Cargo / empresa]",          bio: "[1 linha sobre o cliente que apresenta os convidados]", foto: "" },
    { nome: "[Especialista Macro]",  papel: "Cenários",          cargo: "[Economista / Estrategista]", bio: "[1 linha: formação, onde atua, diferencial]", foto: "" },
    { nome: "[Especialista Wealth]", papel: "Wealth Planning",   cargo: "[Planejador patrimonial]",   bio: "[1 linha: sucessão, tributário, offshore]", foto: "" },
  ],
};
