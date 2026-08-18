# Voxtype Web

Interface web (Docker) para o app CLI/TUI **Voxtype** já instalado no host:
editar configuração e visualizar meetings (inclusive ao vivo). Sem autenticação;
apenas verifica se o voxtype está instalado e se o daemon está rodando.

## Language

**Voxtype**:
O app existente (CLI + TUI de configuração) que esta interface estende. Fonte
única da verdade: binário, config e dados vivem no host.
_Avoid_: "backend de transcrição", "engine" (engine é outra coisa, ver abaixo).

**Daemon**:
Processo residente do voxtype que captura áudio e escreve estado. Estado em
`$XDG_RUNTIME_DIR/voxtype/state` (`idle` | `recording` | `transcribing`).
_Avoid_: serviço, servidor.

**Meeting**:
Uma sessão de transcrição de longa duração, identificada por UUID, com
`metadata.json` + `transcript.json` num diretório próprio e uma linha no
índice `index.db`. Status: `active` | `paused` | `completed` | `cancelled`.
_Avoid_: sessão, gravação, call.

**Meeting Mode**:
Modo do voxtype que fatia o áudio em chunks, transcreve cada um e costura um
transcript contínuo com timestamps, persistindo por chunk (à prova de crash).
_Avoid_: modo gravação, modo longo.

**Chunk**:
Fatia de áudio de duração fixa (`meeting.chunk_duration_secs`, default 15s)
processada de uma vez. Define a granularidade mínima da visualização ao vivo.
_Avoid_: bloco, pedaço.

**Segment**:
Trecho transcrito dentro de um transcript, com `startMs`/`endMs`, `text`,
`source` (`microphone` | `loopback`) e opcionalmente `speaker`.
_Avoid_: linha, frase, trecho.

**Transcript**:
A coleção ordenada de Segments de uma Meeting. Exportável em `text`,
`markdown` ou `json` via `voxtype meeting export`.
_Avoid_: transcrição, texto.

**Speaker Label**:
Nome legível atribuído a um ID de speaker. No modelo do voxtype vem de
`voxtype meeting label` (só speakers diarizados `SPEAKER_NN`, em `speaker_labels`).
Como este build atribui speakers por canal (`You`/`Remote`, `source="both"`), a web
aplica um **alias de exibição próprio** (speaker_id -> nome) na renderização do
transcript; não muta os dados do voxtype.
_Avoid_: participante, orador.

**Diarization**:
Atribuição automática de Segments a speakers (`meeting.diarization`).
_Avoid_: separação de vozes.

**Engine**:
Backend de transcrição selecionado (`parakeet`, `whisper`, etc.). Distinto do
**Variant** (binário compilado).
_Avoid_: modelo, motor.

**Variant**:
Build específico do binário voxtype (ex.: `voxtype-onnx-avx2`), escolhido por
CPU/GPU. `/usr/bin/voxtype` é symlink para o variant ativo em `/usr/lib/voxtype`.
_Avoid_: build, versão.

**Config**:
O arquivo TOML comentado em `~/.config/voxtype/config.toml`. Editado direto
(não há setter não-interativo no CLI); comentários devem ser preservados.
_Avoid_: settings, preferências.

**Live View**:
Visualização de uma Meeting `active`/`paused` enquanto acontece. Atualiza na
granularidade do Chunk (não é palavra-a-palavra); obtida lendo
`transcript.json`/`index.db`, pois o CLI não expõe stream de transcript.
_Avoid_: tempo real, streaming.
