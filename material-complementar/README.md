# Material complementar — Avaliação da UStory.IA

Este diretório reúne o pacote dos dois estudos de avaliação descritos no TCC *UStory.IA*. Todo o material está anonimizado: não há nomes, e-mails ou outros dados que identifiquem participantes, avaliadores ou os autores do projeto usado como objeto do Estudo 2.

## Estudo 1 — Aceitação (TAM)

- Formulário: [Formulário TAM](https://docs.google.com/forms/d/e/1FAIpQLScXBCVIn4Big93odLjCgknyBbtWauECcO7YUaDN5qUJjeLbfw/viewform?usp=header)
- [`estudo1/respostas_estudo1_anonimizadas.csv`](estudo1/respostas_estudo1_anonimizadas.csv): as 14 respostas (01 a 11/11/2026). Foram removidos o carimbo de data e hora e o e-mail deixado pelos interessados na segunda etapa; cada participante é identificado por um código (P01 a P14). Escala de 4 pontos, sem opção neutra.

## Estudo 2 — Comparação cega da qualidade das histórias

Projeto avaliado: sistema de agendamento e prontuário para um médico veterinário autônomo (P06), cujo documento de visão foi elaborado por estudantes na disciplina de Engenharia de Software e anonimizado com a autorização individual dos autores.

Rótulos dos conjuntos (fixos para cada origem):

| Rótulo | Origem |
|---|---|
| A | UStory.IA (`gpt-4o-mini`, temperatura 0) |
| B | Humano (histórias escritas pelos estudantes) |
| C | *Prompt* simples (mesmo modelo, temperatura 0) |

Distribuição dos formulários (dois avaliadores por formulário):

| Formulário | Conjuntos | Documento enviado aos avaliadores |
|---|---|---|
| [AV01](https://docs.google.com/forms/d/e/1FAIpQLSf7FoJTXSSaTAOscF2CkjC3gKCVk3zcMCefOChmH-5dUvnNqA/viewform?usp=header) | B e C | [`estudo2/AV01_documento_de_visao_conjuntos_B_C.md`](estudo2/AV01_documento_de_visao_conjuntos_B_C.md) |
| [AV02](https://docs.google.com/forms/d/e/1FAIpQLScchIEDPf2GSF4kOMiPjVfRwy3Oo9r1nFcP1rvbzlGfDJaQYw/viewform?usp=header) | A e C | [`estudo2/AV02_documento_de_visao_conjuntos_A_C.md`](estudo2/AV02_documento_de_visao_conjuntos_A_C.md) |
| [AV03](https://docs.google.com/forms/d/e/1FAIpQLScpZX8XHrI2ALrBkGtp7rwfheezWrXC_kqEyjfHz8F--hHWiQ/viewform?usp=header) | A e B | [`estudo2/AV03_documento_de_visao_conjuntos_A_B.md`](estudo2/AV03_documento_de_visao_conjuntos_A_B.md) |

Cada documento traz o documento de visão anonimizado (entrada do estudo) seguido dos dois conjuntos de histórias avaliados naquele formulário.

*Prompt* usado no conjunto C, em uma sessão nova e sem histórico, com o documento de visão anexado:

> Nesse chat você deve atuar como um analista de requisitos. A partir do documento de visão do projeto de software em anexo, escreva 8 histórias de usuário incluindo critérios de aceitação. Responda apenas com a lista de histórias e critérios, sem títulos, comentários ou explicações.

- [`estudo2/resultados_estudo2_anonimizados.md`](estudo2/resultados_estudo2_anonimizados.md): perfil dos avaliadores (AV01 a AV06), notas por item, ranking, palpites de origem, médias e comentários.
