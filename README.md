# LOS COLLECTOR

**Collect • Organize • Monitor**

Plataforma privada para coletar, organizar, diagnosticar, monitorar, mesclar e exportar playlists M3U/M3U8 de fontes públicas/autorizadas, com o **LOS COLLECTOR STUDIO** para materiais promocionais de filmes e séries.

## O que já está no projeto

- Login privado com senha armazenada por hash e sessão protegida.
- Alteração de senha pelo painel.
- Dashboard com fontes, conteúdos, status e erros.
- Coleta de M3U/M3U8 com crawler limitado ao mesmo domínio.
- Parser de `#EXTM3U` / `#EXTINF`, grupos, logos e atributos.
- Deduplicação e classificação em canais, filmes, séries e outros.
- Biblioteca com filtros e exportação/mesclagem M3U.
- Diagnóstico de URLs com timeout e isolamento por item.
- Monitoramento por `scheduler.py` preparado para Render Cron.
- LOS COLLECTOR STUDIO com TMDB e renderização real por FFmpeg.
- Formatos 9:16, 16:9 e personalizado.
- Docker + FFmpeg + configuração Render.
- SQLite para desenvolvimento e PostgreSQL por `DATABASE_URL` em produção.
- Interface responsiva com CSS próprio, pensada para iPhone/Safari.

## Segurança

O projeto trabalha somente com conteúdo público/autorizado. Ele não tenta contornar login, CAPTCHA, DRM, paywall ou outros controles de acesso.

**Nunca envie para o GitHub:** `.env`, senha real, chave TMDB, tokens, banco SQLite, vídeos, uploads ou arquivos gerados. O `.gitignore` já cobre esses itens.

## Configuração local

Requisitos: Python 3.12+ e FFmpeg.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

No `.env`, configure:

- `ADMIN_EMAIL` — e-mail do administrador.
- `ADMIN_INITIAL_PASSWORD` — senha inicial privada.
- `TMDB_API_KEY` — chave do TMDB.
- `SECRET_KEY` — segredo forte da aplicação.

Sem `DATABASE_URL`, o sistema usa SQLite em `data/loscollector.db`.

## GitHub + Render

A raiz deste projeto já está preparada para ser a **raiz do repositório**. Não coloque `LosCollector_final_css/` ou outra pasta intermediária acima dos arquivos.

Na raiz do GitHub devem aparecer, entre outros:

```text
app.py
requirements.txt
Dockerfile
render.yaml
.env.example
.gitignore
database.py
m3u_engine.py
collector.py
checker.py
scheduler.py
studio.py
auth.py
assets/
data/
media/
tests/
```

No Render, use **New → Blueprint** e conecte o repositório que contém o `render.yaml`. O Blueprint configura o web service e o cron. O web service está no plano Free para teste; o Cron de monitoramento usa `0.5c-512mb`, pois Cron Jobs não possuem plano Free. O cron tem cobrança mínima de US$ 1/mês segundo a documentação atual do Render.

Configure no Render:

- `ADMIN_EMAIL`
- `ADMIN_INITIAL_PASSWORD`
- `TMDB_API_KEY`
- `DATABASE_URL`
- `SECRET_KEY` (o Blueprint gera automaticamente)

### Persistência

O filesystem do Render é efêmero por padrão. Para dados que precisam sobreviver a reinícios/deploys, use PostgreSQL para dados relacionais e armazenamento persistente/externo para arquivos de vídeo e uploads. O projeto já aceita PostgreSQL por `DATABASE_URL`.

## Primeiro acesso

Use no Render o mesmo e-mail configurado em `ADMIN_EMAIL` e a senha que você colocar em `ADMIN_INITIAL_PASSWORD`. Depois de entrar, altere a senha em **Configurações**.

## Testes locais

```bash
python -m compileall -q .
python -m pytest -q
```

O pacote preparado passou nos testes automatizados disponíveis no ambiente e teve o renderizador FFmpeg testado com um vídeo de demonstração local. Integrações externas como TMDB e o deploy real no Render precisam ser validadas no ambiente com as respectivas credenciais.
