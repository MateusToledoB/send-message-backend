# Documentacao de Fluxo por Caso de Uso

## Identificacao da Rota
- Metodo: `POST`
- Caminho: `/api/v1/security/create`
- Modulo: `app/api/v1/endpoints/security.py`
- Funcao: `create_user`
- Tipo de handler: sincrono (`def`)

## Dependencias e Injeções (FastAPI)
- `data: CreateUserRequest`
  - Body JSON com `user`, `password` e `setor`.
  - `password` aceita alias `passwor` via `validation_alias`.
- `session: Session = Depends(db_client.get_session)`
  - Sessao SQLAlchemy por request com fechamento automatico no final.

## Cadeia de Componentes Executada
- Endpoint -> consulta `session.query(User).filter(User.name == data.user).first()`
- Endpoint -> `get_password_hash(data.password)`
- Endpoint -> `session.add(user)` + `session.commit()` + `session.refresh(user)`
- Retorno `CreateUserResponse`

## Caso de Uso 1: Criar usuario com sucesso
### Objetivo
Cadastrar um novo usuario na tabela `users`.

### Pre-condicoes
- Banco disponivel.
- Nome de usuario ainda nao utilizado.
- Body JSON valido para `CreateUserRequest`.

### Fluxo Tecnico Detalhado
1. Cliente envia `POST /api/v1/security/create`.
2. FastAPI valida schema de entrada.
3. FastAPI resolve `session` via dependencia do `db_client`.
4. Endpoint consulta existencia previa por `User.name`.
5. Se nao existir, gera hash da senha.
6. Instancia `User(name, password_hash, setor)`.
7. Persiste com `add`, confirma com `commit` e recarrega com `refresh`.
8. Retorna `CreateUserResponse(id, user, setor)`.
9. Dependencia encerra e fecha a sessao.

### Entrada Esperada
```json
{
  "user": "usuario",
  "password": "senha",
  "setor": "RH"
}
```

### Saida Esperada
- Status: `201 Created`
- Body:
```json
{
  "id": 1,
  "user": "usuario",
  "setor": "RH"
}
```

## Caso de Uso 2: Usuario ja existe
### Fluxo de Excecao
1. Consulta inicial encontra registro com mesmo `name`.
2. Endpoint lanca `HTTPException` e nao persiste novo usuario.

### Saida de Erro
- Status: `400 Bad Request`
- Body detail: `Usuario ja existe`

## Caso de Uso 3: Payload invalido
### Fluxo de Excecao
1. Campos obrigatorios ausentes ou formato invalido.
2. Requisicao barrada por validacao de schema.

### Saida de Erro
- Status: `422 Unprocessable Entity`

## Observacoes Operacionais
- Esta rota nao exige autenticacao no estado atual.
- Nao ha controle transacional explicito de rollback para erros entre `add` e `commit`.
