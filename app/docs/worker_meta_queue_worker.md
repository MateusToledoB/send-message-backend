# Documentacao de Fluxo por Caso de Uso

## Identificacao do Worker
- Nome: `MetaQueueWorker`
- Modulo: `app/workers/meta_queue_worker.py`
- Filas de entrada:
  - `settings.RABBITMQ_QUEUE_FOLHA_PONTO_ATIVOS`
  - `settings.RABBITMQ_QUEUE_FOLHA_PONTO_INATIVOS`
  - `settings.RABBITMQ_QUEUE_FOLHA_PONTO_ATIVOS_TORRE`
  - `settings.RABBITMQ_QUEUE_VAGAS`
- Saida de contingencia: fila `settings.RABBITMQ_QUEUE_FOLHA_PONTO_BACKUP`
- Modo de execucao: `asyncio.run(main())`

## Dependencias Internas
- `RabbitMQ` (`app/infra/rabbitmq/rabbitmq_client.py`)
  - `connect()`, `ensure_queue()`, `publish()`.
- `MetaRequestService` (`app/services/meta_request_service.py`)
  - `send_template_message(payload)` para chamada HTTP da Meta API.
- `DbClient` + modelo `MessageRequest`
  - Atualiza contabilizacao de envios com sucesso por `message_request_id`.
- Configuracoes `settings`
  - Filas, URL da Meta e token.

## Ciclo de Vida do Worker
1. `main()` instancia `MetaQueueWorker`.
2. `start()` garante existencia de todas as filas configuradas no map `queue_handlers`.
3. `start()` cria um consumidor assíncrono por fila (`_consume_queue`).
4. Consumidores rodam em paralelo com `asyncio.gather`.
5. Para cada mensagem recebida, chama `_handle_message(queue_name, message)`.

## Caso de Uso 1: Consumir e enviar para Meta com sucesso
### Objetivo
Transformar mensagem da fila em payload de template WhatsApp e concluir processamento.

### Pre-condicoes
- RabbitMQ acessivel e fila com mensagens.
- Mensagem JSON contem `whatsapp_number`, `name`, `month_folha_ponto`.
- `WHATSAPP_TOKEN` configurado.

### Fluxo Tecnico Detalhado
1. `_handle_message` decodifica `message.body` de bytes para JSON dict.
2. Worker escolhe handler pelo nome da fila (`_build_meta_payload`).
3. Handler valida payload e monta template correspondente.
4. `MetaRequestService.send_template_message` prepara body HTTP:
5. `messaging_product=whatsapp`, `to=55{whatsapp_number}`, `language=pt_BR`, `components`.
6. Chama `POST settings.META_MESSAGES_URL` via `httpx.AsyncClient`.
7. `response.raise_for_status()` valida sucesso HTTP.
8. Worker valida se retorno contem confirmacao em `messages`.
9. Worker incrementa `send_messages` no `MessageRequest` relacionado ao payload.
10. Quando `send_messages >= published_messages`, worker atualiza status para `finish`.
11. Worker executa `message.ack()`.
12. Loga sucesso com fila, template e `user_id` do payload original.

### Resultado Esperado
- Mensagem removida da fila principal.
- Entrega solicitada para API da Meta concluida com sucesso HTTP.

## Caso de Uso 2: Falha no processamento principal e envio para backup
### Objetivo
Evitar perda de mensagem quando houver erro no envio principal.

### Fluxo de Excecao
1. Erro ocorre em parse JSON, validacao do payload, configuracao Meta ou request HTTP.
2. Worker entra no `except` principal e chama `_publish_backup(queue_name, payload, raw_body, error)`.
3. `_publish_backup` monta payload de backup:
4. Se parse falhou, inclui `raw_body` decodificado + `error`.
5. Se parse funcionou, reutiliza payload original + `error`.
6. Publica em `settings.RABBITMQ_QUEUE_FOLHA_PONTO_BACKUP`.
7. Ao conseguir publicar backup, worker faz `message.ack()` da mensagem original.

### Resultado Esperado
- Mensagem principal nao reprocessa imediatamente.
- Registro de contingencia disponivel na fila de backup.

## Caso de Uso 3: Falha tambem no publish de backup
### Fluxo de Excecao Critica
1. Ocorre erro no fluxo principal.
2. Ocorre novo erro ao chamar `_publish_backup`.
3. Worker executa `message.nack(requeue=True)`.

### Resultado Esperado
- Mensagem volta para fila principal para tentativa futura.
- Logs de excecao principal e de backup sao emitidos.

## Validacoes e Regras de Montagem de Payload
- Filas de folha ponto usam validacao:
  - `whatsapp_number`
  - `name`
  - `month_folha_ponto`
- Ausencia de qualquer um desses campos gera `ValueError`.
- Mapeamento de template por fila:
  - `RABBITMQ_QUEUE_FOLHA_PONTO_ATIVOS` -> `folha_ponto_ativo`
  - `RABBITMQ_QUEUE_FOLHA_PONTO_INATIVOS` -> `folha_ponto_inativo`
  - `RABBITMQ_QUEUE_FOLHA_PONTO_ATIVOS_TORRE` -> `folha_ponto_ativo_torre`
- Fila `RABBITMQ_QUEUE_VAGAS` usa `template_type` do payload (default `vagas`) e monta parametros dinamicos.
- Payload de fila tambem deve carregar `message_request_id` para contabilizacao no banco.

## Comportamento de Confiabilidade
- Publicacao RabbitMQ usa mensagem persistente (`delivery_mode=PERSISTENT`).
- Consumo confirma (`ack`) apenas apos sucesso do envio Meta ou sucesso no fallback backup.
- Requeue so ocorre quando falha principal e falha de fallback acontecem no mesmo ciclo.
