# Topologia: 1 container que monta o voxtype e os dados do host, sem áudio

Um único serviço Docker (FastAPI) monta o binário e os dados do voxtype do host
por bind-mount e é **somente-visualização** para meetings. O host continua a
fonte única da verdade; o container não captura áudio nem roda o daemon.

## Contexto

O voxtype é um app de host que depende de hardware (áudio, teclado, daemon).
A web só precisa editar config e visualizar meetings (inclusive ao vivo,
observando arquivos). Iniciar gravação pela web exigiria passar `/dev/snd` +
socket do PipeWire + daemon para dentro do container — complexidade que o
escopo não pede.

## Decisão

Bind-mounts:
- `/usr/bin/voxtype` + `/usr/lib/voxtype` — binário, libs e modelos (**ro**)
- `~/.local/share/voxtype` — meetings e `index.db` (**ro**)
- `~/.config/voxtype` — config TOML (**rw**, para salvar edições)
- `$XDG_RUNTIME_DIR/voxtype` — estado do daemon (**ro**, para o healthcheck)

Container roda como **UID 1000** (config salva pertence ao usuário do host).
Base image **Fedora 44**: o host tem glibc 2.43; bases Debian/Ubuntu atuais
(glibc 2.41) não executam o binário montado.

## Consequências

- Gravação/controle de meetings fica fora de escopo da web (só no host).
- Trocar a base image por uma de glibc mais antiga quebra o binário montado.
