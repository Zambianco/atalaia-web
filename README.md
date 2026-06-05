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
  "name": "Caixa d'agua",
  "fw": "sonda-0.2.0",
  "temperature": 25.31
}
```

## Proximos passos

- adicionar tela de comandos remotos;
- expor graficos de historico;
- publicar comandos MQTT a partir do Django;
- restringir Mosquitto com usuario/senha e TLS.
