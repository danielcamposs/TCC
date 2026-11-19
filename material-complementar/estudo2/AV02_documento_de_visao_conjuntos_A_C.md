# **Documento de Visão**

**Projeto P06**

Domínio: Sistema de agendamento e prontuário para veterinário autônomo

*Parte A – Entrada do estudo. Contém problema, escopo, stakeholders e levantamento de requisitos. Material anonimizado e padronizado a partir de trabalho de graduação.*

# **1\. Entendimento do Problema e Definição de Escopo**

## **1.1 Problema**

O projeto visa resolver a sobrecarga de trabalho enfrentada por um médico veterinário autônomo que atua sem equipe de apoio administrativo. Atualmente, toda a gestão de seus atendimentos é realizada de forma manual através de seu celular pessoal. Essa centralização gera três problemas principais que afetam a qualidade do seu serviço e a sua qualidade de vida:

* Gargalo no Agendamento: Por atuar sozinho, ele não consegue responder mensagens de clientes enquanto está em consulta. A troca de mensagens para encontrar horários vagos é demorada, pois os clientes não possuem autonomia para visualizar a disponibilidade da agenda.

* Deficiência na Gestão de Prontuários: A dificuldade de redigir, organizar e consultar históricos clínicos completos e detalhados pelo celular compromete a agilidade do acompanhamento médico dos animais e aumenta o risco de perda de informações.

* Desorganização do Fluxo de Trabalho: O acúmulo de papéis de “atendente” e “médico” simultaneamente gera confusão na marcação de consultas, retornos e acompanhamento de exames.

## **1.2 Escopo: funcionalidades incluídas**

O que será incluído no sistema (Dentro do Escopo):

* Módulo de Agendamento Autônomo: Interface onde os clientes (tutores) podem visualizar a grade de horários disponíveis em tempo real e solicitar a marcação da consulta diretamente, sem intervenção prévia do veterinário.

* Módulo de Prontuário Eletrônico Simplificado: Interface otimizada para o veterinário registrar de forma rápida e segura o histórico clínico, exames, e observações de cada paciente, centralizando as informações de saúde.

* Cadastro de Clientes e Pacientes: Gerenciamento de perfis de Tutores e seus respectivos Pets.

* Painel do Veterinário: Visão centralizada da agenda do dia/semana para o controle de status das consultas.

* Notificações: Confirmações de agendamento para o tutor e alertas de nova consulta para o veterinário.

## **1.3 Escopo: funcionalidades não incluídas**

* Módulo de controle financeiro, meios de pagamento, faturamento ou emissão de notas fiscais.

* Módulo de controle de estoque de medicamentos (visto que o profissional atua de forma autônoma e não possui o inventário complexo de uma clínica física).

* Integração automatizada com laboratórios de exames.

* Sistema de chat ou comunicação direta entre tutor e veterinário dentro da plataforma.

## **1.4 Stakeholders**

* Médico Veterinário Autônomo: É o usuário primário e o principal beneficiado. Ele necessita de uma ferramenta ágil que atue como seu assistente administrativo, permitindo-lhe focar no atendimento clínico ao invés de se preocupar com a gestão manual de agendas e anotações avulsas no celular.

* Tutores dos Pets (Clientes): São os usuários secundários. Necessitam de praticidade, conveniência e autonomia para visualizar os horários e agendar consultas para seus animais a qualquer momento, sem depender de uma resposta manual do veterinário via aplicativo de mensagens.

## **1.5 Restrições e premissas**

*Não apresentado no documento original.*

# **2\. Levantamento dos Requisitos**

## **2.1 Técnicas utilizadas**

Para extrair o conhecimento explícito e tácito sobre o domínio do problema foi escolhida a técnica de Entrevista Semiestruturada para levantamento de requisitos, conduzida de forma online com o usuário primário do sistema, o veterinário. Esta abordagem direta foi fundamental para extrair conhecimentos práticos sobre a rotina do médico e identificar os gargalos causados pela falta de uma equipe de apoio administrativo.

A entrevista seguiu um roteiro pré-definido de 10 perguntas abertas, mas permitiu que o entrevistador explorasse tópicos que surgiram naturalmente durante a conversa. Essa flexibilidade foi essencial para captar necessidades que o stakeholder não havia verbalizado inicialmente.

## **2.2 Evidências, análise e resultados do levantamento**

### **Análise dos Requisitos Coletados**

Durante a transcrição e análise da entrevista, avaliamos as reais necessidades do stakeholder e filtramos o que seria implementável, com o objetivo de detectar omissões, resolver conflitos de interesses e garantir a viabilidade técnica do sistema.

* Resolução de Conflitos e Priorização: O cliente inicialmente manifestou o desejo de que o sistema se comunique automaticamente com laboratórios. Após negociação e avaliação de viabilidade, a equipe demonstrou que essa integração era complexa para o prazo do projeto. Chegou-se ao consenso de focar as funcionalidades estritamente nas dores mais críticas: a gestão de prontuários e o agendamento inteligente.

* Eliminação de Duplicações: Requisitos que se sobrepunham (como “ter uma agenda para o cliente” e “ter uma agenda para o veterinário”) foram combinados em um fluxo único de banco de dados, separando apenas a visão da interface de cada ator.

* Realizabilidade: O escopo final foi validado como 100% factível, pois trata-se de um sistema Web/Mobile focado no controle de fluxo de dados (operações de cadastro, leitura e atualização \- CRUD).

Identificamos que a prioridade máxima é otimizar o tempo e a organização clínica. Para resolver conflitos de escopo e garantir que o projeto seja completamente realizável neste primeiro ciclo, decidimos em conjunto com o cliente excluir do sistema o módulo de controle financeiro, faturamento e meios de pagamento. O foco será estritamente na resolução do agendamento autônomo e na gestão de prontuários.

### **Resultados Preliminares e Regras de Negócio Identificadas**

A partir da entrevista, além de confirmar as necessidades já esperadas, foram extraídas as seguintes informações e regras de negócio relevantes para a modelagem do sistema:

* O veterinário atende em diferentes locais (atendimento domiciliar).

* Cada consulta dura em média 2 horas, mas não existe um valor fixo. A duração varia conforme o caso clínico. Por isso, o sistema de agendamento não pode trabalhar com slots de tempo rígidos e deve permitir que o veterinário defina a duração estimada de cada consulta ou bloqueie faixas de horário flexíveis.

* Os tutores frequentemente tentam contato durante consultas, gerando acúmulo de mensagens não respondidas.

* O prontuário atual se resume a anotações soltas no celular, sem padronização e com risco real de perda por troca de aparelho ou exclusão acidental.

* Um mesmo tutor pode ter mais de um pet cadastrado, e cada pet deve ter seu próprio histórico clínico independente.

* O veterinário precisa conseguir bloquear horários na agenda para compromissos pessoais ou deslocamento.

### **Roteiro da Entrevista**

* 1\. Como é feito o seu processo de agendamento atualmente?

* 2\. Qual o número de consultas que você atende por dia em média?

* 3\. Como você armazena o histórico de saúde do pet atualmente?

* 4\. Quais são os maiores desafios de centralizar toda a gestão dos atendimentos no seu celular pessoal, especialmente quando você está no meio de uma consulta clínica?

* 5\. Quanto tempo e esforço é gasto, em média, trocando mensagens com tutores para tentar encontrar horários vagos?

* 6\. Como o acúmulo das funções de “médico” e “atendente” afeta a organização para marcar retornos e acompanhar os exames dos pacientes?

* 7\. Quais as maiores dificuldades na hora de redigir, consultar e organizar os prontuários eletrônicos pelo celular?

* 8\. Sobre a pergunta anterior, existe risco de perda dessas anotações atualmente?

* 9\. Como seria o cenário ideal se os clientes tivessem autonomia para ver a sua disponibilidade e marcar a consulta sem precisar te mandar mensagem?

* 10\. Para o cadastro do sistema, quais dados dos tutores e de seus respectivos pets são essenciais para a rotina (cadastro e prontuários)?

## **2.3 Relato de progresso e registro de interações**

Abaixo, apresentamos o registro da reunião realizada de forma online para o entendimento do problema e definição funcional do sistema.

Data e Duração: Dia 1 (aproximadamente 1 hora de duração).

Participantes: um integrante do grupo (atuando como Engenheiro de Requisitos/Entrevistador) e o médico veterinário autônomo (Stakeholder/Usuário Primário).

Plataforma de Reunião: Videoconferência via Google Meet (conforme registro fotográfico anexado no documento).

Principais Tópicos Discutidos:

* O impacto de atuar sozinho e o gargalo no agendamento via celular.

* A exaustão gerada pela necessidade de atuar simultaneamente como médico e recepcionista.

* A dificuldade de encontrar horários vagos e a falta de autonomia dos clientes.

* A falta de um histórico clínico seguro e rápido para o acompanhamento dos animais.

* Os desafios na redação e organização de prontuários eletrônicos em dispositivos móveis, visto que as anotações atuais se perdem no celular.

*Nota da padronização: A captura de tela da videoconferência foi removida na anonimização (mostrava rostos e nomes de participantes). Nome do entrevistado substituído por sua função; data absoluta substituída por posição relativa.*

## **2.4 Artefatos de apoio**

*Não apresentado no documento original.*

Como tutor do pet, quero visualizar os horários disponíveis e solicitar a marcação de consultas, para que eu possa agendar atendimentos de forma prática e rápida.

**Critérios de Aceitação:**

* O sistema deve exibir uma lista de horários disponíveis em tempo real, permitindo que o tutor selecione um horário para agendar a consulta.  
* O formulário de solicitação de agendamento deve incluir campos obrigatórios como nome do tutor, nome do pet, data e horário da consulta, e deve validar se todos os campos obrigatórios estão preenchidos antes de permitir o envio.

Como veterinário, quero registrar o histórico clínico dos pets de forma simplificada, para que eu possa acompanhar a saúde dos animais de maneira organizada.

**Critérios de Aceitação:**

* O sistema deve permitir o registro de informações como data da consulta, diagnóstico, tratamentos realizados e observações, com todos os campos sendo obrigatórios.  
* O veterinário deve ser capaz de visualizar o histórico clínico de cada pet em uma interface clara e acessível, com a opção de editar ou adicionar novas informações.

Como administrador do sistema, quero gerenciar os perfis de tutores e seus respectivos pets, para que eu possa manter um registro atualizado e organizado.

**Critérios de Aceitação:**

* O sistema deve ter um formulário de cadastro que inclua campos obrigatórios como nome do tutor, CPF, telefone e nome do pet, raça e idade.  
* O sistema deve validar os dados inseridos, garantindo que o CPF tenha o formato correto e que os campos obrigatórios não estejam vazios antes de permitir o cadastro.

Como veterinário, quero ter uma visão centralizada da minha agenda do dia/semana, para que eu possa gerenciar melhor meu tempo e as consultas agendadas.

**Critérios de Aceitação:**

* O painel deve exibir uma lista de consultas agendadas, incluindo informações como nome do tutor, nome do pet, data e horário da consulta, e status (confirmada, pendente, cancelada).  
* O veterinário deve poder filtrar a agenda por data e status das consultas, e o sistema deve atualizar automaticamente a lista ao adicionar ou cancelar consultas.

Como tutor do pet, quero receber notificações de confirmação de agendamento, para que eu tenha certeza de que a consulta foi marcada corretamente.

**Critérios de Aceitação:**

* O sistema deve enviar uma notificação por e-mail e/ou SMS ao tutor assim que a consulta for agendada, contendo detalhes como data, horário e nome do veterinário.  
* O tutor deve poder visualizar todas as notificações recebidas em uma tela dedicada, com a opção de marcar notificações como lidas ou não lidas.

Como veterinário, quero que o sistema se comunique automaticamente com laboratórios de exames, para que eu possa receber resultados de forma ágil e organizada.

**Critérios de Aceitação:**

* O sistema deve permitir o envio automático de solicitações de exames para laboratórios, incluindo informações do pet e do exame solicitado.  
* O veterinário deve receber notificações quando os resultados dos exames estiverem disponíveis, com um link direto para acessar os resultados no sistema.

Como tutor do pet, quero ter um sistema de chat para me comunicar diretamente com o veterinário, para que eu possa esclarecer dúvidas sobre a saúde do meu pet de forma rápida.

**Critérios de Aceitação:**

* O sistema deve permitir que tutores e veterinários enviem e recebam mensagens em tempo real, com notificações de novas mensagens.  
* O chat deve manter um histórico de conversas, permitindo que os usuários visualizem mensagens anteriores e busquem por palavras-chave.

Como usuário do sistema, quero realizar o login de forma segura, para que eu possa acessar minhas informações pessoais e do meu pet.

**Critérios de Aceitação:**

* O sistema deve exigir um nome de usuário e senha para autenticação, com validação de que ambos os campos não estão vazios.  
* O sistema deve permitir a recuperação de senha através de um e-mail cadastrado, enviando um link para redefinição de senha.

Como um tutor de pet, quero visualizar a agenda do veterinário em tempo real, para que eu possa marcar consultas de acordo com a disponibilidade.

**Critérios de Aceitação:**

* O sistema deve mostrar um calendário com horários disponíveis e ocupados.  
* O tutor deve conseguir filtrar horários de acordo com a data e tipo de consulta.

Como um tutor de pet, quero solicitar a marcação de uma consulta, para que eu não precise esperar a resposta do veterinário.

**Critérios de Aceitação:**

* O sistema deve permitir que o tutor envie um pedido de agendamento.  
* O tutor deve receber uma notificação de confirmação ou recusa do agendamento.

Como veterinário, quero ter uma visão centralizada de todas as consultas agendadas, para que eu possa gerenciar meu tempo eficientemente.

**Critérios de Aceitação:**

* O painel deve listar as consultas do dia/semana com status de cada consulta.  
* O veterinário deve poder bloquear horários para compromissos pessoais.

Como veterinário, quero registrar rapidamente o histórico clínico do pet, para que eu possa manter informações organizadas e acessíveis.

**Critérios de Aceitação:**

* O sistema deve oferecer um formulário otimizado para entrada rápida de dados clínicos.  
* O veterinário deve conseguir editar e consultar prontuários de forma simples.

Como um tutor de pet, quero receber notificações sobre confirmações de agendamento, para que eu fique informado sobre o status da consulta.

**Critérios de Aceitação:**

* O sistema deve enviar uma notificação via aplicativo ou e-mail após a solicitação de agendamento.  
* O tutor deve receber alertas para lembrá-lo da consulta agendada.

Como veterinário, quero gerenciar perfis de clientes e pets, para que eu tenha um registro completo e detalhado de cada paciente.

**Critérios de Aceitação:**

* O sistema deve permitir o cadastro de clientes e a associação de múltiplos pets a cada cliente.  
* O veterinário deve poder visualizar e editar informações de cada pet.

Como veterinário, quero ter flexibilidade para definir a duração de cada consulta, para que a agenda se adapte às minhas necessidades de atendimento.

**Critérios de Aceitação:**

* O sistema deve permitir que o veterinário configure a duração de cada consulta durante o agendamento.  
* O veterinário deve conseguir ajustar horários em tempo real conforme necessário.

Como um tutor de pet, quero poder visualizar o histórico clínico do meu animal, para que eu tenha acompanhamento das condições de saúde do pet.

**Critérios de Aceitação:**

* O sistema deve permitir que o tutor acesse o prontuário do pet.  
* O histórico deve ser facilmente navegável, mostrando dados de consultas anteriores e anotações do veterinário.

