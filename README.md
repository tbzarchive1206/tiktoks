# THE BOYZ TikTok Archive

Statyczna strona zgodna z GitHub Pages. Dane w `data.js` są automatycznie odświeżane z publicznych folderów Google Drive co 6 godzin oraz po ręcznym uruchomieniu workflow.

## Jednorazowa konfiguracja

1. W Google Cloud włącz **Google Drive API** i utwórz klucz API.
2. W repozytorium GitHub przejdź do **Settings → Secrets and variables → Actions**.
3. Dodaj sekret repozytorium o nazwie `GOOGLE_DRIVE_API_KEY` i wklej klucz.
4. W zakładce **Actions** uruchom workflow **Update TikTok archive** przez **Run workflow**.

Foldery na Drive muszą pozostać publicznie dostępne. Po dodaniu filmu generator przebuduje `data.js`; GitHub Pages opublikuje zmienioną stronę z tego samego brancha.

## Ręczne odświeżenie

**Actions → Update TikTok archive → Run workflow**.

Nie edytuj ręcznie `data.js`, bo kolejne odświeżenie zastąpi te zmiany. Logikę synchronizacji można zmieniać w `scripts/update_tiktok_data.py`.
