import os, json, tempfile, html
from pathlib import Path
from datetime import timedelta
import streamlit as st
from dotenv import load_dotenv
from database import init_db, seed_admin, get_session, User, Source, Content, StudioProject, utcnow
from auth import verify_password, hash_password
from collector import scan_source
from m3u_engine import deduplicate, export_m3u, M3UItem
from checker import check_url
from studio import tmdb_search, tmdb_details, download_image, render_video, PLATFORM_FORMATS

load_dotenv(); init_db(); seed_admin()
MEDIA=Path(os.getenv('MEDIA_DIR','media')); (MEDIA/'uploads').mkdir(parents=True,exist_ok=True); (MEDIA/'generated').mkdir(parents=True,exist_ok=True)

st.set_page_config(page_title='LOS COLLECTOR',page_icon='👑',layout='wide',initial_sidebar_state='expanded')

CSS='''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Orbitron:wght@500;600;700;800&display=swap');
:root{--bg:#020712;--panel:#071326;--line:#123b68;--blue:#0b7dff;--cyan:#18c8ff;--violet:#5b20ff;--text:#edf7ff;--muted:#7e9ab6}
html,body,[class*="css"]{font-family:Inter,sans-serif}.stApp{background:radial-gradient(900px 500px at 65% -5%,rgba(0,105,255,.22),transparent 65%),radial-gradient(700px 500px at 100% 25%,rgba(0,210,255,.08),transparent 60%),linear-gradient(180deg,#020712 0%,#030a16 45%,#020610 100%);color:var(--text)}
[data-testid="stHeader"]{background:rgba(2,7,18,.72);backdrop-filter:blur(14px);border-bottom:1px solid rgba(28,103,170,.24)}.block-container{padding:1.15rem 1.35rem 3.5rem;max-width:1500px}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#030b18 0%,#020813 100%);border-right:1px solid #102d4c;min-width:245px;max-width:245px}section[data-testid="stSidebar"]>div{padding:18px 14px}
section[data-testid="stSidebar"] .stRadio>div{gap:5px}section[data-testid="stSidebar"] label{border:1px solid transparent;border-radius:10px;padding:7px 10px!important;transition:.2s;background:transparent}section[data-testid="stSidebar"] label:hover{background:rgba(17,105,190,.12);border-color:rgba(35,151,255,.2)}section[data-testid="stSidebar"] label[data-checked="true"]{background:linear-gradient(90deg,rgba(11,125,255,.38),rgba(13,57,105,.2));border-color:#126fd1;box-shadow:inset 3px 0 0 #19c7ff,0 0 18px rgba(0,130,255,.12)}section[data-testid="stSidebar"] label p{font-size:12px!important;color:#c4d7e9!important}
.brand{font-family:Orbitron,sans-serif;letter-spacing:-1px;font-weight:800;font-size:25px;color:#fff}.brand span{color:var(--cyan)}.slogan{color:#78a8ca;font-size:10px;letter-spacing:1.4px;margin-top:3px}.crown{font-size:30px;color:#1fcfff;margin-right:8px;text-shadow:0 0 12px #08aaff,0 0 30px rgba(0,160,255,.45)}.sidebar-brand{text-align:center;padding:4px 0 17px;border-bottom:1px solid #102c48;margin-bottom:12px}.sidebar-brand .brand{font-size:22px}.sidebar-brand .slogan{font-size:9px}.sidebar-section{font-size:9px;letter-spacing:2px;color:#557894;font-weight:800;margin:14px 9px 7px;text-transform:uppercase}
.profile-mini{margin:20px 0 2px;border:1px solid #12385d;border-radius:13px;background:linear-gradient(145deg,#061326,#030914);padding:13px;text-align:center;box-shadow:0 0 28px rgba(0,105,255,.08)}.profile-mini .vortex{font-family:Orbitron;font-size:15px;font-weight:800;color:#fff}.profile-mini .vortex span{color:#12caff}.profile-mini .tiny{font-size:8px;color:#6d8ba6;margin-top:3px}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:15px;border-bottom:1px solid rgba(18,71,116,.42);padding:0 0 13px;margin-bottom:20px}.top-search{flex:1;max-width:540px;background:#061224;border:1px solid #143b61;border-radius:12px;height:42px;display:flex;align-items:center;padding:0 14px;color:#7290ab;font-size:12px}.top-icons{display:flex;gap:18px;color:#9db8d0;font-size:18px}.account-chip{display:flex;align-items:center;gap:9px;font-size:11px;color:#e9f5ff}.account-chip .avatar{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(145deg,#0879ff,#0bd0ff);box-shadow:0 0 18px rgba(0,166,255,.25)}
.hero{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;margin-bottom:17px}.hero h1{font-size:28px;margin:0;font-weight:800;letter-spacing:-.7px}.hero h1 span{color:var(--cyan)}.hero p{margin:5px 0 0;color:#86a4bf;font-size:12px}.hero-art{min-width:350px;border-radius:18px;border:1px solid #124579;background:radial-gradient(circle at 70% 45%,rgba(0,163,255,.18),transparent 48%),linear-gradient(145deg,#061426,#020713);padding:14px 20px;display:flex;align-items:center;gap:14px;box-shadow:0 0 30px rgba(0,118,255,.1)}.hero-art .crown{font-size:36px}.hero-art strong{font-family:Orbitron;font-size:18px}.hero-art small{display:block;color:#7998b3;font-size:9px;letter-spacing:1px;margin-top:4px}
.card{background:linear-gradient(145deg,rgba(8,24,45,.97),rgba(3,11,23,.98));border:1px solid #123d69;border-radius:13px;padding:17px;box-shadow:inset 0 1px rgba(255,255,255,.025),0 10px 35px rgba(0,0,0,.18);margin-bottom:13px}.metric{font-family:Orbitron,sans-serif;font-size:25px;font-weight:800;color:#fff;margin-top:5px}.label{font-size:9px;color:#8aa6be;letter-spacing:1.3px;font-weight:700}.small{font-size:10px;color:#7795af}.glow{color:#eaf9ff;text-shadow:0 0 13px rgba(25,202,255,.2)}.metric-card{position:relative;overflow:hidden;min-height:103px}.metric-card:after{content:"";position:absolute;right:-22px;bottom:-34px;width:95px;height:95px;border:1px solid rgba(23,191,255,.15);border-radius:50%}.metric-icon{width:37px;height:37px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(145deg,#075bd0,#062b66);border:1px solid #1c8be3;color:#6beaff;box-shadow:0 0 18px rgba(0,134,255,.16);float:left;margin-right:12px;font-size:16px}
.panel-title{font-weight:800;font-size:13px;color:#f2f8ff;margin-bottom:10px}.panel-title span{float:right;color:#20c9ff;font-size:9px;font-weight:600}.section-heading{font-family:Orbitron;font-size:15px;letter-spacing:.5px;margin:5px 0 12px;color:#fff}.section-heading span{color:#1ecbff}
.stButton>button,button[kind="primary"]{border-radius:9px!important;border:1px solid #1a93dc!important;min-height:42px!important;background:linear-gradient(100deg,#079ce9,#175cff)!important;color:white!important;font-weight:800!important;font-size:11px!important;box-shadow:0 0 22px rgba(0,129,255,.18)!important}.stButton>button:hover{filter:brightness(1.12);transform:translateY(-1px)}
.stTextInput input,.stTextArea textarea,.stNumberInput input,.stSelectbox>div>div,.stMultiSelect>div>div{background:#061224!important;color:#eaf6ff!important;border:1px solid #153d63!important;border-radius:9px!important;font-size:12px!important}.stTextInput label,.stTextArea label,.stNumberInput label,.stSelectbox label,.stMultiSelect label{font-size:9px!important;color:#7f9bb5!important;text-transform:uppercase;letter-spacing:1px}.stTabs [data-baseweb="tab-list"]{gap:5px;background:transparent}.stTabs [data-baseweb="tab"]{background:#061224;border:1px solid #113656;border-radius:8px;color:#7592ab;padding:8px 12px;font-size:10px}.stTabs [aria-selected="true"]{color:#4de5ff!important;border-color:#1b7fbe!important;background:#09203a!important}
.status{display:inline-block;border-radius:999px;padding:4px 9px;font-size:9px;font-weight:800;letter-spacing:.7px;background:#102335;border:1px solid #183b58}.ok{color:#48f2a2}.err{color:#ff6884}.warn{color:#ffd76a}.stAlert{border-radius:10px!important;border:1px solid #18466d!important;background:#061426!important}.stProgress>div>div>div{background:linear-gradient(90deg,#08a8ff,#5c3cff)}[data-testid="stFileUploaderDropzone"]{background:#061224!important;border:1px dashed #1b5d91!important;border-radius:10px!important}
.login{max-width:430px;margin:8vh auto}.login-shell{padding:34px;border:1px solid #174b78;border-radius:20px;background:linear-gradient(145deg,rgba(7,22,42,.98),rgba(2,8,17,.99));box-shadow:0 0 70px rgba(0,102,255,.13)}.login .brand{text-align:center;display:block;font-size:28px}.login .slogan{text-align:center}.login h3{font-family:Orbitron;letter-spacing:1px;text-align:center;font-size:13px}.divider{height:1px;background:#153451;margin:18px 0}.footer{border-top:1px solid #102c48;margin-top:20px;padding-top:9px;color:#506d87;font-size:8px;display:flex;justify-content:space-between}
@media(max-width:900px){section[data-testid="stSidebar"]{min-width:220px;max-width:220px}.hero-art{min-width:260px}.block-container{padding:1rem .9rem 3rem}}@media(max-width:700px){section[data-testid="stSidebar"]{min-width:0;max-width:290px}.block-container{padding:.75rem .65rem 3rem}.topbar{margin-bottom:13px}.top-icons{display:none}.hero{display:block}.hero-art{min-width:0;margin-top:12px}.hero h1{font-size:23px}.metric{font-size:22px}.card{padding:14px}.stButton>button{width:100%;min-height:48px!important}.stTabs [data-baseweb="tab"]{padding:8px 7px;font-size:9px}}
</style>'''
st.markdown(CSS,unsafe_allow_html=True)

def urlparse_safe(url):
    try:
        from urllib.parse import urlparse
        p=urlparse(url); return p.netloc or 'Nova fonte'
    except Exception: return 'Nova fonte'

def logo_header():
    st.markdown('<div><span class="crown">♛</span><span class="brand">LOS <span>COLLECTOR</span></span><div class="slogan">Collect • Organize • Monitor</div></div>',unsafe_allow_html=True)

def card(label,value,sub=''):
    st.markdown(f'<div class="card"><div class="label">{label}</div><div class="metric glow">{value}</div><div class="small">{sub}</div></div>',unsafe_allow_html=True)

def logged(): return bool(st.session_state.get('user_id'))

def login():
    st.markdown('<div class="login"><div class="login-shell">',unsafe_allow_html=True); logo_header(); st.markdown('<div class="divider"></div>',unsafe_allow_html=True)
    st.markdown('### ACESSO PRIVADO')
    with st.form('login'):
        email=st.text_input('E-mail',value=os.getenv('ADMIN_EMAIL',''))
        pw=st.text_input('Senha',type='password')
        if st.form_submit_button('ENTRAR',use_container_width=True):
            with get_session() as db:
                u=db.query(User).filter_by(email=email.strip().lower()).first()
                if u and verify_password(pw,u.password_hash): st.session_state.user_id=u.id; st.session_state.email=u.email; st.rerun()
                else: st.error('E-mail ou senha inválidos.')
    st.markdown('</div></div>',unsafe_allow_html=True)

if not logged(): login(); st.stop()

with st.sidebar:
    st.markdown('<div class="sidebar-brand"><div class="crown">♛</div><div class="brand">Los<span>Collector</span></div><div class="slogan">Sua mídia, do seu jeito.</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">COLETOR</div>',unsafe_allow_html=True)
    nav=st.radio('NAVEGAÇÃO',['⌂  Início','⌁  Coletor de URLs','⇩  Importar M3U/M3U8','☷  Minhas Playlists','▣  Canais','▤  Filmes','▥  Séries','♧  Mesclar Fontes','⊙  Diagnóstico','⇧  Exportar M3U','◈  Banco de Dados','♛  LosCollector Studio','⚙  Configurações'],label_visibility='collapsed')
    mapping={'⌂  Início':'INÍCIO','⌁  Coletor de URLs':'FONTES','⇩  Importar M3U/M3U8':'FONTES','☷  Minhas Playlists':'BIBLIOTECA','▣  Canais':'CANAIS','▤  Filmes':'FILMES','▥  Séries':'SÉRIES','♧  Mesclar Fontes':'MESCLAR','⊙  Diagnóstico':'DIAGNÓSTICO','⇧  Exportar M3U':'EXPORTAR','◈  Banco de Dados':'BANCO','♛  LosCollector Studio':'STUDIO','⚙  Configurações':'CONFIGURAÇÕES'}
    page=mapping[nav]
    st.markdown('<div class="sidebar-section">CONTA</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="small" style="padding:5px 9px;overflow:hidden;text-overflow:ellipsis">{html.escape(st.session_state.email)}</div>',unsafe_allow_html=True)
    if st.button('SAIR / LOGOUT',use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.markdown('<div class="profile-mini"><div class="crown">♛</div><div class="vortex">VORTEX<span>PLAYER</span> TV</div><div class="tiny">Sua TV, sem limites.</div></div>',unsafe_allow_html=True)

st.markdown(f'<div class="topbar"><div class="top-search">⌕&nbsp;&nbsp; Pesquise filmes, séries, canais, etc...</div><div class="top-icons">☾　♧</div><div class="account-chip"><div class="avatar">♟</div><div><b>Los</b><br><span class="small">Administrador</span></div>⌄</div></div>',unsafe_allow_html=True)
logo_header()

with get_session() as db:
    if page=='INÍCIO':
        sources=db.query(Source).count(); contents=db.query(Content).count(); online=db.query(Content).filter(Content.status=='ONLINE').count(); errors=db.query(Content).filter(Content.status.in_(['ERRO','TIMEOUT'])).count()
        st.markdown('<div class="hero"><div><h1>Bem-vindo, <span>Los</span> ♛</h1><p>Coleta, organize e transforme sua mídia em uma experiência única.</p></div><div class="hero-art"><span class="crown">♛</span><div><strong>Los<span style="color:#20c9ff">Collector</span></strong><small>MAIS QUE UM COLETOR, É O SEU ESTÚDIO DE CONTEÚDO.</small></div></div></div>',unsafe_allow_html=True)
        cols=st.columns(4)
        metrics=[('◈','CANAIS',db.query(Content).filter(Content.category=='CANAIS').count(),'ativos'),('▣','FILMES',db.query(Content).filter(Content.category=='FILMES').count(),'disponíveis'),('▤','SÉRIES',db.query(Content).filter(Content.category=='SÉRIES').count(),'disponíveis'),('☷','PLAYLISTS',sources,'criadas')]
        for c,(ico,l,v,sub) in zip(cols,metrics):
            with c: st.markdown(f'<div class="card metric-card"><div class="metric-icon">{ico}</div><div class="label">{l}</div><div class="metric">{v:,}</div><div class="small">{sub}</div></div>',unsafe_allow_html=True)
        c1,c2=st.columns([1.2,1])
        with c1:
            st.markdown('<div class="card"><div class="panel-title">▰ Coletor de URLs</div><div class="small" style="margin-bottom:10px">Colete listas M3U/M3U8 de fontes públicas/autorizadas.</div>',unsafe_allow_html=True)
            quick=st.text_input('URL',placeholder='Colete uma URL de lista M3U/M3U8...',label_visibility='collapsed')
            if st.button('COLETAR',type='primary',use_container_width=True):
                if quick.strip(): st.session_state['quick_collect_url']=quick.strip(); st.session_state['quick_go']=True; st.rerun()
                else: st.warning('Informe uma URL.')
            q1,q2,q3=st.columns(3)
            with q1:
                if st.button('⇩ Importar M3U/M3U8',use_container_width=True): st.session_state['nav_to']='FONTES'; st.rerun()
            with q2:
                if st.button('⊙ Verificar URL',use_container_width=True): st.session_state['nav_to']='DIAGNÓSTICO'; st.rerun()
            with q3:
                if st.button('♲ Limpar',use_container_width=True): st.session_state['quick_collect_url']=''; st.rerun()
            st.markdown('</div>',unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="card"><div class="panel-title">Últimas Coletas <span>Ver todas →</span></div>',unsafe_allow_html=True)
            latest=db.query(Source).order_by(Source.id.desc()).limit(4).all()
            if latest:
                for src in latest: st.markdown(f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #0e2944"><span><b style="font-size:10px">●　{html.escape(src.name)}</b><br><span class="small">{src.content_count} conteúdos</span></span><span class="small">{html.escape(src.status)}</span></div>',unsafe_allow_html=True)
            else: st.markdown('<div class="small">Nenhuma fonte coletada ainda.</div>',unsafe_allow_html=True)
            st.markdown('</div>',unsafe_allow_html=True)
        st.markdown('<div class="card"><div class="panel-title">♛ LosCollector Studio <span>NOVO</span></div><div class="small">Transforme seus filmes e séries em materiais promocionais profissionais.</div></div>',unsafe_allow_html=True)
        st.markdown('<div class="section-heading">VISÃO GERAL DO SISTEMA</div>',unsafe_allow_html=True)
        a,b,c=st.columns(3)
        with a: st.markdown(f'<div class="card"><div class="label">CONTEÚDOS</div><div class="metric glow">{contents:,}</div><div class="small">Itens na biblioteca</div></div>',unsafe_allow_html=True)
        with b: st.markdown(f'<div class="card"><div class="label">ONLINE</div><div class="metric" style="color:#48f2a2">{online:,}</div><div class="small">Último diagnóstico</div></div>',unsafe_allow_html=True)
        with c: st.markdown(f'<div class="card"><div class="label">COM ERRO</div><div class="metric" style="color:#ff6884">{errors:,}</div><div class="small">Erros e timeouts</div></div>',unsafe_allow_html=True)
        st.markdown('<div class="footer"><span>LosCollector © 2026. Todos os direitos reservados.</span><span>Feito com ♥ por Los　•　VortexPlayerTV</span><span>Versão 1.0.0</span></div>',unsafe_allow_html=True)
    elif page=='FONTES':
        st.markdown('## FONTES'); st.caption('Colete somente recursos públicos ou para os quais você tenha autorização.')
        url=st.text_input('URL DA FONTE',placeholder='https://exemplo.com')
        c1,c2=st.columns([2,1])
        with c1: max_pages=st.number_input('Páginas máximas',1,200,int(os.getenv('COLLECTOR_MAX_PAGES','30')))
        with c2: timeout=st.number_input('Timeout (s)',3,60,int(os.getenv('COLLECTOR_TIMEOUT','12')))
        if st.button('ESCANEAR',type='primary',use_container_width=True):
            progress=st.progress(0); status=st.empty()
            def cb(done,total,current,found): progress.progress(min(done/total,1.0)); status.info(f'Varredura {done}/{total} • {found} playlists • {current[:90]}')
            try:
                res=scan_source(url,int(max_pages),int(timeout),cb); st.session_state['scan_result']=res; progress.progress(1); status.success(f"{len(res['playlist_urls'])} playlist(s) encontrada(s) • {len(res['items'])} item(ns)")
            except Exception as e: st.error(str(e))
        res=st.session_state.get('scan_result')
        if res:
            st.markdown(f'<div class="card"><b>RESULTADO</b><br><span class="small">Páginas: {res["pages_scanned"]} • Playlists: {len(res["playlist_urls"])} • Conteúdos: {len(res["items"])}</span></div>',unsafe_allow_html=True)
            name=st.text_input('Nome para salvar',value=urlparse_safe(url))
            if st.button('IMPORTAR PARA BIBLIOTECA',use_container_width=True):
                src=db.query(Source).filter_by(url=url.strip()).first()
                if not src: src=Source(name=name or 'Fonte',url=url.strip(),status='ONLINE',last_checked=utcnow(),content_count=0); db.add(src); db.flush()
                items=deduplicate(res['items']); existing={(c.url.lower(),c.title.lower()) for c in src.contents}; added=0
                for it in items:
                    if (it.url.lower(),it.title.lower()) in existing: continue
                    db.add(Content(title=it.title,url=it.url,category=it.category,group_name=it.group,logo=it.logo,attributes_json=json.dumps(it.attributes or {}),source_id=src.id)); added+=1
                src.content_count=len(src.contents)+added; src.new_contents=added; db.commit(); st.success(f'{added} conteúdo(s) importado(s).')
            for p in res['playlist_urls'][:20]: st.code(p)
        st.divider(); st.markdown('### FONTES SALVAS')
        for src in db.query(Source).order_by(Source.id.desc()).all():
            c1,c2,c3,c4=st.columns([3,1.3,1.5,1.2])
            with c1: st.markdown(f'**{html.escape(src.name)}**<br><span class="small">{html.escape(src.url)}</span>',unsafe_allow_html=True)
            with c2: st.write(src.status)
            with c3: st.write(f'{src.content_count} itens')
            with c4: st.write(f'+{src.new_contents} novos')
    elif page in ('BIBLIOTECA','CANAIS','FILMES','SÉRIES','EXPORTAR'):
        st.markdown('## BIBLIOTECA')
        default_filter = page if page in ('CANAIS','FILMES','SÉRIES') else 'TODOS'
        filt=st.selectbox('FILTRO',['TODOS','CANAIS','FILMES','SÉRIES','ERROS'],index=['TODOS','CANAIS','FILMES','SÉRIES','ERROS'].index(default_filter))
        q=st.text_input('Pesquisar título / URL')
        query=db.query(Content)
        if filt in ('CANAIS','FILMES','SÉRIES'): query=query.filter(Content.category==filt)
        elif filt=='ERROS': query=query.filter(Content.status.in_(['ERRO','TIMEOUT']))
        rows=query.order_by(Content.id.desc()).limit(1000).all()
        if q: rows=[x for x in rows if q.lower() in (x.title+' '+x.url).lower()]
        st.write(f'**{len(rows)}** resultado(s)')
        if rows:
            selected=[]
            for x in rows[:200]:
                c1,c2,c3,c4=st.columns([4,1.3,1.5,1.2]);
                with c1: st.markdown(f'**{html.escape(x.title)}**<br><span class="small">{html.escape(x.group_name or "Sem grupo")} • {html.escape(x.source.name if x.source else "")}</span>',unsafe_allow_html=True)
                with c2: st.write(x.category)
                with c3: st.write(x.status)
                with c4:
                    if st.checkbox('Selecionar',key=f'sel{x.id}'): selected.append(x.id)
            if selected:
                if st.button('EXPORTAR SELECIONADOS',use_container_width=True):
                    items=[M3UItem(x.title,x.url,x.group_name or '',x.category,x.logo,json.loads(x.attributes_json or '{}'),x.source.url if x.source else '') for x in rows if x.id in selected]
                    st.download_button('BAIXAR M3U',export_m3u(items),'loscollector_selecionados.m3u','audio/x-mpegurl')
        st.divider(); sources=db.query(Source).all(); choices=st.multiselect('MESCLAR FONTES',[f'{s.id} — {s.name}' for s in sources])
        if choices and st.button('MESCLAR FONTES',use_container_width=True):
            ids=[int(x.split(' — ')[0]) for x in choices]; items=[]
            for s in sources:
                if s.id in ids:
                    for x in s.contents: items.append(M3UItem(x.title,x.url,x.group_name or '',x.category,x.logo,json.loads(x.attributes_json or '{}'),s.url))
            merged=deduplicate(items); st.success(f'{len(merged)} conteúdo(s) após deduplicação.'); st.download_button('EXPORTAR M3U FINAL',export_m3u(merged),'loscollector_merged.m3u','audio/x-mpegurl')
    elif page=='MESCLAR':
        st.markdown('## MESCLAR FONTES')
        sources=db.query(Source).all(); choices=st.multiselect('FONTES PARA MESCLAGEM',[f'{s.id} — {s.name}' for s in sources])
        if choices:
            st.markdown(f'<div class="card"><b class="glow">{len(choices)} fonte(s) selecionada(s)</b><br><span class="small">Os conteúdos serão normalizados, classificados e deduplicados antes da exportação.</span></div>',unsafe_allow_html=True)
            if st.button('MESCLAR E EXPORTAR M3U',type='primary',use_container_width=True):
                ids=[int(x.split(' — ')[0]) for x in choices]; items=[]
                for src in sources:
                    if src.id in ids:
                        for x in src.contents: items.append(M3UItem(x.title,x.url,x.group_name or '',x.category,x.logo,json.loads(x.attributes_json or '{}'),src.url))
                merged=deduplicate(items); st.success(f'{len(merged)} conteúdo(s) após deduplicação.'); st.download_button('BAIXAR M3U FINAL',export_m3u(merged),'loscollector_merged.m3u','audio/x-mpegurl')
    elif page=='BANCO':
        st.markdown('## BANCO DE DADOS')
        st.markdown(f'<div class="card"><div class="label">REGISTROS</div><div class="metric glow">{db.query(Content).count():,}</div><div class="small">conteúdos armazenados</div></div>',unsafe_allow_html=True)
        x,y,z=st.columns(3)
        with x: st.metric('Fontes',db.query(Source).count())
        with y: st.metric('Usuários',db.query(User).count())
        with z: st.metric('Projetos Studio',db.query(StudioProject).count())
        st.info('O banco é SQLite no desenvolvimento e aceita PostgreSQL via DATABASE_URL no Render.')
    elif page=='DIAGNÓSTICO':
        st.markdown('## DIAGNÓSTICO'); rows=db.query(Content).order_by(Content.id.desc()).limit(500).all(); timeout=int(os.getenv('STREAM_TIMEOUT','8'))
        if st.button('VERIFICAR STREAMS',type='primary',use_container_width=True):
            prog=st.progress(0); counts={'ONLINE':0,'ERRO':0,'TIMEOUT':0}
            for i,x in enumerate(rows):
                status,detail=check_url(x.url,timeout); x.status=status; x.response_detail=detail; counts[status]=counts.get(status,0)+1; prog.progress((i+1)/max(1,len(rows)))
            db.commit(); st.success(f"Online: {counts.get('ONLINE',0)} • Erro: {counts.get('ERRO',0)} • Timeout: {counts.get('TIMEOUT',0)}")
        for x in rows[:100]: st.markdown(f'**{html.escape(x.title)}** · {x.category} · `{x.status}`  \n<span class="small">{html.escape(x.url)}</span>',unsafe_allow_html=True); st.divider()
    elif page=='STUDIO':
        st.markdown('## LOS COLLECTOR STUDIO'); st.caption('Materiais promocionais usando dados do TMDB e mídia própria/licenciada.')
        query=st.text_input('PESQUISAR FILME OU SÉRIE');
        if st.button('PESQUISAR TMDB',use_container_width=True):
            try: st.session_state['tmdb_results']=tmdb_search(query,os.getenv('TMDB_API_KEY',''))
            except Exception as e: st.error(f'TMDB: {e}')
        results=st.session_state.get('tmdb_results',[])
        if results:
            opts=[f"{r.get('title') or r.get('name')} ({(r.get('release_date') or r.get('first_air_date') or '')[:4]}) — {r.get('media_type')}" for r in results[:20]]; choice=st.selectbox('RESULTADOS',range(len(opts)),format_func=lambda i:opts[i])
            if st.button('SELECIONAR RESULTADO',use_container_width=True):
                try: st.session_state['studio_data']=tmdb_details(results[choice],os.getenv('TMDB_API_KEY',''))
                except Exception as e: st.error(f'TMDB: {e}')
        d=st.session_state.get('studio_data',{'title':'','description':'','genre':'','cover':''})
        title=st.text_input('Título',d.get('title','')); desc=st.text_area('Descrição',d.get('description',''),height=120); genre=st.text_input('Gênero',d.get('genre',''))
        promo_text=st.text_input('Texto promocional (opcional)', '')
        c1,c2=st.columns(2)
        with c1: platform=st.selectbox('Plataforma',list(PLATFORM_FORMATS),index=0); fmt=PLATFORM_FORMATS[platform]; duration=st.slider('Duração (s)',5,120,15)
        with c2:
            uploaded_logo=st.file_uploader('Adicionar logo',type=['png','jpg','jpeg','webp']); uploaded_video=st.file_uploader('Adicionar vídeo próprio/licenciado',type=['mp4','mov','mkv','webm']); music=st.file_uploader('Música licenciada (opcional)',type=['mp3','wav','m4a'])
        cover_upload=st.file_uploader('Trocar capa',type=['png','jpg','jpeg','webp'])
        if d.get('cover') and not cover_upload: st.image(d['cover'],width=180)
        def do_render(is_preview=False):
            with tempfile.TemporaryDirectory() as td:
                cover=Path(td)/'cover.jpg'; logo=Path(td)/'logo.png'; bg=Path(td)/'bg.mp4'; mus=Path(td)/'music.m4a'
                if cover_upload: cover.write_bytes(cover_upload.getvalue())
                elif d.get('cover'): download_image(d['cover'],cover)
                else: raise RuntimeError('Selecione uma obra TMDB ou envie uma capa.')
                lp=None
                if uploaded_logo: logo.write_bytes(uploaded_logo.getvalue()); lp=logo
                vp=None
                if uploaded_video: bg.write_bytes(uploaded_video.getvalue()); vp=bg
                mp=None
                if music: mus.write_bytes(music.getvalue()); mp=mus
                return render_video({'title':title,'description':desc,'genre':genre,'text':promo_text,'format':fmt,'duration':duration},MEDIA,cover,lp,vp,mp,preview=is_preview)
        b1,b2=st.columns(2)
        with b1:
            if st.button('PREVIEW',use_container_width=True):
                try: st.session_state['studio_preview']=do_render(True); st.success('Preview renderizado com FFmpeg.')
                except Exception as e: st.error(f'Preview: {e}')
        with b2:
            if st.button('GERAR VÍDEO FINAL',type='primary',use_container_width=True):
                try:
                    path=do_render(False); target=Path(path); project=StudioProject(title=title,description=desc,genre=genre,cover=d.get('cover',''),logo=str(uploaded_logo.name) if uploaded_logo else '',platform=platform,format=fmt,duration=duration,file_path=str(target)); db.add(project); db.commit(); st.session_state['studio_file']=str(target); st.success('Vídeo final renderizado com FFmpeg.')
                except Exception as e: st.error(f'Renderização: {e}')
        if st.session_state.get('studio_preview') and Path(st.session_state['studio_preview']).exists():
            st.video(st.session_state['studio_preview'])
        if st.session_state.get('studio_file'):
            p=Path(st.session_state['studio_file'])
            if p.exists(): st.video(str(p)); st.download_button('BAIXAR VÍDEO FINAL',p.read_bytes(),p.name,'video/mp4')
        st.divider(); st.markdown('### HISTÓRICO');
        for p in db.query(StudioProject).order_by(StudioProject.id.desc()).limit(20).all():
            st.markdown(f'**{html.escape(p.title)}** · {p.platform} · {p.format} · {p.duration}s · {p.created_at}')
            fp=Path(p.file_path) if p.file_path else None
            if fp and fp.exists(): st.download_button('BAIXAR',fp.read_bytes(),fp.name,'video/mp4',key=f'dl{p.id}')
    elif page=='CONFIGURAÇÕES':
        st.markdown('## CONFIGURAÇÕES')
        with st.form('pwchange'):
            old=st.text_input('Senha atual',type='password'); new=st.text_input('Nova senha',type='password'); new2=st.text_input('Confirmar nova senha',type='password')
            if st.form_submit_button('ALTERAR SENHA'):
                u=db.get(User,st.session_state.user_id)
                if not verify_password(old,u.password_hash): st.error('Senha atual incorreta.')
                elif len(new)<8: st.error('A nova senha precisa ter pelo menos 8 caracteres.')
                elif new!=new2: st.error('As senhas não coincidem.')
                else: u.password_hash=hash_password(new); u.password_changed_at=utcnow(); db.commit(); st.success('Senha alterada com sucesso.')
        st.markdown('<div class="card"><b class="glow">CONTA</b><br><span class="small">E-mail: '+html.escape(st.session_state.email)+'</span></div>',unsafe_allow_html=True)
        st.markdown('<div class="card"><b class="glow">MONITORAMENTO</b><br><span class="small">O cron de produção executa scheduler.py independentemente do Safari. Cada fonte usa intervalo e próxima verificação armazenados no banco.</span></div>',unsafe_allow_html=True)

