# Ordem do Culto - Guia de Uso

## Visão Geral

O módulo **Ordem do Culto** registra a programação completa de cada culto, incluindo a ordem dos itens (hinos, leituras, orações etc.) e um histórico das **canções efetivamente cantadas**. Ele integra-se ao **catálogo de canções** para vincular automaticamente hinos detectados na programação ao cadastro existente.

---

## Estrutura de Dados

### WorshipService (o culto)

| Campo | Descrição |
|---|---|
| `title` | Título do culto (ex: "Culto de Ceia - 20/04/2026") |
| `service_kind` | Tipo: Regular, Ceia, Cantata ou Especial |
| `service_date` | Data do culto |
| `service_time` | Horário (opcional) |
| `leader_dirigente` | Nome do dirigente |
| `leader_regente` | Nome do regente |
| `leader_musician` | Nome do pianista/músico |
| `leaders_text` | Texto consolidado da liderança (auto-gerado a partir dos campos individuais, formato: "Dirigente: X / Regente: Y / Pianista: Z") |
| `program_html` | Ordem do culto em HTML (editor TinyMCE) |
| `program_font_scale` | Escala da fonte para impressão (75% a 130%, padrão 100%) |
| `notes` | Observações livres |

### WorshipServiceSong (canção cantada no culto)

Cada registro representa uma canção que foi cantada ou citada durante o culto.

| Campo | Descrição |
|---|---|
| `song` | FK para o catálogo `Song` (pode ser null = avulsa) |
| `song_snapshot` | Texto original como apareceu na programação |
| `source` | `MANUAL` (adicionada à mão) ou `IMPORTED` (extraída da programação) |
| `order_ref` | Posição na ordem do culto |
| `resolution_status` | Status de vínculo com o catálogo (ver abaixo) |
| `detected_hymnal` / `detected_number` | Hinário e número detectados automaticamente |
| `match_confidence` | Confiança da resolução automática (0 a 1) |
| `resolution_note` | Nota sobre a resolução |

---

## Status de Resolução (`resolution_status`)

O sistema tenta vincular automaticamente cada canção ao catálogo. O resultado cai em um destes estados:

| Status | Badge | Significado |
|---|---|---|
| **Vinculada** (`LINKED`) | Verde | Canção foi encontrada no catálogo com confiança >= 80% |
| **Pendente** (`PENDING_REVIEW`) | Amarelo | O sistema detectou a canção mas não tem confiança suficiente para vincular automaticamente |
| **Avulsa** (`UNLINKED`) | Cinza | O usuário decidiu manter sem vínculo com o catálogo |

---

## Fluxos de Uso

### 1. Criar culto manualmente

1. Acesse `/worship/services/` e clique em **Novo Culto**
2. Preencha título, tipo, data, horário e liderança
3. No campo **Programação**, use o editor TinyMCE para montar a ordem do culto com `<ol><li>` (listas ordenadas)
4. Salve

### 2. Gerar culto com IA (a partir de texto)

1. Acesse `/worship/services/import/` (ou clique em **Gerar com IA** na listagem)
2. Cole o texto da programação (pode vir do WhatsApp, Word etc.)
3. Opcionalmente, adicione uma instrução extra no campo de dica (ex: "incluir campo de ceia")
4. Clique em **Gerar pré-visualização**
5. Revise o resultado: título, data, tipo, liderança, programação HTML e canções detectadas
6. Se estiver bom, clique em **Criar culto com esta estrutura**

> **Requisito:** A variável `MISTRAL_API_KEY` deve estar configurada no `.env`. O sistema usa a API do Mistral para parsing.

### 3. Gerar programação com IA em culto existente

1. Abra um culto para edição (`/worship/services/<id>/edit/`)
2. Na seção **Gerar com IA** (aparece apenas ao editar), cole o texto base
3. Clique em **Gerar programação com IA**
4. O sistema sobrescreve título, liderança, programação e reimporta as canções detectadas

### 4. Extrair canções da programação

Após ter a programação HTML preenchida (manualmente ou por IA):

1. Na página de detalhe do culto, clique em **Extrair da programação**
2. O sistema analisa o HTML buscando linhas com "hino", "CC", "VM", "HA", "HL"
3. Cada canção detectada é criada como `WorshipServiceSong` com origem `IMPORTED`
4. A resolução automática tenta vincular ao catálogo

> **Importante:** Re-extrair **substitui** todas as canções importadas anteriormente. Canções manuais não são afetadas.

### 5. Resolver canções pendentes

Após extrair canções, as que não foram vinculadas automaticamente aparecem com badge **Pendente**. Para cada uma:

- **Vincular:** Selecione uma canção do catálogo no dropdown e clique em **Vincular**. O status muda para **Vinculada**. Funciona para qualquer status, inclusive para trocar o vínculo de uma canção já vinculada.
- **Manter avulsa:** Clique em **Manter avulsa**. O status muda para **Avulsa** e a canção permanece apenas como registro textual, sem link com o catálogo. Use quando a canção não existe no cadastro e você não pretende cadastrá-la. Disponível para Vinculadas e Pendentes.
- **Tentar novamente:** Re-executa a resolução automática. Útil quando novas canções foram cadastradas no catálogo após a importação. Disponível para Pendentes e Avulsas.
- **Remover:** Remove o registro daquela canção do culto.

> Canções vinculadas aparecem como link clicável para a página de detalhes da canção no catálogo.

### 6. Adicionar canção extra (não listada na programação)

1. Na seção **"Adicionar canção extra"** (final da página de detalhe), abra o painel
2. Digite o nome da canção (ex: "VM 123 - Vencendo vem Jesus")
3. Clique em **Salvar canção extra**
4. O sistema tenta resolver automaticamente; se não encontrar, fica como pendente

### 7. Duplicar culto

Clique em **Duplicar** na página de detalhe. Isso cria uma cópia completa do culto (programação + canções) e redireciona para a edição, permitindo ajustar data, liderança etc.

### 8. Excluir culto

Na página de detalhe, clique em **Excluir**. Uma confirmação será pedida. A exclusão é permanente e remove o culto e todas as canções associadas.

### 9. Imprimir / PDF

Na página de detalhe do culto:

- **Imprimir:** Abre uma versão otimizada para impressão no navegador
- **PDF 1/página:** Gera PDF em retrato (A4) com uma cópia por folha
- **PDF 2/página:** Gera PDF em paisagem (A4) com duas cópias lado a lado

> A escala da fonte pode ser ajustada com os botões **A-**, **A+** e **100%** na página de detalhe. Isso afeta tanto a visualização quanto a impressão/PDF.

---

## Resolução Automática de Canções

O algoritmo em `worship/utils/song_resolution.py` funciona assim:

1. **Parse:** Extrai referência de hinário e número do texto (ex: "CC 291 - A Deus demos glória" → hinário "CC", número 291)
2. **Resolução do hinário:** Busca pelo hinário no cadastro usando aliases exatos ou similaridade fuzzy (cutoff 0.72). Os aliases são definidos no modelo `HymnalAlias`.
3. **Busca da canção:**
   - Se hinário + número encontrados: busca exata por `hymnal + hymn_number` (confiança 1.0 ou 0.65 se houver múltiplas)
   - Se não: busca por título similar (confiança 0.82 se única, 0.55 se múltiplas)
4. **Decisão final:**
   - Confiança >= 0.8 → **Vinculada** automaticamente
   - Hinário detectado como "HA" (hinos avulsos) → **Avulsa** automaticamente
   - Demais casos → **Pendente** para revisão manual

---

## URLs do Módulo

| URL | Nome | Ação |
|---|---|---|
| `/worship/services/` | `service-list` | Listagem de cultos |
| `/worship/services/new/` | `service-create` | Formulário de criação |
| `/worship/services/import/` | `service-import` | Gerar culto com IA |
| `/worship/services/<id>/` | `service-detail` | Detalhe do culto |
| `/worship/services/<id>/edit/` | `service-edit` | Editar culto |
| `/worship/services/<id>/delete/` | `service-delete` | Excluir culto |
| `/worship/services/<id>/duplicate/` | `service-duplicate` | Duplicar culto |
| `/worship/services/<id>/font-scale/` | `service-font-scale` | Ajustar escala da fonte |
| `/worship/services/<id>/generate/` | `service-generate` | Gerar programação com IA |
| `/worship/services/<id>/songs/sync/` | `service-song-sync` | Extrair canções da programação |
| `/worship/services/<id>/songs/add/` | `service-song-add` | Adicionar canção extra |
| `/worship/services/<id>/songs/<sid>/delete/` | `service-song-delete` | Remover canção do culto |
| `/worship/services/<id>/songs/<sid>/resolve/` | `service-song-resolve` | Vincular/manter avulsa |
| `/worship/services/<id>/print/` | `service-print` | Versão para impressão |
| `/worship/services/<id>/pdf/` | `service-pdf` | Download PDF |

---

## Permissões

Todas as views usam `WorshipAccessMixin` que permite acesso a:

- Superusuários
- Membros do staff
- Usuários com tipo `REGULAR`

---

## Dicas Práticas

- **Antes de importar canções**, certifique-se de que os hinários estejam cadastrados com seus aliases (ex: "CC" para "Cantor Cristão", "HCC" para "Hinário Para o Culto Cristão"). Isso é feito em **Configurações do Catálogo** (`/worship/catalog-settings/`).
- O campo **Instrução extra** ao gerar com IA aceita dicas como "manter formato tradicional", "incluir ceia quando houver", "usar hinário HCC" etc.
- A **escala da fonte** é salva por culto, então cada programação pode ter seu próprio tamanho ideal para impressão.
- **Liderança:** Os campos individuais (Dirigente, Regente, Pianista) são automaticamente consolidados em `leaders_text` ao salvar. Se todos estiverem vazios, a IA pode preencher diretamente o campo consolidado.
- Ao **duplicar** um culto, todos os registros de canções são copiados com seus respectivos status de resolução, permitindo reutilizar um culto como template.
- O botão **Tentar novamente** é útil quando canções foram cadastradas no catálogo após a importação da programação — ele re-executa o algoritmo de resolução automática.
