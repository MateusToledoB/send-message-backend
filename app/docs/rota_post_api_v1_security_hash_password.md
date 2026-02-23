# Documentacao de Fluxo por Caso de Uso

## Identificacao da Rota
- Metodo: `POST`
- Caminho: `/api/v1/security/hash-password`
- Modulo: `app/api/v1/endpoints/security.py`
- Funcao: `hash_password`
- Tipo de handler: sincrono (`def`)

## Dependencias e Injeções (FastAPI)
- `data: PasswordHashRequest`
  - Body JSON com campo `password`.
- Nao utiliza `Depends`.

## Cadeia de Componentes Executada
- Endpoint -> `get_password_hash(data.password)`
- Retorno `PasswordHashResponse`

## Caso de Uso 1: Gerar hash para senha
### Objetivo
Gerar hash de senha para uso em persistencia segura no banco.

### Pre-condicoes
- Payload JSON valido com `password`.

### Fluxo Tecnico Detalhado
1. Cliente envia `POST /api/v1/security/hash-password` com senha em JSON.
2. FastAPI valida `PasswordHashRequest`.
3. Endpoint chama `get_password_hash`, que usa `CryptContext` (passlib).
4. Endpoint retorna objeto `PasswordHashResponse` com `password_hash`.

### Entrada Esperada
```json
{
  "password": "senha_em_texto_puro"
}
```

### Saida Esperada
- Status: `200 OK`
- Body:
```json
{
  "password_hash": "<hash>"
}
```

## Caso de Uso 2: Payload invalido
### Fluxo de Excecao
1. Campo `password` ausente ou body invalido.
2. FastAPI/Pydantic rejeita request antes de entrar no handler.

### Saida de Erro
- Status: `422 Unprocessable Entity`
- Erro padrao de validacao.

## Observacoes Operacionais
- Endpoint nao persiste dados e nao requer autenticacao.
- Uso recomendado para apoio administrativo/desenvolvimento, nao para login.
