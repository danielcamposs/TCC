# Estudo 2 — Resultados consolidados (comparação cega)

Fonte: planilhas de respostas dos formulários [AV01], [AV02] e [AV03] (lidas em 16/11/2026).
Mapa de rótulos (informado por Daniel): **A = UStory.IA**, **B = Humano (alunos)**, **C = Prompt simples**.
Projeto avaliado: P06. Escala Likert 1–5. Cada formulário foi respondido por 2 avaliadores (o código digitado é o do formulário, igual para os dois; aqui eles foram renumerados AV01 a AV06 na ordem de envio, como na tabela de distribuição da Metodologia: form. 1 → AV01 e AV02, form. 2 → AV03 e AV04, form. 3 → AV05 e AV06).

| Formulário | Par comparado | Avaliadores |
|---|---|---|
| Form. 1 | Humano (B) × Prompt simples (C) | AV01, AV02 |
| Form. 2 | UStory.IA (A) × Prompt simples (C) | AV03, AV04 |
| Form. 3 | UStory.IA (A) × Humano (B) | AV05, AV06 |

Itens: 1 formato e clareza; 2 atomicidade/independência; 3 valor e testabilidade; 4 critérios de aceitação; 5 fidelidade ao documento de visão; 6 cobertura; 7 qualidade geral.

## 1. Perfil dos avaliadores (n = 6)

| Avaliador | Ocupação | Experiência em ER | Experiência com HU | Uso de IA generativa | Tempo |
|---|---|---|---|---|---|
| AV01 | Profissional de TI | Prática em projetos acadêmicos | Escreveu em projetos acadêmicos | Frequentemente | < 20 min |
| AV02 | Graduando(a) | Prática profissional até 2 anos | Escreveu em projetos profissionais | Frequentemente | 20–40 min |
| AV03 | Graduado(a) | Prática profissional > 2 anos | Escreveu em projetos profissionais | Às vezes | < 20 min |
| AV04 | Profissional de TI | Prática profissional até 2 anos | Escreveu em projetos profissionais | Frequentemente | 20–40 min |
| AV05 | Graduando(a) | Cursou a disciplina | Escreveu em projetos acadêmicos | Raramente | 20–40 min |
| AV06 | Graduando(a) | Prática em projetos acadêmicos | Já leu ou estudou | Frequentemente | 20–40 min |

Todos aceitaram o TCLE, declararam ter 18 anos ou mais, autorizaram a publicação anonimizada e declararam não ter participado da autoria do projeto.

## 2. Respostas por par (itens 1–7, ranking e palpite de origem)

### Par 1 — Humano × ChatGPT (formulário 1)

| Avaliador | Conjunto | I1 | I2 | I3 | I4 | I5 | I6 | I7 | Média | Ranking | Palpite de origem |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AV01 | Humano (B) | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5,00 | 1º | UStory.IA ✗ |
| AV01 | Prompt simples (C) | 5 | 3 | 4 | 4 | 4 | 4 | 3 | 3,86 | 2º | Estudantes ✗ |
| AV02 | Humano (B) | 5 | 3 | 4 | 4 | 4 | 5 | 4 | 4,14 | 1º | Não sei |
| AV02 | Prompt simples (C) | 4 | 3 | 4 | 3 | 4 | 4 | 4 | 3,71 | 2º | UStory.IA ✗ |

### Par 2 — UStory.IA × ChatGPT (formulário 2)

| Avaliador | Conjunto | I1 | I2 | I3 | I4 | I5 | I6 | I7 | Média | Ranking | Palpite de origem |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AV03 | UStory.IA (A) | 4 | 5 | 5 | 4 | 5 | 4 | 4 | 4,43 | 1º | IA simples + UStory.IA (marcou dois) |
| AV03 | Prompt simples (C) | 4 | 4 | 2 | 1 | 2 | 2 | 1 | 2,29 | 2º | Estudantes ✗ |
| AV04 | UStory.IA (A) | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5,00 | 1º | UStory.IA ✓ |
| AV04 | Prompt simples (C) | 5 | 5 | 5 | 4 | 4 | 4 | 4 | 4,43 | 2º | IA simples ✓ |

### Par 3 — UStory.IA × Humano (formulário 3)

| Avaliador | Conjunto | I1 | I2 | I3 | I4 | I5 | I6 | I7 | Média | Ranking | Palpite de origem |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AV05 | UStory.IA (A) | 5 | 5 | 4 | 5 | 4 | 5 | 5 | 4,71 | 2º | Estudantes ✗ |
| AV05 | Humano (B) | 5 | 5 | 4 | 4 | 4 | 5 | 5 | 4,57 | 1º | Estudantes ✓ |
| AV06 | UStory.IA (A) | 5 | 5 | 5 | N/A* | 5 | 5 | 5 | 5,00 | 1º | Marcou as três opções |
| AV06 | Humano (B) | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5,00 | 2º | Estudantes + IA simples (marcou dois) |

\* AV06 marcou "Este conjunto não traz critérios de aceitação" para o Conjunto A, mas o conjunto apresentava dois critérios por história; a resposta foi tratada como dado ausente.

Observação: em AV05 o UStory.IA teve média maior (4,71 × 4,57), mas o avaliador colocou o Humano em 1º no ranking.

## 3. Médias por abordagem (cada abordagem recebeu 4 avaliações)

| Item | UStory.IA | Humano | ChatGPT |
|---|---|---|---|
| 1 Formato e clareza | 4,75 | 5,00 | 4,50 |
| 2 Atomicidade e independência | 5,00 | 4,50 | 3,75 |
| 3 Valor e testabilidade | 4,75 | 4,50 | 3,75 |
| 4 Critérios de aceitação | 4,67 (n=3) | 4,50 | 3,00 |
| 5 Fidelidade ao documento | 4,75 | 4,50 | 3,50 |
| 6 Cobertura | 4,75 | 5,00 | 3,50 |
| 7 Qualidade geral | 4,75 | 4,75 | 3,00 |
| **Média geral (itens 1–7)** | **4,78** | **4,68** | **3,57** |
| Mediana geral | 5 | 5 | 4 |

## 4. Preferência (item 8)

| Par | Preferido | Resultado |
|---|---|---|
| Humano × ChatGPT | Humano | 2 de 2 |
| UStory.IA × ChatGPT | UStory.IA | 2 de 2 |
| UStory.IA × Humano | Empate | 1 × 1 |

No total, o UStory.IA ficou em 1º em 3 das 4 comparações de que participou, o Humano em 3 de 4 e o ChatGPT em 0 de 4.

## 5. Identificação da origem (item 9)

Foram 12 palpites (6 avaliadores × 2 conjuntos). Em 3 o avaliador marcou mais de uma origem e em 1 marcou "Não sei". Dos 8 palpites com uma única origem, 3 acertaram (37,5%), perto do acaso de 1/3. Os acertos foram: UStory.IA e ChatGPT por AV04, e Humano por AV05. O conjunto Humano foi tomado por UStory.IA uma vez, o ChatGPT foi tomado por estudantes duas vezes e por UStory.IA uma vez. Isso indica que o cegamento funcionou.

## 6. Comentários abertos

- **AV03 (item 10):** "Apesar do documento feito com IA (na minha visão), achei alguns poucos critérios não tão detalhados e com margem para interpretação errada para desenvolvimento. Poderia ser um pouco mais específico em certos detalhes para garantir o correto desenvolvimento e entrega. Acredito que pelo não detalhamento de certos critérios de aceitação, isso poderia gerar pequenos ruídos na validação." (O formulário tem um campo único por projeto, então o comentário não diz a qual conjunto se refere. Pelas notas, parece ser o Conjunto C, o do ChatGPT, que recebeu 1 no item 4.)
- **AV03 (F2):** dificuldade para rolar o documento no celular (Google Docs).
- **AV02 (F2):** "Só a questão do formulário errado na primeira vez, nada de mais."

## 7. Leitura descritiva (n = 6)

- O UStory.IA e o Humano ficaram próximos (4,78 × 4,68), e ambos bem acima do ChatGPT com prompt simples (3,57).
- A maior distância para o ChatGPT apareceu nos critérios de aceitação (item 4) e na qualidade geral (item 7), ambos com média 3,00, seguidos de fidelidade e cobertura (3,50).
- O UStory.IA superou o Humano em atomicidade (5,00 × 4,50), testabilidade, critérios de aceitação e fidelidade. O Humano superou o UStory.IA em formato e clareza e em cobertura (5,00 × 4,75).
- No ranking direto, o ChatGPT perdeu todas as comparações. UStory.IA × Humano terminou empatado.
- Cautelas: n = 6, um único projeto e só 2 avaliações por par, então os números descrevem esta amostra e não permitem inferência. AV03 puxou a média do ChatGPT para baixo (2,29). Sem esse avaliador, a média do ChatGPT seria 4,00.
