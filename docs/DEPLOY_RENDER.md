# Uhamishaji kwenda Render (Deploy to Render)

Runbook hii inaeleza hatua za kuhamisha **Madras_Webapp** kutoka PythonAnywhere
kwenda **Render** (PostgreSQL + Cloudinary media), bila kupoteza data.

> Kabla ya kuanza, soma pia [DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md)
> kwa muktadha wa mradi na mpango wa zamani.

## 1. Maandalizi ya ndani (Local preparation)

- Install Python dependencies:

  ```
  py -m pip install -r requirements.txt
  ```

- Run Django checks:

  ```
  py manage.py check
  ```

- Run critical tests:

  ```
  py manage.py test usimamizi.tests.test_db_settings
  py manage.py test usimamizi.tests.test_media_auth
  ```

- If Flutter SDK is available, run:

  ```
  flutter analyze
  flutter test
  ```

## 2. Hifadhi nakala za PythonAnywhere (Backup PythonAnywhere)

Fanya haya **kabla** ya kugusa chochote kwenye PythonAnywhere:

- Download `db.sqlite3` from PythonAnywhere Files.
- Download or zip the media folder from PythonAnywhere Files.
- Record the current PythonAnywhere git commit:

  ```
  git rev-parse HEAD
  ```

- Keep these backups **outside** PythonAnywhere (e.g., on your PC or another drive).

## 3. Sukuma code mpya GitHub (Push to GitHub)

- Commit the staged changes.
- Push to `main`.

## 4. Sasisha PythonAnywhere kwa muda (Temporary update)

Hatua hii inatayarisha PythonAnywhere kuendesha command za uhamishaji tu.

- In PythonAnywhere **Bash**, go to the project folder.
- Pull the latest code from GitHub:

  ```
  git pull
  ```

- Install updated requirements:

  ```
  pip install -r requirements.txt
  ```

- Reload the PythonAnywhere web app.
- If the site breaks, restore the previous git commit and reinstall the
  previous requirements.

## 5. Sanidi Cloudinary kwa muda kwenye Bash (Temporary Cloudinary)

- Create a Cloudinary account if not already created.
- In the **PythonAnywhere Bash session only**, export:

  ```
  export CLOUDINARY_CLOUD_NAME="..."
  export CLOUDINARY_API_KEY="..."
  export CLOUDINARY_API_SECRET="..."
  ```

- **Do not** put these values into the public website config yet.

## 6. Hamisha media za zamani kwenda Cloudinary (Migrate media)

- First run dry-run:

  ```
  python manage.py migrate_media_to_cloudinary --dry-run --verbose
  ```

- Then run a small test with a limit:

  ```
  python manage.py migrate_media_to_cloudinary --limit 5 --verbose
  ```

- Then run the full migration:

  ```
  python manage.py migrate_media_to_cloudinary --verbose
  ```

- If some assets already exist and you want to replace them, use:

  ```
  python manage.py migrate_media_to_cloudinary --overwrite --verbose
  ```

## 7. Toa backup ya database kutoka PythonAnywhere (Export data)

- Run:

  ```
  python manage.py export_madrasa_data --output madrasa_backup.json
  ```

- Download `madrasa_backup.json` from PythonAnywhere Files.

## 8. Unda akaunti ya Render na deploy (Render deploy)

- Create a Render account.
- Connect GitHub.
- Create a new Blueprint/Web Service from the repository.
- Render should detect `render.yaml`.
- Deploy initially **WITHOUT** Cloudinary environment variables. Leave
  `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET`
  empty.

## 9. Ingiza data kwenye Render PostgreSQL (Import data)

- Open **Render Shell**.
- Upload `madrasa_backup.json`.
- Run:

  ```
  python manage.py import_madrasa_data --input madrasa_backup.json --migrate
  ```

- Confirm the command reports successful `loaddata` and the PostgreSQL
  sequence reset (e.g., "Sequences za PostgreSQL zilizorekebishwa: N, ...").

## 10. Thibitisha Render kabla ya Cloudinary (Verify first)

- Open the Render URL.
- Test login.
- Test the student list.
- Test attendance.
- Test fees.
- Test one PDF report.
- Media may not work fully yet because Cloudinary env vars are not set on
  Render. **That is expected.**

## 11. Wezesha Cloudinary kwenye Render (Enable Cloudinary)

- In **Render Environment Variables**, set:
  - `CLOUDINARY_CLOUD_NAME`
  - `CLOUDINARY_API_KEY`
  - `CLOUDINARY_API_SECRET`
- Redeploy or restart the Render service.
- Verify student/teacher photos and Nyenzo files load through `/media/`.
- Verify PDF reports that include images.

## 12. Jenga app ya Flutter (Build Flutter app)

- Use the **actual Render URL**.
- Either update `apps/mobile/lib/config.dart`, or build with:

  ```
  flutter build apk --dart-define=API_BASE_URL=https://your-real-render-url.onrender.com
  ```

- Test the APK on mobile data, especially **Halotel**.

## 13. Mpango wa kurudi nyuma (Rollback plan)

- Keep PythonAnywhere running until Render is fully verified.
- If Render fails, continue using PythonAnywhere on Wi-Fi.
- If PythonAnywhere breaks after pulling the new code, revert to the recorded
  previous git commit and reinstall the previous requirements.
- Do **not** delete the PythonAnywhere backups until Render has been stable
  for several days.

## 14. Maonyo muhimu (Important warnings)

- Do **not** enable Cloudinary on Render before legacy media has been uploaded
  to Cloudinary (hatua 6).
- The Render free tier can sleep after inactivity.
- Render free PostgreSQL may have expiration/backup limitations; download
  database backups regularly.
- Never commit `.env`.
- Never commit `db.sqlite3`.
- Never commit `media/` or `staticfiles/`.
