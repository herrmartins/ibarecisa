# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

#### Types of changes

-   **Added** for new features.
-   **Changed** for changes in existing functionality.
-   **Deprecated** for soon-to-be removed features.
-   **Removed** for now removed features.
-   **Fixed** for any bug fixes.
-   **Security** in case of vulnerabilities.

## [Unreleased](https://github.com/herrmartins/ibarecisa/commits/Unreleased) - 2024-00-00

### Added

- **Tesouraria**: Sistema completo de gestão financeira com funcionalidades de:
  - Cadastro e gestão de transações financeiras (receitas e despesas)
  - Categorização de transações para melhor organização
  - Periodização contábil por mês/ano para controle financeiro
  - Anexação de comprovantes digitais em transações
  - Interface moderna e responsiva com visualização detalhada
  - Estorno de transações com rastreabilidade completa
  - Balanços mensais consolidados por período contábil
  - Controle de acesso baseado em permissões (tesoureiro e admin)
  - Dashboard com cards estatísticos e filtros avançados
  - Modal lightbox para visualização de comprovantes
  - Atualização automática de balanços ao criar/editar transações

- **Edição de comentários**: Adicionada funcionalidade para que autores possam editar seus próprios comentários no blog. Inclui:
  - Novo endpoint API `PATCH /api2/comments/update/<comment_id>` para atualização de comentários
  - Validação de permissão para garantir que apenas o autor possa editar seu comentário
  - Interface JavaScript responsiva para edição inline de comentários
  - Botão "Editar" exibido apenas para autores dos comentários
  - Suporte para edição de comentários e respostas
  - Testes unitários e de integração abrangentes

### Changed

- **Framework CSS**: Substituição do Bootstrap 5 pelo Tailwind CSS 4 em toda a aplicação:
  - Build system com Tailwind CLI para geração otimizada de CSS
  - Arquivo de saída único em `core/static/css/tailwind/output.css`
  - Configuração moderna com `@import` do Tailwind v4
  - Componentes customizados para botões, cards, formulários e tabelas
  - Classes utilitárias para layout responsivo e estados interativos
  - Design system consistente com cores, espaçamentos e tipografia padronizados
  - Redução significativa do tamanho do CSS final após build
  - Melhor performance de carregamento com CSS puramente utilitário

## [0.1.0](https://github.com/herrmartins/ibarecisa/commits/0.1.0) - 2024-09-10

### Added

- Asynchronous reading and display of events. [task](https://trello.com/c/dbiwvUKf/8-chama-eventos-assincronamente)
