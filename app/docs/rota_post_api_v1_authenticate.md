# Documentacao de Fluxo por Caso de Uso

## Identificacao da Rota
- Metodo: `POST`
- Caminho: `/api/v1/authenticate`
- Modulo: `app/api/v1/endpoints/auth.py`
- Funcao: `login_json`
- Tipo de handler: sincrono (`def`)

## Dependencias e Injeções (FastAPI)
- `data: AuthRequest`
  - Body JSON com `name` e `password`.
- `response: Response`
  - Objeto usado para definir cookie de autenticacao.
- `session: Session = Depends(db_client.get_session)`
  - Sessao SQLAlchemy criada por request e fechada ao final.

## Cadeia de Componentes Executada
- Endpoint -> `UserRepository(session)`
- Endpoint -> `AuthService(user_repo)`
- `AuthService.authenticate(data.name, data.password)`
- `create_token_for_user(user)`
- `set_auth_cookie(response, access_token)`
- Retorno `TokenResponse`

## Caso de Uso 1: Autenticar com JSON
### Objetivo
Permitir autenticacao de cliente que envia credenciais em JSON.

### Pre-condicoes
- Usuario cadastrado na base.
- Senha valida para o usuario.
- Configuracoes JWT disponiveis.

### Fluxo Tecnico Detalhado
1. Cliente envia `POST /api/v1/authenticate` com payload JSON valido.
2. FastAPI valida schema `AuthRequest`.
3. FastAPI resolve `session` via `Depends(db_client.get_session)`.
4. Endpoint cria `UserRepository` e `AuthService`.
5. `AuthService.authenticate` consulta usuario e valida senha hash.
6. Em sucesso, endpoint gera token com `create_token_for_user`.
7. Endpoint seta cookie HTTP-only com `set_auth_cookie`.
8. Endpoint retorna `TokenResponse` com `access_token` e `token_type` default.
9. Final da request: dependencia de sessao fecha conexao da sessao.

### Entrada Esperada
- Content-Type: `application/json`
- Body:
```json
{
  "name": "usuario",
  "password": "senha"
}
```

### Saida Esperada
- Status: `200 OK`
- Body:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```
- Side effects:
  - Cookie de autenticacao enviado na resposta.

## Caso de Uso 2: Payload invalido
### Fluxo de Excecao
1. Body JSON ausente/invalido ou campos obrigatorios faltando.
2. FastAPI/Pydantic bloqueia chamada do handler.

### Saida de Erro
- Status: `422 Unprocessable Entity`
- Erro padrao de validacao de schema.

## Caso de Uso 3: Credenciais invalidas
### Fluxo de Excecao
1. Usuario inexistente ou senha incorreta.
2. `AuthService` lanca `HTTPException`.

### Saida de Erro
- Status: `401 Unauthorized`
- Body detail: `Credenciais invalidas`

## Observacoes Operacionais
- Sem persistencia no banco nessa rota; apenas leitura de usuario para autenticacao.
- Reuso dos utilitarios de token/cookie em `app/api/v1/endpoints/utils.py`.
