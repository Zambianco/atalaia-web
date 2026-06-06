# TODO

## Prioridade alta

- [ ] Implementar comandos remotos de ponta a ponta:
  - criar comando pela interface web;
  - publicar comando via MQTT;
  - receber ACK do dispositivo;
  - exibir status do comando no painel.
- [ ] Proteger o broker MQTT:
  - remover acesso anonimo;
  - configurar usuario e senha;
  - avaliar TLS;
  - evitar exposicao publica da porta `1883` quando nao for necessario.
- [ ] Criar alertas e eventos automaticos:
  - dispositivo offline;
  - temperatura fora do limite;
  - payload invalido;
  - firmware desatualizado.

## Prioridade media

- [ ] Melhorar o dashboard operacional:
  - filtro por periodo;
  - min, media e max por dispositivo;
  - ultima leitura com unidade;
  - status "offline ha X minutos";
  - grafico geral com todos os dispositivos.
- [ ] Melhorar tratamento de telemetria:
  - aceitar `timestamp` enviado pelo dispositivo;
  - guardar latencia entre leitura e recebimento;
  - deixar a deduplicacao mais explicita.
- [ ] Adicionar observabilidade:
  - healthcheck do worker;
  - logs estruturados;
  - contadores de mensagens recebidas e erros;
  - indicador de status do worker e do broker.
- [ ] Definir politica de retencao de dados:
  - manter dados brutos por periodo limitado;
  - consolidar historico por hora ou dia;
  - evitar crescimento infinito do Postgres.

## Prioridade baixa

- [ ] Adicionar testes minimos:
  - parser de payload MQTT;
  - deduplicacao de telemetria;
  - criacao e atualizacao de dispositivos;
  - views principais.
- [ ] Ajustar configuracao para producao:
  - HTTPS;
  - cookies seguros;
  - HSTS;
  - `CSRF_TRUSTED_ORIGINS`;
  - hardening do admin.
- [ ] Polir a experiencia da interface:
  - estados vazios;
  - acentuacao dos textos;
  - navegacao ativa;
  - responsividade mobile;
  - acoes rapidas por dispositivo.
