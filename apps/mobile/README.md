# Madrasa Mobile (P1)

Staff Android app: **ingia**, **madarasa**, **mahudhurio** (roll call) na picha za wanafunzi.

API: `https://rasulillahmadras.pythonanywhere.com/api/v1/`

## Mahitaji

1. Flutter SDK (`flutter --version`)
2. Android SDK / emulator au simu

Ikiwa folder `android/` haipo bado:

```bash
cd apps
flutter create --org tz.rasulillah --project-name madrasa_mobile mobile
```

Kisha usiifute `lib/` iliyopo — `flutter create` inahifadhi source.

## Endesha

```bash
cd apps/mobile
flutter pub get
flutter test
flutter run --dart-define=API_BASE_URL=https://rasulillahmadras.pythonanywhere.com
```

Lab (emulator → PC):

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Akaunti ni zile zile za tovuti (Mwalimu wa Kawaida / Mkuu / Jaji).
