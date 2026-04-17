# ✨ Read this readme first please

# 🎧 iPod LazySync OS

**"Sync your playlists the lazy way (for people who don't care about library management)."**

---

## 🚀 The "Lazy" Philosophy
This app is designed for users who hate the rigid structure of the iTunes Library. If you are used to the **"Drag & Drop"** life and you don't want to spend hours pre-arranging playlists in your library before syncing them to your device, this is for you.

**The goal:** You have a folder on your PC. You want it as a playlist on your iPod. You click two buttons. Done. 

> **Note for the non-lazy:** If you care about your original file names or your hyper-detailed ID3 tags, **stay away**. This tool is for those who value speed and "iPod-ready" grouping over metadata preservation. If you want strict library management, stick to the standard iTunes way.

---

## ⚠️ File Integrity & "Lazy" Trade-off
**This app performs destructive metadata and filesystem operations.**

* It **permanently renames** your physical files on Windows to a clean format.
* It **overwrites** internal ID3 tags (Title, Artist, Album) to force perfect iPod grouping.
* **The "Source of Truth" is the file name:** The app takes what you named your file on Windows and forces it as the song title.
* **Automatic Artwork Injection:** The app forces a hardcoded **Base64 image** into every track's metadata. This ensures you never see a blank screen on your iPod.
    * **Note:** You are free to change this image in the code (Base64 string). We recommend using an image under **35kb** to keep the process fast and avoid UI lag on the iPod. Many websites allow you to convert PNG/JPEG to Base64.
* **Why?** Because a "lazy" user doesn't want to see "Unknown Artist" or 50 different albums for one folder. We clean everything so you don't have to. 
* **Maybe backup:** If you are not sure, I advise you to backup your music folder before a first sync if you aren't sure. **(But then again, a true lazy user probably won't).**

---

## ✨ Key Features

* **Lazy Syncing:** No need to manually import songs into iTunes first.
* **Random Discovery:** Generate instant discovery playlists (10, 20, 50 tracks) from your existing iPod library at the click of a button.
* **Strict Waterfall Sequence:** Windows finishes 100% of the work (renaming + tagging + artwork injection) before iTunes is even authorized to touch the files.
* **Physical Filename Authority:** The filename on your disk becomes the *Title* on your iPod.
* **Automatic Sanitization (Slugify):** No more special characters, emojis, or sync-breaking symbols in your filenames.
* **Folder-to-Group Logic:** The folder name is automatically injected as the *Artist*, *Album* and *Playlist name* newly created, ensuring perfect sorting on the device.
* **Deep Physical Purge:** A dedicated tool to wipe a playlist and its associated physical files from the iPod's memory to free up space.

---

## ⚙️ How it works (The Strict Technical Flow)

To guarantee that your iPod displays exactly what you see in your Windows folder, the app follows a non-negotiable sequence:

0. **Tested on iPod Shuffle 4th Gen, Nano 6th Gen and Nano 7th Gen.**

1.  **Phase 1: Windows Physical Preparation (Isolated)**
    * **Rename First:** Files are renamed physically on your disk.
    * **Tag Second:** The new filename is written into the *Title* tag. *Artist* and *Album* are overwritten by the local folder name.
    * **Artwork Third:** The Base64 image is injected directly into the file metadata.
    * **Cool Down:** A system pause ensures Windows flushes all file handles and disk writes.
2.  **Phase 2: iTunes Authorization**
    * Only now is the iTunes COM bridge initialized.
3.  **Phase 3: Secure Transfer**
    * Files are imported. Since they are already "perfect" on disk, iTunes reads the metadata directly from the file. We no longer force iTunes to replace artwork via API as the file itself already carries it.

---

## 🕹️ Interface Guide

When you launch the app, the interface will open automatically.

### **01 / DEVICE**
* **BROWSE FOLDER:** Pick your local music source. Once selected, the path appears in the "Path Box".
* **COPY:** Copies the current folder path to your clipboard.
* **IPOD STATUS:** Real-time heartbeat detection (Green/Grey dot) to check if your device is connected.

### **02 / ACTIONS**
* **LAUNCH SYNC:** Starts the "Waterfall" sequence. Only active when a folder and iPod are ready.

### **03 / MAINTENANCE**
* **Playlist Dropdown:** Select any existing playlist on your iPod.
* **Refresh ↱↲ :** Force a re-scan of the device's playlists.
* **List ☰:** Lists every track inside the selected playlist in the terminal.
* **Delete playlist ✖:** * Delete the playlist you have selected from the dropdown menu. If the playlist starts with `RANDOMX`: It only removes the playlist container (songs stay on the iPod).
    * For normal folders: It triggers a **Confirm Purge** and physically deletes the MP3s from the iPod's storage.
* **RANDOM BUTTONS (10 or 20):** Instantly creates a new playlist (named `RANDOMX...`) with random songs from your library. These lists do not modify your existing tags.
* **CLEAN ORPHANS AND TAGS:** Scans for "ghost" files and fixes logical inconsistencies. It also corrects tags but **automatically ignores `RANDOMX` playlists** to preserve your original music organization.

---

## 🛠 Prerequisites & Setup

### 1. iTunes Configuration (CRITICAL)
Your iPod **MUST** be configured for manual management:
1.  Connect your iPod and open iTunes.
2.  Go to **Summary** > Check **"Manually manage music and videos"**.
3.  Disable any automatic synchronization.

### 2. Dependencies

`pip install flask pywin32 mutagen`

---

## 📦 Compilation & Versions

#### 1. Why 2 scripts ?
Depending on how you want the app to behave, use one of these two scripts:

| Script | Version | Behavior |
| :--- | :--- | :--- |
| `server_lite.py` | **Lite** | Starts a background Flask server and opens your **default web browser** (Chrome, Edge, etc.) to show the UI. ~25Mo .exe file output|
| `server_webv.py` | **Big / Standalone** | Uses the `pywebview` library to open the UI in a **dedicated, independent window** (no browser tabs/bars). It feels like a native Windows App. ~130Mo .exe file output|

#### 2. Build Commands (PyInstaller)

**For Lite version:**
`pyinstaller --noconfirm --onefile --windowed --name "iPod_Manager_Lite4" --add-data "index.html;." --exclude-module "webview" --hidden-import "win32com.client" --hidden-import "pythoncom" server_lite.py`

**For WebV version:**
`pyinstaller --noconsole --onefile --name "iPod_Manager_Big4" --add-data "index.html;." server_webv.py`
