# USF4 Reader

O USF4 Reader é um complemento gratuito e de código aberto para NVDA, desenvolvido para
Ultra Street Fighter IV no Windows. Ele anuncia menus, escolhas e avisos reconhecidos enquanto
você navega com os controles habituais do jogo, sem atalhos de consulta ou OCR.

[Página oficial](https://deb-evelyn.com.br/USF4Reader/)
· [Baixar a versão 0.3.7](https://github.com/mama-eva/USF4Reader/releases/download/v0.3.7/USF4Reader-0.3.7.nvda-addon)
· [Notas da versão](https://github.com/mama-eva/USF4Reader/releases/tag/v0.3.7)
· [English](https://github.com/mama-eva/USF4Reader)

## Funcionalidades

A leitura está disponível nas seguintes áreas reconhecidas. A cobertura de cada uma ainda é parcial:

- Menu principal e telas de Options reconhecidas, incluindo Sound Settings e Voice Language.
- Seleção e personalização de personagens e nomes de Ultra Combo.
- Seleção de Trials, tarefas reconhecidas, avisos de conclusão e opções de resultado.
- Menus de pausa e perguntas reconhecidos, com a resposta selecionada.
- Menus de Player Data e linhas de registros, com personagem, categoria e valores apresentados.
- Stage Select, escolhas no resultado de Versus e avisos reconhecidos da abertura e da luta.

No resultado de Versus, a leitura identifica a escolha de cada jogador. Quando um deles muda
a seleção, a escolha inalterada do outro não é repetida. Sua voz e seu sintetizador do NVDA
continuam em uso. Na instalação testada, os nomes e avisos são anunciados em inglês, mesmo
quando o NVDA está configurado em português.

## Compatibilidade

Testado com **NVDA 2026.1** e com a edição Windows de **Ultra Street Fighter IV** utilizada pelo
projeto. A compatibilidade com outras edições do jogo ou versões do NVDA ainda não foi confirmada.
É necessário possuir uma cópia compatível do jogo; ela não está incluída no complemento.

## Instalação e atualização

1. Feche o jogo e mantenha o NVDA aberto.
2. Baixe e abra o arquivo `USF4Reader-0.3.7.nvda-addon`.
3. Confirme a instalação ou atualização e reinicie o NVDA quando solicitado.
4. Abra o jogo e navegue com seu teclado ou controle habitual.

A leitura começa automaticamente quando você volta ao jogo. Não há atalhos de consulta para
aprender. Para atualizar uma instalação existente, siga os mesmos passos com o pacote mais recente.
As próximas versões estarão na [página de Releases](https://github.com/mama-eva/USF4Reader/releases/latest)
e na [página oficial](https://deb-evelyn.com.br/USF4Reader/).

### Desinstalação

No NVDA, abra **Ferramentas → Loja de complementos** e localize USF4 Reader na lista de complementos
instalados. Escolha **Remover**, confirme e reinicie o NVDA quando solicitado. Para interromper
o uso temporariamente, você também pode escolher **Desativar**.

## Limitações conhecidas

Algumas telas podem ficar em silêncio. Estas áreas ainda precisam de trabalho:

- Páginas de Command List, detalhes de golpes e seus submenus.
- Leitura intermitente de Button Config e algumas outras telas de Options.
- Certas perguntas de confirmação, a tela de confronto e outras transições de Versus.
- Cobertura completa de telas online, Bonus Stages e variantes de cenário, pausa e resultado.
- Estatísticas em tempo real durante o combate e legendas cinematográficas apresentadas como imagens.

A leitura de Stage Select e os anúncios corrigidos de round ainda aguardam confirmação por escuta
após a atualização para 0.3.7. Os nomes de personagens nos avisos de novas cores e provocações
também precisam de confirmação durante o uso.

Consulte o [histórico de versões](https://github.com/mama-eva/USF4Reader/blob/main/changelog.md).
O download da versão 0.3.7 mantém seu guia original em português.

## Como relatar problemas

Use os [Issues do GitHub](https://github.com/mama-eva/USF4Reader/issues) ou escreva para
[smartdebby29@gmail.com](mailto:smartdebby29@gmail.com). Informe as versões do complemento e do
NVDA, o modo de jogo, a tela em que chegou, o que esperava ouvir e o último anúncio.
Não é necessário enviar uma captura de tela.

## Licença

O USF4 Reader é gratuito e de código aberto, sob a licença
[GPL-2.0-or-later](https://github.com/mama-eva/USF4Reader/blob/main/COPYING.txt).
Contribuições, sugestões e relatos de telas sem leitura são bem-vindos.

## Autora e contato

**Débora Evelyn Lisboa**

[smartdebby29@gmail.com](mailto:smartdebby29@gmail.com)
