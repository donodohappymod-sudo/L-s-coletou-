import streamlit as st
from pathlib import Path
from datetime import datetime
from m3u_engine import parse_m3u, merge_entries, organize_entries, generate_m3u
from database import init_db, save_source, list_sources, save_snapshot, load_snapshot
from collector import crawl_site_for_playlists
from checker import check_entries

init_db()
st.set_page_config(page_title="LosCollector", page_icon="👑", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1200px; padding-top: 2rem;}
h1 {letter-spacing: .04em;}
.card {padding:1rem;border:1px solid rgba(127,127,127,.2);border-radius:16px;margin-bottom:1rem;}
</style>
""", unsafe_allow_html=True)

st.title("👑 LOS COLLECTOR")
st.caption("Collect • Organize • Monitor")

home, sources, library, studio, diagnosis = st.tabs(
    ["⌂ Início", "📡 Fontes", "📚 Biblioteca", "🎬 Studio", "🩺 Diagnóstico"]
)

with home:
    st.subheader("Painel")
    ss = list_sources()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Fontes", len(ss))
    c2.metric("Entradas", sum(x["entries"] for x in ss))
    c3.metric("Status", "Pronto")
    c4.metric("Atualização", "Manual")
    st.info("Adicione uma fonte para começar a coleta.")

with sources:
    st.subheader("Adicionar fonte")
    url = st.text_input("URL do site", placeholder="https://exemplo.com", key="source_url")
    pages = st.number_input("Limite de páginas", 1, 500, 50)
    if st.button("🔎 Iniciar varredura", type="primary"):
        if not url.startswith(("http://","https://")):
            st.error("URL inválida.")
        else:
            with st.spinner("Varrendo a fonte..."):
                result = crawl_site_for_playlists(url, int(pages))
            st.session_state["crawl"] = result
            st.success(f"{len(result['playlists'])} playlist(s) identificada(s).")
            if result["warnings"]:
                st.warning("Alguns recursos não puderam ser acessados.")

    r = st.session_state.get("crawl")
    if r:
        for p in r["playlists"]:
            st.code(p)
        if st.button("💾 Importar fonte encontrada"):
            entries=[]
            for p, text in r["contents"].items():
                entries.extend(parse_m3u(text, source=url))
            entries=organize_entries(merge_entries(entries))
            save_source(url,len(entries))
            save_snapshot(url,generate_m3u(entries))
            st.success(f"{len(entries)} entradas importadas e organizadas.")

with library:
    st.subheader("Biblioteca")
    ss=list_sources()
    if not ss:
        st.info("Sua biblioteca ainda está vazia.")
    else:
        for s in ss:
            st.markdown(f"**{s['url']}**  ·  {s['entries']} entradas  ·  {s['updated_at']}")
    selected=st.multiselect("Fontes para mesclar",[x["url"] for x in ss])
    if st.button("🧩 Mesclar e deduplicar"):
        entries=[]
        for u in selected:
            raw=load_snapshot(u)
            if raw: entries.extend(parse_m3u(raw,source=u))
        entries=organize_entries(merge_entries(entries))
        final=generate_m3u(entries)
        st.session_state["final"]=final
        st.success(f"Playlist final: {len(entries)} entradas únicas.")
    if st.session_state.get("final"):
        st.download_button("📥 Baixar M3U final",st.session_state["final"],
                           f"LosCollector_{datetime.now():%Y%m%d_%H%M%S}.m3u",
                           "audio/x-mpegurl")

with studio:
    st.subheader("🎬 LosCollector Studio")
    st.caption("Criação de materiais promocionais a partir de informações e imagens que você possui autorização para usar.")
    title=st.text_input("Título do filme ou série")
    desc=st.text_area("Descrição")
    genre=st.text_input("Gênero / categoria")
    logo=st.file_uploader("Seu logo",type=["png","jpg","jpeg","webp"])
    cover=st.file_uploader("Capa",type=["png","jpg","jpeg","webp"])
    platform=st.selectbox("Onde será publicado",["Instagram Reels","Instagram Story","YouTube","YouTube Shorts","Formato personalizado"])
    ratio={"Instagram Reels":"9:16","Instagram Story":"9:16","YouTube":"16:9","YouTube Shorts":"9:16","Formato personalizado":"Personalizado"}[platform]
    duration=st.slider("Duração (segundos)",5,60,15)
    text=st.text_input("Texto de destaque",placeholder="Novo lançamento")
    if st.button("✨ Criar projeto do trailer"):
        if not title:
            st.error("Informe o título.")
        else:
            project={
                "title":title,"description":desc,"genre":genre,"platform":platform,
                "ratio":ratio,"duration":duration,"headline":text,
                "logo":bool(logo),"cover":bool(cover)
            }
            st.session_state["studio_project"]=project
            st.success("Projeto preparado. A próxima etapa é renderizar o vídeo com os arquivos enviados.")
    if st.session_state.get("studio_project"):
        st.json(st.session_state["studio_project"])

with diagnosis:
    st.subheader("🩺 Diagnóstico")
    raw=st.session_state.get("final")
    if not raw:
        st.info("Primeiro gere uma playlist na Biblioteca.")
    else:
        entries=parse_m3u(raw)
        n=st.number_input("Quantidade para verificar",1,len(entries),min(100,len(entries)))
        if st.button("🟢 Testar disponibilidade"):
            with st.spinner("Testando..."):
                df=check_entries(entries[:int(n)])
            st.dataframe(df,use_container_width=True)
