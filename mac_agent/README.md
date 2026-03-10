# Mac Mini Time Limit Agent

在 Mac Mini 上安裝後，會自動：
- 連到 Windows 的 edu 教育 app 伺服器，同步剩餘時間
- 每 60 分鐘彈出 macOS 原生 **TIME LIMIT** 彈窗提醒
- 時間耗盡時強制關閉 Safari / Chrome 等瀏覽器

## 安裝步驟（在 Mac Mini 上執行）

### 1. 把整個 `mac_agent` 資料夾複製到 Mac Mini

用 AirDrop、USB 或 scp 都行：
```bash
scp -r mac_agent/ 你的mac使用者@mac-mini-ip:~/EduApp/
```

### 2. 執行安裝腳本（只需一次）

```bash
cd ~/EduApp/mac_agent
chmod +x setup.sh
./setup.sh
```

安裝過程會問：
- Windows PC 的 IP（手機控制頁面顯示的 IP）
- 每次最長使用幾分鐘（預設 60 分鐘）

安裝完畢後 Agent **開機自動啟動**。

---

## 手動執行（不自動啟動）

```bash
python3 mac_time_agent.py --server http://192.168.1.100:5050 --limit 60
```

---

## 彈窗說明

| 觸發條件 | 動作 |
|---------|------|
| 剩餘 10 / 5 / 1 分鐘 | macOS 通知橫幅提醒 |
| 連續使用滿 60 分鐘 | 🚨 強制關閉瀏覽器 + 大彈窗 |
| Windows 端時間歸零 | 🚨 強制關閉瀏覽器 + 大彈窗 |

彈窗有「我知道了」和「繼續使用（家長同意）」兩個按鈕。
按「繼續使用」則計時器重置，可再用 60 分鐘。

---

## 查看日誌

```bash
tail -f ~/Library/Logs/EduApp/agent.log
```

## 停止 Agent

```bash
launchctl unload ~/Library/LaunchAgents/com.eduapp.timeagent.plist
```
