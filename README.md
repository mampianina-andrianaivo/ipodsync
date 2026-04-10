# ipodsync
Sync your playlists the lazy way. For people who don't care about arranging tracks and just want their music on their iPod, now.

# 🎧 iPod LazySync OS

**"Sync your playlist in very lazy way (for lazy people who doesn't care about playlist arranging)."**

### 🚀 The "Lazy" Philosophy
This app is designed for users who hate the rigid structure of the iTunes Library. If you are used to the **"Drag & Drop"** life and you don't want to spend hours pre-arranging playlists in your library before syncing them to your device, this is for you.

**The goal:** You have a folder on your PC. You want it as a playlist on your iPod. You click one button. Done.

---

## ✨ Key Features

* **Lazy Syncing:** No need to manually import songs into iTunes first. The app bridge your local folders directly to the device.
* **Automatic Sanitization (Slugify):** Automatically renames files into a clean format (e.g., `my_song_track.mp3`) to avoid file system errors.
* **Automatic Tagging:** The app overwrites ID3 tags (Title, Artist, Album) to match the folder name. This ensures a perfectly uniform display on your iPod and simplifies your playlist view.
* **Smart Duplicate Linker:** If a song already exists in the iPod's library, the app creates a link instead of re-uploading, saving time and storage.
* **Deep Physical Purge:** A dedicated maintenance tool to completely wipe a playlist and its associated files from the iPod's physical memory.

---

## 🛠 Prerequisites & Setup

### 1. iTunes Configuration (CRITICAL)
For this tool to work, your iPod **MUST** be configured for manual management:
1.  Connect your iPod to your PC and open iTunes.
2.  Go to the **Summary** tab of your device.
3.  Check the box: **"Manually manage music and videos"** (or *"Gérer manuellement la musique et les vidéos"*).
4.  Disable any automatic synchronization.

### 2. Environment
* **OS:** Windows (Requires iTunes for Windows installed).
* **Software:** iTunes must be running in the background.
* **Python:** Version 3.10+ recommended.

### 3. Installation
```bash
# Clone the repository
git clone [https://github.com/your-username/iPod-LazySync.git](https://github.com/your-username/iPod-LazySync.git)

# Install dependencies
pip install flask pywin32 mutagen
