# PostgreSQL de Producao

Este documento descreve a configuracao inicial do PostgreSQL para producao do Atalaia, mantendo `lyra` como superadmin do cluster e usando um usuario proprio da aplicacao.

## Estrutura recomendada

- `lyra`: administrador do cluster PostgreSQL.
- `atalaia_prod`: banco da aplicacao.
- `atalaia_user_prod`: usuario usado pelo Django em producao.

O Django deve se conectar usando `atalaia_user_prod`, nunca usando `lyra`.

## 1. Entrar no PostgreSQL

No servidor Linux:

```bash
sudo -u postgres psql
```

Se `lyra` ja existir e voce preferir usar esse usuario:

```bash
psql -U lyra -d postgres
```

## 2. Conferir ou criar o superadmin `lyra`

Liste os roles existentes:

```sql
\du
```

Se precisar criar o `lyra` como superuser:

```sql
CREATE ROLE lyra WITH LOGIN SUPERUSER CREATEDB CREATEROLE PASSWORD 'SENHA_FORTE_AQUI';
```

Se ele ja existir e voce quiser apenas garantir os privilegios:

```sql
ALTER ROLE lyra WITH SUPERUSER CREATEDB CREATEROLE LOGIN;
```

## 3. Criar o usuario da aplicacao

Crie um usuario sem privilegios administrativos:

```sql
CREATE ROLE atalaia_user_prod
WITH
  LOGIN
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  INHERIT
  PASSWORD 'SENHA_FORTE_DA_APLICACAO';
```

## 4. Criar o banco da aplicacao

Crie o banco ja pertencendo ao usuario da aplicacao:

```sql
CREATE DATABASE atalaia_prod
  OWNER atalaia_user_prod
  ENCODING 'UTF8'
  TEMPLATE template0;
```

## 5. Ajustar permissoes do schema `public`

Conecte no banco:

```sql
\c atalaia_prod
```

Garanta que o schema principal pertence ao usuario da aplicacao:

```sql
ALTER SCHEMA public OWNER TO atalaia_user_prod;
GRANT USAGE, CREATE ON SCHEMA public TO atalaia_user_prod;
```

Isso normalmente basta para o Django criar tabelas com `python manage.py migrate`.

## 6. Validar a conexao

Teste a conexao com o usuario da aplicacao:

```bash
psql -h localhost -U atalaia_user_prod -d atalaia_prod
```

Se a conexao funcionar, a base esta pronta para a aplicacao.

## 7. Configuracao do Django

No `.env` de producao:

Se a aplicacao estiver rodando via `docker compose` deste repositorio, use o nome do servico `postgres` como host:

```env
POSTGRES_DB=atalaia_prod
POSTGRES_USER=atalaia_user_prod
POSTGRES_PASSWORD=SENHA_FORTE_DA_APLICACAO
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
DJANGO_SECRET_KEY=sua-chave-secreta-forte
```

Se o Django estiver fora do Docker e o banco no mesmo servidor, `POSTGRES_HOST=localhost` continua valido.

## 8. Rodar as migracoes

Na aplicacao:

```bash
python manage.py migrate
python manage.py createsuperuser_if_missing
```

## Boas praticas

- Nao use `lyra` no `.env` da aplicacao.
- Nao de `SUPERUSER` para `atalaia_user_prod`.
- Use senhas diferentes para `lyra` e `atalaia_user_prod`.
- Restrinja acesso ao PostgreSQL no firewall quando ele estiver fora de uma rede interna Docker.
- Em Compose, prefira `POSTGRES_HOST=postgres`.

## Script SQL completo

Se quiser executar a preparacao basica em uma sequencia unica:

```sql
CREATE ROLE atalaia_user_prod
WITH
  LOGIN
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  INHERIT
  PASSWORD 'SENHA_FORTE_DA_APLICACAO';

CREATE DATABASE atalaia_prod
  OWNER atalaia_user_prod
  ENCODING 'UTF8'
  TEMPLATE template0;

\c atalaia_prod

ALTER SCHEMA public OWNER TO atalaia_user_prod;
GRANT USAGE, CREATE ON SCHEMA public TO atalaia_user_prod;
```
