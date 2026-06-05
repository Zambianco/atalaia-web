# PostgreSQL de Desenvolvimento

Este documento descreve a configuracao inicial do PostgreSQL para desenvolvimento do Atalaia, mantendo um usuario administrativo separado e usando um usuario proprio da aplicacao para o ambiente local.

## Estrutura recomendada

- `lyra`: administrador do cluster PostgreSQL.
- `atalaia_dev`: banco da aplicacao em desenvolvimento.
- `atalaia_user_dev`: usuario usado pelo Django no ambiente de desenvolvimento.

O Django deve se conectar usando `atalaia_user_dev`, nunca usando `lyra`.

## 1. Entrar no PostgreSQL

No servidor ou maquina local:

```bash
sudo -u postgres psql
```

Se `lyra` ja existir e voce preferir usar esse usuario:

```bash
psql -U lyra -d postgres
```

No Windows, se `psql` estiver instalado:

```cmd
psql -h localhost -U postgres -d postgres
```

## 2. Conferir ou criar o admin `lyra`

Liste os roles existentes:

```sql
\du
```

Se precisar criar o `lyra`:

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
CREATE ROLE atalaia_user_dev
WITH
  LOGIN
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  INHERIT
  PASSWORD 'SENHA_DA_APLICACAO_DEV';
```

## 4. Criar o banco da aplicacao

Crie o banco ja pertencendo ao usuario da aplicacao:

```sql
CREATE DATABASE atalaia_dev
  OWNER atalaia_user_dev
  ENCODING 'UTF8'
  TEMPLATE template0;
```

## 5. Ajustar permissoes do schema `public`

Conecte no banco:

```sql
\c atalaia_dev
```

Garanta que o schema principal pertence ao usuario da aplicacao:

```sql
ALTER SCHEMA public OWNER TO atalaia_user_dev;
GRANT USAGE, CREATE ON SCHEMA public TO atalaia_user_dev;
```

Isso normalmente basta para o Django criar tabelas com `python manage.py migrate`.

## 6. Validar a conexao

Teste a conexao com o usuario da aplicacao:

```bash
psql -h localhost -U atalaia_user_dev -d atalaia_dev
```

No Windows:

```cmd
psql -h localhost -U atalaia_user_dev -d atalaia_dev
```

Se a conexao funcionar, a base esta pronta para a aplicacao.

## 7. Configuracao do Django

No `.env` local:

Se a aplicacao estiver rodando via `docker compose` deste repositorio, use o nome do servico `postgres` como host:

```env
POSTGRES_DB=atalaia_dev
POSTGRES_USER=atalaia_user_dev
POSTGRES_PASSWORD=SENHA_DA_APLICACAO_DEV
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_SECRET_KEY=sua-chave-secreta-local
```

Se voce for rodar o Django fora do Docker, ai sim `POSTGRES_HOST=localhost` pode fazer sentido.

## 8. Rodar as migracoes

Na aplicacao:

```bash
python manage.py migrate
python manage.py createsuperuser_if_missing
python manage.py runserver
```

No Windows:

```cmd
python manage.py migrate
python manage.py createsuperuser_if_missing
python manage.py runserver
```

## Boas praticas

- Nao use `lyra` no `.env` local da aplicacao.
- Nao de `SUPERUSER` para `atalaia_user_dev`.
- Use senhas diferentes para `lyra` e `atalaia_user_dev`.
- Mantenha `DJANGO_DEBUG=1` apenas em desenvolvimento.
- Se precisar recriar o banco com frequencia, faca isso com o usuario admin, nao com o usuario da aplicacao.

## Script SQL completo

Se quiser executar a preparacao basica em uma sequencia unica:

```sql
CREATE ROLE atalaia_user_dev
WITH
  LOGIN
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  INHERIT
  PASSWORD 'SENHA_DA_APLICACAO_DEV';

CREATE DATABASE atalaia_dev
  OWNER atalaia_user_dev
  ENCODING 'UTF8'
  TEMPLATE template0;

\c atalaia_dev

ALTER SCHEMA public OWNER TO atalaia_user_dev;
GRANT USAGE, CREATE ON SCHEMA public TO atalaia_user_dev;
```
