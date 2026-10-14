# ⚡ 寶可夢冒險（Streamlit 版）

回合制寶可夢粉絲遊戲：選擇御三家、野外捕捉、屬性相剋、升級進化、4 場道館挑戰、商店、電腦箱、圖鑑、存檔/讀檔。

## 本機執行
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 部署到 Streamlit Community Cloud（免費、永久網址）
1. 在 GitHub 建立一個 **Public** repository，把這個資料夾的檔案（`app.py`、`requirements.txt`、`.streamlit/config.toml`）上傳到根目錄。
2. 到 https://share.streamlit.io 用 GitHub 帳號登入。
3. 點 **Create app** → **Deploy a public app from GitHub**。
4. 選擇 repository、branch（`main`），Main file path 填 `app.py`。
5. 在 **App URL** 可以自訂網址，例如 `my-pokemon.streamlit.app`。
6. 按 **Deploy**，等 1～2 分鐘就完成了。

> 免費方案的 App 若一段時間沒人使用會進入休眠，網址仍然有效；有人打開時點「Yes, get this app back up」即可喚醒。
> 遊戲進度只存在瀏覽器分頁中，請用「💾 存檔」分頁下載存檔檔案。
