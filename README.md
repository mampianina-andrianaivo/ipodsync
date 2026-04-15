# ✨ Read this readme first please

# 🎧 iPod LazySync OS

**"Sync your playlists the lazy way (for people who don't care about library management)."**

---

## 🚀 The "Lazy" Philosophy
This app is designed for users who hate the rigid structure of the iTunes Library. If you are used to the **"Drag & Drop"** life and you don't want to spend hours pre-arranging playlists in your library before syncing them to your device, this is for you.

**The goal:** You have a folder on your PC. You want it as a playlist on your iPod. You click one button. Done. 

> **Note for the non-lazy:** If you care about your original file names or your hyper-detailed ID3 tags, **stay away**. This tool is for those who value speed and "iPod-ready" grouping over metadata preservation. If you want strict library management, stick to the standard iTunes way.

---

## ⚠️ File Integrity & "Lazy" Trade-off
**This app performs destructive metadata and filesystem operations.** * It **permanently renames** your physical files on Windows to a clean format.
* It **overwrites** internal ID3 tags (Title, Artist, Album) to force perfect iPod grouping.
* **The "Source of Truth" is the file name:** The app takes what you named your file on Windows and forces it as the song title.
* **Why?** Because a "lazy" user doesn't want to see "Unknown Artist" or 50 different albums for one folder. We clean everything so you don't have to. 
* **Backup:** Always backup your music folder before a first sync if you aren't sure. (But then again, a true lazy user probably won't).

---

## ✨ Key Features

* **Lazy Syncing:** No need to manually import songs into iTunes first.
* **Strict Waterfall Sequence:** Windows finishes 100% of the work (renaming + tagging) before iTunes is even authorized to touch the files.
* **Physical Filename Authority:** The filename on your disk becomes the *Title* and *Playlist name* newly created on your iPod.
* **Automatic Sanitization (Slugify):** No more special characters, emojis, or sync-breaking symbols in your filenames.
* **Folder-to-Group Logic:** The folder name is automatically injected as the *Artist* and *Album*, ensuring perfect sorting on the device.
* **Deep Physical Purge:** A dedicated tool to wipe a playlist and its associated physical files from the iPod's memory to free up space.

---

## ⚙️ How it works (The Strict Technical Flow)

To guarantee that your iPod displays exactly what you see in your Windows folder, the app follows a non-negotiable sequence:

1.  **Phase 1: Windows Physical Preparation (Isolated)**
    * **Rename First:** Files are renamed physically on your disk.
    * **Tag Second:** The new filename is written into the *Title* tag. *Artist* and *Album* are overwritten by the local folder name.
    * **Cool Down:** A system pause ensures Windows flushes all file handles and disk writes.
2.  **Phase 2: iTunes Authorization**
    * Only now is the iTunes COM bridge initialized.
3.  **Phase 3: Secure Transfer**
    * Files are imported. Since they are already "perfect" on disk, iTunes cannot mess up the metadata or display old cached information.

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
* **↻ (Refresh):** Force a re-scan of the device's playlists.
* **👁 (View):** Lists every track inside the selected playlist in the terminal.
* **DELETE PLAYLIST:** Triggers a **Confirm Purge**. This physically deletes the MP3s from the iPod's storage.
* **CLEAN ORPHANS AND TAGS:** Scans for "ghost" files and fixes logical inconsistencies.

---

## 🛠 Prerequisites & Setup

### 1. iTunes Configuration (CRITICAL)
Your iPod **MUST** be configured for manual management:
1.  Connect your iPod and open iTunes.
2.  Go to **Summary** > Check **"Manually manage music and videos"**.
3.  Disable any automatic synchronization.

### 2. Dependencies
```bash
pip install flask pywin32 mutagen
