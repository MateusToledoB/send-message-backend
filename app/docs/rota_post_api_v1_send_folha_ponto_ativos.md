# Documentacao de Fluxo por Caso de Uso

## Identificacao da Rota
- Metodo: `POST`
- Caminho: `/api/v1/send_folha_ponto_ativos`
- Modulo: `app/api/v1/endpoints/send_folha_ponto_ativos.py`
- Funcao: `send_folha_ponto_ativos`
- Tipo de handler: assincrono (`async def`)

## Dependencias e Injeções (FastAPI)
- `payload: FolhaPontoUploadRequest = Depends(FolhaPontoUploadRequest.as_form)`
  - Extrai arquivo e campos do formulario:
  - `file` (`UploadFile`)
  - `column_name`
  - `column_month`
  - `column_contact`
  - `template_type` (default `FP`)
- `current_user: User = Depends(get_current_user)`
  - Resolve autenticacao por cadeia de tokens:
  - Bearer (`Authorization`)
  - Cookie configurado (`settings.JWT_COOKIE_NAME`)
  - Cookie legados `access_token` e `token_acess`
- `session: Session = Depends(db_client.get_session)`
  - Sessao SQLAlchemy aberta por request e fechada no final.

## Cadeia de Componentes Executada
- Endpoint -> `FolhaPontoAtivosService(session)`
- `FolhaPontoAtivosService.loop_folha_ponto_ativos(...)`
- Criacao inicial de `MessageRequest` com `status="requested"`
- `xlsx_to_dataframe(file)`
- Loop de linhas -> `RabbitMQ.publish(settings.RABBITMQ_QUEUE_FOLHA_PONTO_ATIVOS, payload)`
- Atualizacao de `published_messages` ao final da publicacao

## Caso de Uso 1: Processar planilha e publicar mensagens
### Objetivo
Transformar cada linha da planilha em payload e publicar na fila para envio posterior.

### Pre-condicoes
- Token JWT valido (header bearer ou cookie aceito por `get_current_user`).
- Arquivo `.xlsx` valido.
- Colunas informadas existem na planilha.
- Banco e RabbitMQ disponiveis.

### Fluxo Tecnico Detalhado
1. Cliente envia `POST /api/v1/send_folha_ponto_ativos` como multipart.
2. FastAPI resolve `FolhaPontoUploadRequest.as_form` e cria objeto unico com arquivo + campos de formulario.
3. FastAPI resolve `get_current_user`:
4. Decodifica JWT com `JWT_SECRET_KEY` e `JWT_ALGORITHM`.
5. Le `sub` do token e carrega `User` na sessao.
6. FastAPI resolve `session` via `db_client.get_session`.
7. Endpoint instancia `FolhaPontoAtivosService` com a sessao.
8. Servico chama `xlsx_to_dataframe(file)`.
9. `xlsx_to_dataframe` valida extensao `.xlsx` e le arquivo via `pandas.read_excel`/`openpyxl`.
10. Antes do processamento da planilha, servico cria `MessageRequest` com:
11. `published_messages=0`, `send_messages=0`, `status=\"requested\"`.
12. Para cada linha, servico monta payload com:
13. `name`, `month_folha_ponto`, `whatsapp_number`, `user_id`, `template_type`, `message_request_id`.
14. Cada payload e publicado em `settings.RABBITMQ_QUEUE_FOLHA_PONTO_ATIVOS`.
15. Ao final, servico atualiza `published_messages` com total publicado.
16. Se total publicado for `0`, servico finaliza com `status=\"finish\"`.
17. Endpoint retorna resumo com IDs e contagem.
18. No final da request, sessao de banco e fechada pela dependencia.

### Entrada Esperada
- Content-Type: `multipart/form-data`
- Partes:
  - `file`: arquivo `.xlsx`
  - `column_name`: nome da coluna de nome
  - `column_month`: nome da coluna de competencia/mes
  - `column_contact`: nome da coluna de contato
  - `template_type`: opcional

### Saida Esperada (com publicacoes)
- Status: `200 OK`
- Body contendo:
  - `message_request_id`
  - `published_messages`
  - `send_messages` (inicialmente `0`)
  - `status` (`requested`)
  - `template_type`
  - `created_at`

## Caso de Uso 2: Planilha sem linhas publicadas
### Fluxo Alternativo
1. DataFrame e processado sem iteracoes publicadas.
2. `MessageRequest` ja existe e recebe `published_messages=0`.
3. Servico atualiza `status` para `finish`.

### Saida Esperada
- Status: `200 OK`
- Body com `published_messages: 0`, `send_messages: 0`, `status: "finish"`.

## Caso de Uso 3: Falha de autenticacao
### Fluxo de Excecao
1. Token/cookie ausente, invalido, expirado ou usuario nao encontrado.
2. `get_current_user` lanca `HTTPException`.

### Saida de Erro
- Status: `401 Unauthorized`
- Detail padrao: `Could not validate credentials`

## Caso de Uso 4: Arquivo invalido
### Fluxo de Excecao
1. Arquivo nao termina com `.xlsx`.
2. `xlsx_to_dataframe` lanca `HTTPException`.

### Saida de Erro
- Status: `400 Bad Request`
- Detail: `Arquivo deve ser .xlsx`

## Caso de Uso 5: Falhas de infraestrutura
### Fluxo de Excecao
- Erro na leitura do excel, no publish RabbitMQ ou no commit de banco interrompe fluxo.

### Saida de Erro
- Sem tratamento local especifico no endpoint/servico para essas excecoes.
- FastAPI responde com erro interno (`500`) quando nao ha captura especifica.

## Observacoes Operacionais
- Rota nao envia para Meta diretamente; apenas publica na fila.
- A entrega final WhatsApp e responsabilidade do worker `MetaQueueWorker`.
