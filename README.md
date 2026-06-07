# Atalaia Web

Estrutura base para migrar a interface do ESP32 para uma aplicacao web com `Django + Bootstrap`.

Os caminhos e comandos deste documento assumem a raiz do repositorio como diretorio de trabalho.

## Servicos

- `web`: Django com painel, admin e autenticacao.
- `worker`: consumidor MQTT que grava telemetria no PostgreSQL.
- `nginx`: proxy reverso e entrega de arquivos estaticos.
- `postgres`: banco principal.
- `mosquitto`: broker MQTT.

## Estrutura

```text
web/
worker/
nginx/
postgres/
mosquitto/
```

## Subida inicial

1. Copie `.env.example` para `.env`.
2. Ajuste as credenciais e hosts.
   Se for usar a stack Docker deste repositorio, defina `POSTGRES_HOST=postgres`.
   Tambem defina `MQTT_HOST=mosquitto`.
3. Suba os containers:

```bash
docker compose up --build
```

## Acesso

- Aplicacao: `http://localhost/`
- Admin Django: `http://localhost/admin/`

O superusuario inicial e criado a partir destas variaveis:

- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`

## Topico MQTT esperado

O worker assina por padrao:

```text
devices/+/telemetry
```

Payload esperado:

```json
{
  "type": "telemetry",
  "id": "AA:BB:CC:DD:EE:FF",
  "name": "Gateway Caixa Dagua",
  "probeId": "11:22:33:44:55:66",
  "probeName": "Sonda Caixa",
  "readingId": "11:22:33:44:55:66@2026-06-06T23:10:15",
  "fw": "gateway-0.1.0",
  "seq": 42,
  "receivedPackets": 42,
  "lostPackets": 3,
  "timeSinceLastReceptionMs": 5987,
  "rssi": -87,
  "snr": 7.5,
  "timestamp": "2026-06-06T23:10:15",
  "timestampEpoch": 1780783815,
  "temperature": 24.37
}
```

Regras aceitas pelo worker:

- `readingId` e usado como chave de idempotencia.
- `timeSinceLastReceptionMs` pode vir `null` na primeira leitura conhecida.
- `rssi` e `snr` sao obrigatorios e ficam disponiveis no `payload` salvo para uso futuro no dashboard.
- `temperature` pode vir `null` se a leitura do sensor falhar.
- `timestamp` e `timestampEpoch` podem vir `null` se o gateway ainda estiver sem horario sincronizado.
- `receivedPackets` e `lostPackets` sao tratados como contadores acumulados por `probeId`.

## Proximos passos

- adicionar tela de comandos remotos;
- expor graficos de historico;
- publicar comandos MQTT a partir do Django;
- restringir Mosquitto com usuario/senha e TLS.
