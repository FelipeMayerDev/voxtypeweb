# Topologia: 1 container que monta o voxtype e os dados do host, sem áudio

Um único serviço Docker (FastAPI) monta o binário e os dados do voxtype do host
por bind-mount. Meetings são **somente-leitura** (a web não muta dados do
voxtype). O host continua a fonte única da verdade; o container não captura áudio
nem roda o daemon.

## Contexto

O voxtype é um app de host que depende de hardware (áudio, teclado, daemon).
A web só precisa editar config e visualizar meetings (inclusive ao vivo,
observando arquivos). Iniciar gravação pela web exigiria passar `/dev/snd` +
socket do PipeWire + daemon para dentro do container — complexidade que o
escopo não pede.

## Decisão

Bind-mounts (montados nos **mesmos caminhos absolutos do host**, pois o
`index.db` guarda `storage_path` absoluto que a CLI do voxtype dereferencia):
- `/usr/bin/voxtype` + `/usr/lib/voxtype` — binário, libs e modelos (**ro**)
- `~/.local/share/voxtype` — meetings e `index.db` (**ro**): listar/exibir/exportar
- `~/.config/voxtype` — config TOML (**rw**, para salvar edições)
- `$XDG_RUNTIME_DIR/voxtype` — estado do daemon (**ro**, para o healthcheck)
- `~/.local/state/voxtypeweb` — estado próprio da web (**rw**): aliases de speaker
  (`speaker-aliases.json`), NÃO são dados do voxtype

A imagem também instala as libs de runtime do binário montado (`alsa-lib`,
`libstdc++`), ausentes no `fedora:44` mínimo.

Container roda como **UID 1000** (dados/config gravados pertencem ao usuário do
host). Base image **Fedora 44**: o host tem glibc 2.43; bases Debian/Ubuntu
atuais (glibc 2.41) não executam o binário montado.

## Consequências

- Nenhuma mutação nos dados do voxtype pela web (start/stop/pause/delete/label
  ficam no host). Renomear speaker é um alias de exibição próprio da web.
- O diretório de estado (`~/.local/state/voxtypeweb`) precisa existir e pertencer
  ao UID 1000 antes do `up` (senão o Docker o cria como root e a escrita falha).
- Trocar a base image por uma de glibc mais antiga quebra o binário montado.
