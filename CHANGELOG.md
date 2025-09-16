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

- **Edição de comentários**: Adicionada funcionalidade para que autores possam editar seus próprios comentários no blog. Inclui:
  - Novo endpoint API `PATCH /api2/comments/update/<comment_id>` para atualização de comentários
  - Validação de permissão para garantir que apenas o autor possa editar seu comentário
  - Interface JavaScript responsiva para edição inline de comentários
  - Botão "Editar" exibido apenas para autores dos comentários
  - Suporte para edição de comentários e respostas
  - Testes unitários e de integração abrangentes

## [0.1.0](https://github.com/herrmartins/ibarecisa/commits/0.1.0) - 2024-09-10

### Added

- Asynchronous reading and display of events. [task](https://trello.com/c/dbiwvUKf/8-chama-eventos-assincronamente)
