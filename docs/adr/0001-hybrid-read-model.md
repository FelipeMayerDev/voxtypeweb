# Modelo de leitura híbrido: CLI para mutações, arquivos para leitura

O backend usa o **CLI do voxtype** para ações que mutam estado
(`voxtype meeting export`, `label`, `delete`) e lê os **arquivos direto**
(`index.db`, `metadata.json`, `transcript.json`) para listar, exibir e para o
Live View.

## Contexto

O CLI não expõe saída estruturada para listagem (`meeting list` é texto puro,
sem `--json`) nem stream do transcript ao vivo (o único `--follow` é o estado
do daemon, não o texto). Ler `index.db` e os JSON direto dá listagem completa,
ordenável e atualização a cada 5s para o Live View — coisas impossíveis via CLI.

## Decisão

- **Leitura** (list / show / live): ler `index.db` (SQLite) + `transcript.json`.
- **Mutação** (export / label / delete): invocar o binário voxtype, que é o
  dono do formato e mantém `index.db` e os arquivos coerentes.

Nunca escrever no `index.db` ou nos arquivos de meeting direto — mutação sempre
via CLI, para não divergir do que o voxtype espera.
