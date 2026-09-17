import os, subprocess, uuid, shutil
from pathlib import Path
from urllib.parse import urljoin
import requests
from PIL import Image

TMDB='https://api.themoviedb.org/3'
IMG='https://image.tmdb.org/t/p/w780'

PLATFORM_FORMATS={
 'Instagram Reels':'9:16','Instagram Story':'9:16','YouTube Shorts':'9:16','TikTok':'9:16','YouTube':'16:9','Personalizado':'custom'
}

def tmdb_search(query, api_key, page=1):
    if not api_key: raise RuntimeError('TMDB_API_KEY não configurada.')
    r=requests.get(f'{TMDB}/search/multi',params={'api_key':api_key,'query':query,'language':'pt-BR','include_adult':'false','page':page},timeout=10)
    r.raise_for_status(); data=r.json()
    return [x for x in data.get('results',[]) if x.get('media_type') in ('movie','tv')]

def tmdb_details(item, api_key):
    typ=item.get('media_type'); ident=item.get('id')
    r=requests.get(f'{TMDB}/{typ}/{ident}',params={'api_key':api_key,'language':'pt-BR'},timeout=10)
    r.raise_for_status(); d=r.json()
    title=d.get('title') or d.get('name') or ''
    genres=', '.join(g['name'] for g in d.get('genres',[]))
    return {'title':title,'description':d.get('overview',''),'genre':genres,'cover':IMG+d['poster_path'] if d.get('poster_path') else '', 'year':(d.get('release_date') or d.get('first_air_date') or '')[:4]}

def download_image(url,dest):
    r=requests.get(url,timeout=15); r.raise_for_status(); Path(dest).write_bytes(r.content); return dest

def _size(fmt): return (1080,1920) if fmt=='9:16' else (1920,1080)

def render_video(project, media_dir, cover_path=None, logo_path=None, background_video=None, music_path=None, preview=False):
    outdir=Path(media_dir)/'generated'; outdir.mkdir(parents=True,exist_ok=True)
    job=uuid.uuid4().hex[:12]; out=outdir/f'{job}{'_preview' if preview else ''}.mp4'
    w,h=_size(project['format']) if project['format']!='custom' else (int(project.get('width',1080)),int(project.get('height',1920)))
    if preview: w,h=max(360,w//2),max(640,h//2)
    duration=5 if preview else max(5,min(int(project.get('duration',15)),120))
    bg=background_video or cover_path
    if not bg: raise RuntimeError('Adicione uma capa ou vídeo de fundo.')
    cmd=['ffmpeg','-y','-hide_banner','-loglevel','error']
    if background_video: cmd += ['-stream_loop','-1','-i',str(bg)]
    else: cmd += ['-loop','1','-i',str(bg)]
    vf=f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=yuv420p"
    current='[base]'; vf += current
    # The first filter needs a label; build it explicitly.
    if background_video:
        vf=f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=yuv420p[base]"
    else:
        vf=f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},zoompan=z='min(zoom+0.0007,1.12)':d=1:s={w}x{h}:fps=30,format=yuv420p[base]"
    current='[base]'; input_idx=1
    if logo_path:
        cmd += ['-i',str(logo_path)]
        vf += f";[{input_idx}:v]scale='min(300,iw)':'min(180,ih)':force_original_aspect_ratio=decrease[logo];[base][logo]overlay=W-w-40:40[withlogo]"
        current='[withlogo]'; input_idx+=1
    title=project['title'].replace('\\','').replace(':','\\:').replace("'","\\'")[:70]
    custom=project.get('text','').replace('\\','').replace(':','\\:').replace("'","\\'")[:120]
    draw=f";{current}drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='{title}':fontcolor=white:fontsize={max(28,int(w*0.045))}:x=(w-text_w)/2:y=h*0.72:box=1:boxcolor=black@0.45:boxborderw=18[tmp1]"
    if custom: draw += f";[tmp1]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='{custom}':fontcolor=white:fontsize={max(20,int(w*0.028))}:x=(w-text_w)/2:y=h*0.82:box=1:boxcolor=black@0.35:boxborderw=12[vout]"
    else: draw += ";[tmp1]null[vout]"
    vf += draw
    if music_path:
        cmd += ['-stream_loop','-1','-i',str(music_path)]
        music_idx=input_idx
        vf += f";[{music_idx}:a]volume=0.22[aout]"
        cmd += ['-filter_complex',vf,'-map','[vout]','-map','[aout]','-t',str(duration),'-r','30','-c:v','libx264','-preset','veryfast','-crf','22','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',str(out)]
    else:
        cmd += ['-filter_complex',vf,'-map','[vout]','-t',str(duration),'-r','30','-c:v','libx264','-preset','veryfast','-crf','22','-an','-movflags','+faststart',str(out)]
    subprocess.run(cmd,check=True,timeout=duration*15+90)
    return str(out)
