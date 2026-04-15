import re, sys, os, random, string, subprocess, webbrowser, threading, time, queue
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from flask import Flask, request, jsonify, Response, stream_with_context

try:
    import win32com.client
    import pythoncom
    import webview  # Pour la fenêtre native
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TDRC, ID3NoHeaderError
except ImportError:
    print("❌ Missing dependencies: pip install flask pywin32 mutagen pywebview")
    sys.exit(1)

app = Flask(__name__)
is_busy = False # Server global lock
APP_TITLE = "iPod Manager Lazy" # Nom dans la barre de titre

# --- TKINTER MANAGEMENT (DEDICATED THREAD) ---
_tk_queue = queue.Queue()
_tk_result = queue.Queue()

def _tk_worker():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    def process():
        try:
            task = _tk_queue.get_nowait()
            if task == 'browse':
                path = filedialog.askdirectory(parent=root)
                _tk_result.put(path.replace('/', '\\') if path else None)
            elif task == 'wake':
                root.update()
                _tk_result.put(True)
        except queue.Empty: pass
        root.after(100, process)
    root.after(100, process)
    root.mainloop()

threading.Thread(target=_tk_worker, daemon=True).start()

def tk_wake():
    _tk_queue.put('wake')
    try: _tk_result.get(timeout=2)
    except: pass

# --- HELPERS (COM INITIALIZATION) ---
def get_ipod():
    """Initialize COM on each request to prevent resource leaks"""
    pythoncom.CoInitialize()
    try:
        itunes = win32com.client.Dispatch("iTunes.Application")
        for source in itunes.Sources:
            if source.Kind == 2: return itunes, source
    except: pass
    # Pas de source trouvee : on balance CoInitialize tout de suite
    pythoncom.CoUninitialize()
    return None, None

def slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '_', slug)
    slug = slug.strip('_')
    return slug if slug else ''.join(random.choices(string.ascii_uppercase, k=7))

def clean_tags(p: Path, t: str, f: str):
    try:
        try: tags = ID3(p)
        except ID3NoHeaderError:
            audio = MP3(p); audio.add_tags(); tags = audio.tags
        tags.delete(p, delete_v1=True, delete_v2=True)
        tags = ID3()
        tags.add(TIT2(encoding=3, text=t)); tags.add(TPE1(encoding=3, text=f))
        tags.add(TALB(encoding=3, text=f)); tags.add(TRCK(encoding=3, text="1"))
        tags.add(TDRC(encoding=3, text="2000")); tags.save(p, v2_version=3)
    except: pass

# --- ROUTES ---

@app.route("/api/clean-orphans", methods=["POST"])
def clean_orphans():
    global is_busy
    is_busy = True
    def generate():
        global is_busy
        log = lambda m: f"data: {m}\n\n"
        yield log("🔍 Deep scan (Secure mode: Name + Artist)...")
        try:
            itunes, ipod = get_ipod()
            if not ipod:
                yield log("❌ iPod not found."); yield log("DONE"); return

            # 1. Catalog everything in user playlists
            valid_tracks_keys = set()
            yield log("📝 Inventorying valid playlists...")
            
            for pl in ipod.Playlists:
                # Kind 2 = User Playlists, SpecialKind 0 = Normal
                if pl.Kind == 2 and pl.SpecialKind == 0:
                    count = pl.Tracks.Count
                    for i in range(1, count + 1):
                        try:
                            t = pl.Tracks.Item(i)
                            # Unique key based on smoothed text content
                            key = f"{t.Name.lower().strip()}|{t.Artist.lower().strip()}"
                            valid_tracks_keys.add(key)
                        except: continue
            
            yield log(f"✅ {len(valid_tracks_keys)} unique tracks identified to keep.")

            # 2. Scan Master Library (Kind 1) to find intruders
            lib = next(p for p in ipod.Playlists if p.Kind == 1)
            total_in_lib = lib.Tracks.Count
            to_delete_indices = []
            
            yield log(f"📦 Analyzing main library ({total_in_lib} files)...")
            
            # Going backwards for deletion later
            for i in range(total_in_lib, 0, -1):
                try:
                    t = lib.Tracks.Item(i)
                    key = f"{t.Name.lower().strip()}|{t.Artist.lower().strip()}"
                    
                    if key not in valid_tracks_keys:
                        to_delete_indices.append(i)
                except: continue

            # 3. Purging orphans
            if not to_delete_indices:
                yield log("✨ iPod is perfectly clean. No orphans found.")
            else:
                yield log(f"🔥 {len(to_delete_indices)} orphans detected. Starting purge...")
                deleted = 0
                for idx in to_delete_indices:
                    try:
                        lib.Tracks.Item(idx).Delete()
                        deleted += 1
                        if deleted % 5 == 0:
                            yield log(f"  🗑️ {deleted}/{len(to_delete_indices)} deleted")
                    except: continue
                
                yield log("💾 Saving database to iPod...")
                itunes.UpdateIPod()

            yield log("✅ Success.")
            yield log("DONE")
        except Exception as e:
            yield log(f"❌ Error : {str(e)}")
            yield log("DONE")
        finally:
            is_busy = False
            pythoncom.CoUninitialize()
            
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/api/smooth-tags", methods=["POST"])
def smooth_tags():
    global is_busy
    is_busy = True
    def generate():
        global is_busy
        log = lambda m: f"data: {m}\n\n"
        yield log("🎨 Logical smoothing...")
        try:
            itunes, ipod = get_ipod()
            if not ipod:
                yield log("❌ iPod not found."); yield log("DONE"); return

            playlists = ipod.Playlists
            for p_idx in range(1, playlists.Count + 1):
                pl = playlists.Item(p_idx)
                
                # Processing only normal user playlists
                if pl.Kind == 2 and pl.SpecialKind == 0:
                    pl_name = pl.Name
                    tracks = pl.Tracks
                    count = tracks.Count
                    
                    if count > 0:
                        yield log(f"📦 Processing: {pl_name} ({count} tracks)")
                        
                        for t_idx in range(1, count + 1):
                            try:
                                t = tracks.Item(t_idx)
                                
                                # 1. TITLE SECURITY (if Unknown)
                                if not t.Name or "unknown" in t.Name.lower():
                                    try:
                                        t.Name = os.path.basename(t.Location).rsplit('.', 1)[0]
                                    except:
                                        pass

                                # 2. IDENTITY TAGS
                                t.Artist = pl_name
                                t.Album = pl_name
                                t.Year = 2026
                                
                                # 3. FULL CLEANUP
                                t.Comment = ""
                                t.Composer = ""
                                t.Genre = ""
                                t.Grouping = ""
                                t.TrackNumber = 0
                                t.TrackCount = 0
                                t.DiscNumber = 0
                                t.DiscCount = 0
                                t.BPM = 0
                                t.Rating = 0
                                
                                # 4. REMOVING ARTWORK
                                try:
                                    count = t.Artwork.Count
                                    for a_idx in range(count, 0, -1):
                                        try: t.Artwork.Item(a_idx).Delete()
                                        except: pass
                                except:
                                    pass
                                    
                            except Exception:
                                continue
            
            yield log("💾 Saving to iPod...")
            itunes.UpdateIPod()
            yield log("✅ Success !")
            yield log("DONE")
        except Exception as e:
            yield log(f"❌ Error : {str(e)}"); yield log("DONE")
        finally:
            is_busy = False
            pythoncom.CoUninitialize()
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/api/ipod-status", methods=["POST"])
def ipod_status():
    tk_wake()
    itunes, ipod = get_ipod()
    res = jsonify({"connected": ipod is not None, "name": ipod.Name if ipod else None, "busy": is_busy})
    pythoncom.CoUninitialize() 
    return res

@app.route("/api/list-playlists", methods=["POST"])
def list_playlists():
    itunes, ipod = get_ipod()
    if not ipod: 
        pythoncom.CoUninitialize()
        return jsonify({"playlists": []})
    
    names = []
    try:
        for pl in ipod.Playlists:
            if pl.Kind == 2 and pl.SpecialKind == 0:
                names.append(pl.Name)
    except:
        pass

    res = jsonify({"playlists": sorted(list(set(names)))})
    pythoncom.CoUninitialize()
    return res

@app.route("/api/browse-folder", methods=["POST"])
def browse_folder():
    if is_busy: return jsonify({"folder": None})
    while not _tk_result.empty():
        try: _tk_result.get_nowait()
        except: break
    _tk_queue.put('browse')
    try:
        path = _tk_result.get(timeout=60)
        if isinstance(path, bool): path = None
        return jsonify({"folder": path})
    except:
        return jsonify({"folder": None})

@app.route("/api/delete-playlist", methods=["POST"])
def delete_playlist():
    global is_busy
    is_busy = True
    pl_name = request.json.get("playlist")
    def generate():
        global is_busy
        log = lambda m: f"data: {m}\n\n"
        yield log(f"🗑️ Purge: {pl_name}")
        try:
            itunes, ipod = get_ipod()
            playlist = next((p for p in ipod.Playlists if p.Name == pl_name), None)
            if not playlist:
                yield log("❌ Playlist not found.")
                yield log("DONE")
                return

            to_delete = set((t.Name.lower().strip(), t.Artist.lower().strip()) for t in playlist.Tracks)
            total = len(to_delete)
            yield log(f"🔥 {total} files to delete...")

            lib = next(p for p in ipod.Playlists if p.Kind == 1)
            deleted = 0

            for i in range(lib.Tracks.Count, 0, -1):
                try:
                    t = lib.Tracks.Item(i)
                    key = (t.Name.lower().strip(), t.Artist.lower().strip())
                    if key in to_delete:
                        t.Delete()
                        deleted += 1
                        to_delete.discard(key)
                except Exception as e:
                    err = str(e).lower()
                    if "playlist" in err and "deleted" in err:
                        try:
                            itunes, ipod = get_ipod()
                            lib = next(p for p in ipod.Playlists if p.Kind == 1)
                        except: pass
                    continue

            yield log(f"  Pass 1: {deleted}/{total} removed.")

            if to_delete:
                yield log(f"  ↻ Pass 2: {len(to_delete)} stubborn file(s)...")
                for k in to_delete:
                    yield log(f"    → '{k[0]}' / artist='{k[1]}'")
                names_only = {k[0] for k in to_delete}
                try:
                    itunes2, ipod2 = get_ipod()
                    lib2 = next(p for p in ipod2.Playlists if p.Kind == 1)
                    for i in range(lib2.Tracks.Count, 0, -1):
                        try:
                            t = lib2.Tracks.Item(i)
                            tname = t.Name.lower().strip()
                            if tname in names_only:
                                t.Delete()
                                deleted += 1
                                names_only.discard(tname)
                        except: continue
                except: pass
                yield log(f"  Pass 2: {deleted}/{total} total removed.")

            yield log(f"✅ Final: {deleted}/{total} files removed.")

            try:
                pl_check = next((p for p in ipod.Playlists if p.Name == pl_name), None)
                if pl_check:
                    pl_check.Delete()
            except: pass

            yield log("DONE")
        except Exception as e:
            yield log(f"❌ Error: {str(e)}")
            yield log("DONE")
        finally:
            is_busy = False
            pythoncom.CoUninitialize()
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/api/sync", methods=["POST"])
def sync():
    global is_busy
    is_busy = True
    data = request.json
    folder = Path(data.get("folder", ""))
    
    def generate():
        global is_busy
        log = lambda m: f"data: {m}\n\n"
        
        try:
            # --- PHASE 1 : WINDOWS FILE OPERATIONS ONLY ---
            yield log(f"🚀 Phase 1: Windows file system operations")
            
            # On récupère la liste initiale
            mp3_files = sorted(folder.glob("*.mp3"))
            
            # 1. WINDOWS RENOMME TOUS LES MP3 (FILE NAME PHYSIQUE)
            yield log("  📁 Step 1: Renaming all physical files...")
            renamed_files = []
            for mp3 in mp3_files:
                original_stem = mp3.stem
                new_filename = f"{slugify(original_stem)}.mp3"
                new_path = mp3.parent / new_filename
                
                if mp3.name != new_filename:
                    if new_path.exists():
                        new_path.unlink()
                    mp3.rename(new_path)
                
                # On mémorise le nouveau chemin pour l'étape suivante
                renamed_files.append(new_path)

            # 2. WINDOWS MODIFIE TOUS LES TITRES (TITLE = NEW FILE NAME)
            # Puis modifie Album et Artiste
            yield log("  🏷️ Step 2: Applying New Filename to Title tags...")
            for path in renamed_files:
                # On extrait le nom physique sans extension pour le titre
                new_title = path.stem 
                for _ in range(3): # Sécurité verrous Windows
                    try:
                        clean_tags(path, new_title, folder.name)
                        break
                    except:
                        time.sleep(0.5)
            
            yield log("  ✅ Windows phase completed successfully.")

            # --- SÉCURITÉ : STABILISATION ---
            yield log("⏳ Waiting for disk synchronization...")
            time.sleep(3)

            # --- PHASE 2 : ITUNES AUTHORIZATION ---
            yield log("🚀 Phase 2: iTunes Authorization and Transfer")
            pythoncom.CoInitialize()
            itunes, ipod = get_ipod()
            
            if not ipod:
                yield log("❌ iPod not found."); return

            itunes.UpdateIPod()
            playlist = next((p for p in ipod.Playlists if p.Name == folder.name), None)
            if not playlist: 
                playlist = itunes.CreatePlaylistInSource(folder.name, ipod)
            
            existing_tracks = {t.Name.lower().strip() for t in playlist.Tracks}
            
            transfers = 0
            for path in renamed_files:
                current_title = path.stem
                if current_title.lower().strip() not in existing_tracks:
                    yield log(f"  📥 iTunes Import: {current_title}")
                    
                    # Le fichier est importé avec son nom et son tag déjà synchronisés
                    operation = playlist.AddFile(str(path.resolve()))
                    if operation:
                        while operation.InProgress:
                            time.sleep(0.3)
                    
                    # Force la base iTunes pour être raccord avec le nouveau nom
                    time.sleep(0.5)
                    count = playlist.Tracks.Count
                    if count > 0:
                        last_t = playlist.Tracks.Item(count)
                        last_t.Name = current_title
                        last_t.Artist = folder.name
                        last_t.Album = folder.name
                    
                    transfers += 1
                else:
                    yield log(f"  🆗 Already in Playlist: {current_title}")

            if transfers > 0:
                yield log("💾 Updating iPod database...")
                try: ipod.Update()
                except: pass

            yield log("🔌 Operation Finished. DONE")

        except Exception as e:
            yield log(f"❌ Critical Error: {str(e)}")
        finally:
            is_busy = False
            pythoncom.CoUninitialize()

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    return jsonify({"ok": True})

@app.route("/api/list-playlist-tracks", methods=["POST"])
def list_playlist_tracks():
    pl_name = request.json.get("playlist", "")
    itunes, ipod = get_ipod()
    if not ipod:
        pythoncom.CoUninitialize()
        return jsonify({"tracks": [], "error": "iPod not connected"})
    try:
        playlist = next((p for p in ipod.Playlists if p.Name == pl_name), None)
        if not playlist:
            return jsonify({"tracks": [], "error": "Playlist not found"})
        tracks = []
        for i in range(1, playlist.Tracks.Count + 1):
            try:
                t = playlist.Tracks.Item(i)
                tracks.append({"name": t.Name, "artist": t.Artist, "duration": t.Duration})
            except: continue
        return jsonify({"tracks": tracks, "count": len(tracks)})
    except Exception as e:
        return jsonify({"tracks": [], "error": str(e)})
    finally:
        pythoncom.CoUninitialize()

@app.route("/api/list-mp3", methods=["POST"])
def list_mp3():
    folder = Path(request.json.get("folder", ""))
    files = list(folder.glob("*.mp3"))
    return jsonify({"count": len(files)})

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

@app.route("/")
def index():
    path = resource_path("index.html")
    return open(path, encoding="utf-8").read()

# --- SERVER RUNNER ---
def run_flask():
    app.run(port=5000, threaded=True, debug=False, use_reloader=False)

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_flask, daemon=True)
    server_thread.start()

    window = webview.create_window(
        title=APP_TITLE,
        url="http://localhost:5000",
        width=900,
        height=700,
        resizable=True,
        maximized=True,
        min_size=(600, 800)
    )
    
    webview.start()
    sys.exit(0)
