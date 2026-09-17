import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

UA='LosCollector/1.0 (+public-authorized-content)'

def check_url(url, timeout=8):
    try:
        r=requests.get(url, stream=True, timeout=(3,timeout), allow_redirects=True, headers={'User-Agent':UA}, verify=True)
        code=r.status_code
        r.close()
        return ('ONLINE' if 200 <= code < 400 else 'ERRO', str(code))
    except requests.exceptions.Timeout: return ('TIMEOUT','timeout')
    except (requests.exceptions.RequestException, socket.error) as e: return ('ERRO', str(e)[:450])

def check_many(items, timeout=8, workers=12):
    results={}
    with ThreadPoolExecutor(max_workers=max(1,min(workers,len(items) or 1))) as ex:
        futures={ex.submit(check_url,i.url,timeout):i for i in items}
        for f in as_completed(futures):
            i=futures[f]
            try: results[i.id]=f.result()
            except Exception as e: results[i.id]=('ERRO',str(e)[:450])
    return results
