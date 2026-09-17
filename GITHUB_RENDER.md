# GUIA RÁPIDO — GITHUB → RENDER → IPHONE

## 1. GitHub

Crie um repositório novo e coloque **o conteúdo desta pasta na raiz**.

Não envie o ZIP como substituto da estrutura do projeto e não crie uma pasta extra como:

```text
meu-repo/LosCollector_final_css/app.py
```

O correto é:

```text
meu-repo/app.py
meu-repo/Dockerfile
meu-repo/render.yaml
```

Se o upload pelo navegador não preservar pastas, use GitHub Desktop ou Git para enviar a pasta inteira mantendo a estrutura.

## 2. Render

No Render:

1. `New` → `Blueprint`.
2. Conecte o repositório.
3. Selecione o `render.yaml` da raiz.
4. Preencha as variáveis secretas solicitadas.
5. Faça o deploy.

O web service usa Docker e instala FFmpeg durante o build.

## 3. Variáveis

Preencha:

```text
ADMIN_EMAIL=seu-email
ADMIN_INITIAL_PASSWORD=sua-senha-inicial
TMDB_API_KEY=sua-chave-tmdb
DATABASE_URL=sua-url-postgresql
```

`SECRET_KEY` pode ser gerado pelo próprio Blueprint.

## 4. Acesso

Depois que o Render informar a URL, abra a URL no Safari do iPhone.

O login aparece antes do dashboard.

## 5. Monitoramento

O `scheduler.py` fica separado do Safari. O Render Cron chama:

```text
python scheduler.py
```

a cada 30 minutos.

Esse Cron é um serviço pago no Render; o projeto está configurado para `0.5c-512mb`.
