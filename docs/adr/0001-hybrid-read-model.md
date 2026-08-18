# Modelo de leitura híbrido: CLI para exportar, arquivos para ler

O backend lê os **arquivos direto** (`index.db`, `transcript.json`) para listar
e exibir, e usa o **CLI do voxtype** para renderizar o transcript na tela
(`voxtype meeting export -f markdown`, que aplica timestamps/speakers). A web não
muta dados do voxtype.

## Contexto

O CLI não expõe saída estruturada para listagem (`meeting list` é texto puro,
sem `--json`) nem stream do transcript ao vivo (o único `--follow` é o estado
do daemon, não o texto). Ler `index.db` e os JSON direto dá listagem completa,
ordenável e atualização a cada 5s para o Live View — coisas impossíveis via CLI.

## Decisão

- **Leitura** (list / show): ler `index.db` (SQLite) direto.
- **Transcript na tela**: `voxtype meeting export -f markdown --timestamps
  --speakers`, renderizado para HTML. O CLI é o dono do formato; não relemos
  `transcript.json` para montar o texto (o `storage_path` é absoluto do host).
- **Renomear speaker**: alias de exibição próprio da web (ver ADR 0002 e
  CONTEXT), pois o `voxtype meeting label` só cobre `SPEAKER_NN` diarizado, que
  este build não gera (speakers por canal: `You`/`Remote`).

Nunca escrever no `index.db` nem nos arquivos de meeting — a web é read-only
sobre os dados do voxtype.
