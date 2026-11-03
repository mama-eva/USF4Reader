# USF4 Reader 0.3.7

O USF4 Reader oferece leitura automática com NVDA para Ultra Street Fighter IV. Ele acompanha os itens,
valores e escolhas reconhecidos enquanto você navega com os controles habituais do jogo.

**Autora:** Débora Evelyn Lisboa  
**Contato:** [smartdebby29@gmail.com](mailto:smartdebby29@gmail.com)

## Compatibilidade

- NVDA 2026.1. A compatibilidade com versões posteriores depende das alterações do NVDA.
- Ultra Street Fighter IV para Windows, com o executável x86 `SSFIV.exe` correspondente à edição verificada.

A compatibilidade foi verificada para este executável:

```text
SHA-256: a9017416ee8104cdde64d79f1e47697c1dfecb3d58496e4950945c3e37dea537
```

Outras edições do jogo ainda não têm compatibilidade confirmada.

## Instalação e atualização

1. Feche o jogo e mantenha o NVDA aberto.
2. Abra o arquivo `USF4Reader-0.3.7.nvda-addon`.
3. Confirme a instalação ou atualização no NVDA e reinicie o NVDA quando solicitado.
4. Abra o jogo normalmente e navegue com o teclado ou controle que você já utiliza.

A leitura acompanha automaticamente as mudanças reconhecidas. Não há atalhos de consulta do complemento
e não é utilizado OCR. O sintetizador e a voz configurados no NVDA permanecem sob seu controle.

Na instalação verificada, o jogo está em inglês. Os nomes, valores e mensagens auxiliares são anunciados
em inglês, mesmo quando a interface do NVDA está em português.

## Funcionalidades disponíveis

- Menus e submenus reconhecidos, com o item selecionado e seus valores.
- Seleção e personalização de personagens.
- Nomes de Ultra Combo.
- Seleção de Trials e leitura das tarefas reconhecidas.
- Janelas reconhecidas de pausa e resultado.
- Perguntas reconhecidas, com acompanhamento da resposta selecionada.
- Logos da abertura, indicação para pular o vídeo e aviso de Press Enter na tela de título.
- Anúncios de luta reconhecidos, como Round, Fight! e K.O., e avisos reconhecidos de conclusão de Trial.

## Atualização 0.3.7 em validação

Esta atualização procura melhorar a continuidade da leitura quando o jogo troca de tela. Leituras
incompletas passageiras deixam de causar uma reconexão desnecessária. Problemas de leitura e de
permissão passam a receber mensagens distintas. Foram acrescentadas uma prevenção para o travamento
do NVDA ao reconhecer as janelas do jogo e uma melhoria na rapidez da leitura dos avisos da abertura.
A documentação e a identificação da autora também foram revisadas.

Esta versão acrescenta leitura da seleção de cenário e das escolhas do menu de resultado de Versus.
Ao mudar uma escolha no resultado, somente o jogador cuja seleção mudou é anunciado. A numeração
dos rounds foi corrigida: o primeiro passa a ser anunciado como Round 1 e o segundo como Round 2.
As duas entradas de round foram capturadas durante uma partida real. A nova leitura de cenário e
resultado foi conferida em capturas e aguarda confirmação auditiva com este pacote.

Foram aprovados 101 testes automáticos, mantendo as verificações das versões anteriores e corrigindo
a expectativa antiga que reproduzia o erro na numeração do segundo round. A navegação
pela abertura, menu principal, Options e Sound Settings foi confirmada sem novo travamento na versão
0.3.5. A leitura da lista de Player Data, da seleção de personagens e das linhas e valores de Player
Records e Character Records foi confirmada pelo uso na versão 0.3.6. O título de Voice Language
também foi corrigido.

## Correções da versão 0.3.3

- O valor de tempo ilimitado nos menus em inglês, incluindo Time Select, é anunciado como **Infinite**.
  Isso evita a pronúncia em português do símbolo de infinito pelo NVDA.
- Os avisos de nova cor ou provocação procuram anunciar o nome do personagem. Quando esse nome não
  está disponível, a mensagem informa apenas o desbloqueio, sem pronunciar `[CHARANAME]` nem atribuí-lo
  a outro personagem.
- O aviso de desbloqueio de Car Crusher e as perguntas que já funcionavam foram preservados.

## Validação e limitações conhecidas

Menus, seleção de personagens, grade de Trials e pausa foram confirmados em uso nas versões anteriores.
As confirmações de saída e o aviso de Car Crusher foram confirmados na versão 0.3.2.
A versão 0.3.3 passou em 56 testes automáticos.

A leitura do nome do personagem nos novos avisos de desbloqueio ainda aguarda uma nova confirmação
auditiva durante o uso do jogo. Os testes automáticos dessa correção não substituem essa confirmação.

A cobertura é ampliada gradualmente. Ainda há telas de opções, variações de perguntas, transições do
modo Versus, Command List, Voice Language e situações de Button Config que precisam de verificação
ou de melhorias. As outras áreas sem cobertura completa confirmada incluem:

- Legendas cinematográficas apresentadas como imagens.
- Estatísticas de combate.
- Telas online.
- Bonus Stages.
- Seleção de cenário.
- Algumas variantes de pausa e resultado.

Telas desconhecidas permanecem em silêncio para evitar anúncios incorretos. O complemento não altera
a disponibilidade de conteúdo nem os arquivos originais do jogo.

O USF4 Reader funciona dentro do NVDA e consulta o jogo somente para leitura enquanto ele está em foco.
Não é necessário iniciar outro programa para utilizar o complemento.

## Histórico de versões

- **0.3.3:** leitura de Infinite em inglês e correções nos avisos de desbloqueio de cores e provocações.
- **0.3.2:** perguntas e respostas selecionadas, avisos da abertura e melhorias na leitura de Trials e resultados.
- **0.3.1:** grade e instruções de Trials e ampliação da leitura de menus de pausa.
- **0.3.0:** idioma do jogo, valores de submenus, personalização, nomes de Ultra Combo e anúncios de luta.

## Contato

Para relatar um problema, informe a versão do complemento, o modo de jogo, a tela em que a leitura
parou e o que foi anunciado. Não é necessário enviar capturas de tela.

Entre em contato com Débora Evelyn Lisboa pelo e-mail
[smartdebby29@gmail.com](mailto:smartdebby29@gmail.com).
