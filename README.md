# Dosely

Dosely is a medication-reminder prototype built with Python, Kivy, and KivyMD. It lets you keep a local medication list and schedule reminders while the app is running.

## Implemented

- Add and edit medication names, strengths, notes, and reminder intervals.
- Search a small sample catalog by medication name or active ingredient.
- Store entries in local JSON files.
- Schedule notifications through Plyer.

## Run locally

Use Python 3.11 and a virtual environment. From the repository directory:

```bash
python -m venv .venv
```

Activate `.venv` with `.\.venv\Scripts\Activate.ps1` on Windows PowerShell or `source .venv/bin/activate` on macOS/Linux. Then run:

```bash
python -m pip install "kivy==2.3.0" "kivymd==1.2.0" "plyer==2.1.0"
python main.py
```

Run from the project root so the app can find `ui.kv` and `storage/`.

## Status

The notification scheduler uses in-process timers. It does not provide a persistent background alarm service, and saved reminders are not automatically rescheduled on startup. Notification behavior also depends on the platform.

The repository does not currently include an Android build configuration or release APK. Dose-history tracking and adherence reports are not implemented.

## Screenshots

<img width="300" alt="Dosely application screenshot 1" src="https://github.com/user-attachments/assets/31a71831-7e94-438e-8a8a-5a6c604905f0" />
<img width="300" alt="Dosely application screenshot 2" src="https://github.com/user-attachments/assets/c4420af7-3c1a-4813-9049-b67c63d2f4ba" />
<img width="300" alt="Dosely application screenshot 3" src="https://github.com/user-attachments/assets/33a19962-439b-4859-9025-62aac5029177" />
<img width="300" alt="Dosely application screenshot 4" src="https://github.com/user-attachments/assets/c0010eb4-e229-41eb-9880-48ea3a1bdadc" />

## Files

- `main.py`: forms, navigation, and reminder scheduling.
- `backend.py`: JSON storage and catalog search.
- `notify.py`: notification helpers and timers.
- `ui.kv`: interface layout.
