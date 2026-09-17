# TaskHub Android

Native Android client for the TaskHub FastAPI backend.

## Run locally

1. Open the `android` directory in Android Studio.
2. Start the backend from the repository root:

   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0
   ```

3. Run the app on an Android emulator.

The debug build connects to `http://10.0.2.2:8000/`, which is the emulator
alias for the host computer. A physical device needs the computer's LAN IP or
an HTTPS deployment; change `API_BASE_URL` in `app/build.gradle.kts`.

The first MVP uses user ID `1` until authentication is added. Cleartext HTTP is
enabled only for local development and must be removed before production.
