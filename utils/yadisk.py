from __future__ import annotations

import json
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from urllib.parse import quote, urlparse
from http.client import HTTPSConnection


@dataclass
class YaDiskConfig:
    oauth_token: str
    api_host: str = "cloud-api.yandex.net"
    remote_dir: str = "/SdelkaBackups"


class YaDiskClient:
    def __init__(self, cfg: YaDiskConfig) -> None:
        self.cfg = cfg

    def _conn_api(self) -> HTTPSConnection:
        context = ssl.create_default_context()
        return HTTPSConnection(self.cfg.api_host, 443, context=context)

    def _auth_header(self) -> tuple[str, str]:
        return ("Authorization", f"OAuth {self.cfg.oauth_token}")

    def ensure_dir(self, path: str) -> None:
        """Create remote directory recursively via REST (PUT /v1/disk/resources?path=...)."""
        p = "/" + (path or "").strip("/")
        if p == "/":
            return
        parts = [seg for seg in p.split("/") if seg]
        current = ""
        for seg in parts:
            current = f"{current}/{seg}"
            conn = self._conn_api()
            try:
                path_q = quote(current)
                url = f"/v1/disk/resources?path={path_q}"
                conn.putrequest("PUT", url)
                h, v = self._auth_header()
                conn.putheader(h, v)
                conn.endheaders()
                resp = conn.getresponse()
                # 201 Created or 409 Already exists are fine
                if resp.status not in (201, 409):
                    raise RuntimeError(f"MKDIR failed: {resp.status} {resp.reason}")
                try:
                    _ = resp.read()
                except Exception:
                    pass
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

    def test_connection(self) -> tuple[bool, str]:
        """Validate OAuth by calling /v1/disk/ (expects 200)."""
        conn = self._conn_api()
        try:
            conn.putrequest("GET", "/v1/disk/")
            h, v = self._auth_header()
            conn.putheader(h, v)
            conn.endheaders()
            resp = conn.getresponse()
            ok = resp.status == 200
            msg = f"{resp.status} {resp.reason}"
            try:
                _ = resp.read()
            except Exception:
                pass
            return ok, msg
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def download_public_file(self, public_url: str, dest_path: Path, item_name: Optional[str] = None) -> None:
        """Download a public file (no OAuth) using public resources API.

        If public_url points to a folder, provide item_name (e.g., 'sdelka_base.db').
        If public_url points directly to a file, item_name can be None.
        """
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        # Step 1: get download URL from public
        conn = self._conn_api()
        try:
            pk = quote(public_url, safe="")
            if item_name:
                path_q = quote("/" + item_name)
                url = f"/v1/disk/public/resources/download?public_key={pk}&path={path_q}"
            else:
                url = f"/v1/disk/public/resources/download?public_key={pk}"
            conn.putrequest("GET", url)
            # Public endpoints допускают без OAuth, но можно добавлять заголовок при наличии токена
            if self.cfg.oauth_token:
                h, v = self._auth_header()
                conn.putheader(h, v)
            # Добавим заголовки как у обычного браузера, чтобы снизить шанс капчи
            conn.putheader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
            conn.putheader("Accept", "*/*")
            conn.putheader("Accept-Language", "ru-RU,ru;q=0.9,en;q=0.8")
            conn.endheaders()
            resp = conn.getresponse()
            data = resp.read()
            if resp.status != 200:
                # Если дали ссылку на папку без item_name — попробуем найти sdelka_base.db или первый .db
                if not item_name:
                    try:
                        conn_list = self._conn_api()
                        list_url = f"/v1/disk/public/resources?public_key={pk}&limit=1000"
                        # Простая ретрай-логика для временных 5xx
                        attempt = 0
                        while True:
                            attempt += 1
                            conn_list.putrequest("GET", list_url)
                            if self.cfg.oauth_token:
                                h, v = self._auth_header()
                                conn_list.putheader(h, v)
                            conn_list.endheaders()
                            rlist = conn_list.getresponse()
                            listing = rlist.read()
                            if rlist.status == 200:
                                break
                            if 500 <= rlist.status < 600 and attempt < 3:
                                try:
                                    conn_list.close()
                                except Exception:
                                    pass
                                conn_list = self._conn_api()
                                continue
                            raise RuntimeError(f"List public folder failed: {rlist.status} {rlist.reason}")
                        if rlist.status == 200:
                            meta = json.loads(listing.decode("utf-8", errors="ignore"))
                            items = ((meta.get("_embedded") or {}).get("items") or [])
                            # Сформировать упорядоченный список кандидатов
                            candidates: list[str] = []
                            # 1) точное имя sdelka_base.db
                            for it in items:
                                nm = str(it.get("name", ""))
                                if nm.lower() == "sdelka_base.db":
                                    candidates.append(nm)
                                    break
                            # 2) остальные *.db (кроме Thumbs.db)
                            for it in items:
                                nm = str(it.get("name", ""))
                                lnm = nm.lower()
                                if lnm.endswith(".db") and lnm != "sdelka_base.db" and lnm != "thumbs.db":
                                    candidates.append(nm)
                            # Перебираем кандидатов до первой валидной SQLite
                            downloaded_ok = False
                            last_err: str | None = None
                            for nm in candidates:
                                try:
                                    conn2 = self._conn_api()
                                    try:
                                        pth_q = quote("/" + nm)
                                        dl2 = f"/v1/disk/public/resources/download?public_key={pk}&path={pth_q}"
                                        conn2.putrequest("GET", dl2)
                                        if self.cfg.oauth_token:
                                            h, v = self._auth_header()
                                            conn2.putheader(h, v)
                                        conn2.endheaders()
                                        r2 = conn2.getresponse()
                                        d2 = r2.read()
                                        if r2.status != 200:
                                            last_err = f"{r2.status} {r2.reason}"
                                            continue
                                        info2 = json.loads(d2.decode("utf-8", errors="ignore"))
                                        href2 = info2.get("href")
                                        if not href2:
                                            last_err = "no href"
                                            continue
                                    finally:
                                        try:
                                            conn2.close()
                                        except Exception:
                                            pass
                                    # Скачать кандидата
                                    parsed2 = urlparse(href2)
                                    dl2c = HTTPSConnection(parsed2.hostname, 443, context=ssl.create_default_context())
                                    try:
                                        pwq = parsed2.path + (f"?{parsed2.query}" if parsed2.query else "")
                                        dl2c.putrequest("GET", pwq)
                                        # Браузерные заголовки для снижения капчи
                                        dl2c.putheader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
                                        dl2c.putheader("Accept", "*/*")
                                        dl2c.putheader("Accept-Language", "ru-RU,ru;q=0.9,en;q=0.8")
                                        dl2c.endheaders()
                                        rdl = dl2c.getresponse()
                                        if rdl.status != 200:
                                            last_err = f"{rdl.status} {rdl.reason}"
                                            continue
                                        blob = rdl.read()
                                        # Проверим на SQLite заголовок
                                        if not (len(blob) >= 16 and blob[:16] == b"SQLite format 3\x00"):
                                            last_err = "not sqlite"
                                            continue
                                        dest_path.write_bytes(blob)
                                        downloaded_ok = True
                                        break
                                    finally:
                                        try:
                                            dl2c.close()
                                        except Exception:
                                            pass
                                except Exception as e:
                                    last_err = str(e)
                                    continue
                            if not downloaded_ok:
                                raise RuntimeError(f"В расшаренной папке не найден корректный файл базы (.db). {last_err or ''}")
                            return
                        else:
                            raise RuntimeError(f"List public folder failed: {rlist.status} {rlist.reason}")
                    finally:
                        try:
                            conn_list.close()
                        except Exception:
                            pass
                # Если не папка — отдадим исходную ошибку
                if resp.status != 200:
                    try:
                        j = json.loads(data.decode("utf-8", errors="ignore"))
                        err = j.get("message") or j
                    except Exception:
                        err = data[:200]
                    raise RuntimeError(f"Get public download URL failed: {resp.status} {resp.reason} — {err}")
            info = json.loads(data.decode("utf-8"))
            href = info.get("href")
            if not href:
                raise RuntimeError("Public download URL not provided by API")
        finally:
            try:
                conn.close()
            except Exception:
                pass
        # Step 2: download
        parsed = urlparse(href)
        dl_conn = HTTPSConnection(parsed.hostname, 443, context=ssl.create_default_context())
        try:
            path_with_query = parsed.path + (f"?{parsed.query}" if parsed.query else "")
            dl_conn.putrequest("GET", path_with_query)
            # Браузерные заголовки
            dl_conn.putheader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
            dl_conn.putheader("Accept", "*/*")
            dl_conn.putheader("Accept-Language", "ru-RU,ru;q=0.9,en;q=0.8")
            dl_conn.endheaders()
            dl_resp = dl_conn.getresponse()
            if dl_resp.status != 200:
                raise RuntimeError(f"Public download failed: {dl_resp.status} {dl_resp.reason}")
            content = dl_resp.read()
            # Если запрашивали конкретный файл, проверим, что это SQLite
            if not (len(content) >= 16 and content[:16] == b"SQLite format 3\x00"):
                raise RuntimeError("Загруженный файл не является базой SQLite. Убедитесь, что в папке лежит sdelka_base.db")
            dest_path.write_bytes(content)
        finally:
            try:
                dl_conn.close()
            except Exception:
                pass

    def get_public_meta(self, public_url: str) -> dict:
        """Return metadata for a public resource (file or folder)."""
        conn = self._conn_api()
        try:
            pk = quote(public_url, safe="")
            url = f"/v1/disk/public/resources?public_key={pk}"
            conn.putrequest("GET", url)
            if self.cfg.oauth_token:
                h, v = self._auth_header()
                conn.putheader(h, v)
            conn.endheaders()
            resp = conn.getresponse()
            data = resp.read()
            if resp.status != 200:
                raise RuntimeError(f"Get public meta failed: {resp.status} {resp.reason}")
            return json.loads(data.decode("utf-8", errors="ignore"))
        finally:
            try:
                conn.close()
            except Exception:
                pass
    def upload_file(self, local_path: Path, remote_name: Optional[str] = None, overwrite: bool: bool = True) -> str:
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(local_path)
        remote_name = remote_name or local_path.name
        remote_dir = self.cfg.remote_dir.rstrip("/") or "/"
        remote_path = f"{remote_dir}/{remote_name}"
        # ensure dir
        if remote_dir and remote_dir != "/":
            self.ensure_dir(remote_dir)
        # Step 0: delete existing file if overwrite
        if overwrite:
            try:
                conn_del = self._conn_api()
                path_q = quote(remote_path)
                conn_del.putrequest("DELETE", f"/v1/disk/resources?path={path_q}")
                h, v = self._auth_header()
                conn_del.putheader(h, v)
                conn_del.endheaders()
                respd = conn_del.getresponse()
                # 204/202 ok, 404 not found also ok
                _ = respd.read()
            except Exception:
                pass
            finally:
                try:
                    conn_del.close()
                except Exception:
                    pass

        # Step 1: get upload URL
        conn = self._conn_api()
        try:
            path_q = quote(remote_path)
            url = f"/v1/disk/resources/upload?path={path_q}&overwrite={'true' if overwrite else 'false'}"
            conn.putrequest("GET", url)
            h, v = self._auth_header()
            conn.putheader(h, v)
            conn.endheaders()
            resp = conn.getresponse()
            data = resp.read()
            if resp.status not in (200, 201):
                try:
                    j = json.loads(data.decode("utf-8", errors="ignore"))
                    err = j.get("message") or j
                except Exception:
                    err = data[:200]
                raise RuntimeError(f"Get upload URL failed: {resp.status} {resp.reason} — {err}")
            try:
                info = json.loads(data.decode("utf-8"))
            except Exception as exc:
                raise RuntimeError(f"Invalid JSON from upload URL: {exc}")
            href = info.get("href")
            if not href:
                raise RuntimeError("Upload URL not provided by API")
        finally:
            try:
                conn.close()
            except Exception:
                pass

        # Step 2: PUT file to href
        parsed = urlparse(href)
        up_conn = HTTPSConnection(parsed.hostname, 443, context=ssl.create_default_context())
        try:
            path_with_query = parsed.path + (f"?{parsed.query}" if parsed.query else "")
            data_bytes = local_path.read_bytes()
            up_conn.putrequest("PUT", path_with_query)
            # upload URL already includes auth via pre-signed URL; no OAuth header needed
            up_conn.putheader("Content-Length", str(len(data_bytes)))
            up_conn.putheader("Content-Type", "application/octet-stream")
            up_conn.endheaders()
            up_conn.send(data_bytes)
            up_resp = up_conn.getresponse()
            if up_resp.status not in (201, 202, 200):
                raise RuntimeError(f"Upload failed: {up_resp.status} {up_resp.reason}")
            try:
                _ = up_resp.read()
            except Exception:
                pass
            return remote_path
        finally:
            try:
                up_conn.close()
            except Exception:
                pass

    def download_file(self, remote_path: str, dest_path: Path) -> None:
        """Download a file from Yandex.Disk to a local destination using REST API.

        remote_path: absolute path on Disk (e.g., "/SdelkaBackups/sdelka_base.db")
        dest_path: local file path (will be overwritten)
        """
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        # Step 1: get download URL
        import logging
        log = logging.getLogger(__name__)
        log.info("download_file start: remote=%s -> dest=%s", remote_path, dest_path)
        conn = self._conn_api()
        try:
            path_q = quote(remote_path)
            conn.putrequest("GET", f"/v1/disk/resources/download?path={path_q}")
            h, v = self._auth_header()
            conn.putheader(h, v)
            conn.endheaders()
            resp = conn.getresponse()
            data = resp.read()
            if resp.status != 200:
                try:
                    j = json.loads(data.decode("utf-8", errors="ignore"))
                    err = j.get("message") or j
                except Exception:
                    err = data[:200]
                log.error("download URL error: %s %s: %s", resp.status, resp.reason, err)
                raise RuntimeError(f"Get download URL failed: {resp.status} {resp.reason} — {err}")
            info = json.loads(data.decode("utf-8"))
            href = info.get("href")
            if not href:
                raise RuntimeError("Download URL not provided by API")
        finally:
            try:
                conn.close()
            except Exception:
                pass
        # Step 2: GET from href
        parsed = urlparse(href)
        dl_conn = HTTPSConnection(parsed.hostname, 443, context=ssl.create_default_context())
        try:
            path_with_query = parsed.path + (f"?{parsed.query}" if parsed.query else "")
            dl_conn.putrequest("GET", path_with_query)
            dl_conn.endheaders()
            dl_resp = dl_conn.getresponse()
            log.info("download GET resp: %s %s", dl_resp.status, dl_resp.reason)
            if dl_resp.status != 200:
                raise RuntimeError(f"Download failed: {dl_resp.status} {dl_resp.reason}")
            content = dl_resp.read()
            dest_path.write_bytes(content)
        finally:
            try:
                dl_conn.close()
            except Exception:
                pass
