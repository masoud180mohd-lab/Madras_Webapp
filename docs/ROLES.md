# Majukumu na ruhusa (AuthZ)

Mfumo unatumia **cheo cha Mwalimu** pamoja na **Django model permissions** (kwa ofisi).

## Majukumu

| Cheo | Capabilities |
|------|----------------|
| **Mwalimu Mkuu** | Zote (students, attendance, sabaq, exams, fees, materials, mseto, directories) |
| **Mwalimu wa Kawaida** | View students, attendance, sabaq, exams, materials, directory — **si** fees wala usajili wa wanafunzi (isipokuwa Django perm) |
| **Jaji** | View students, exams, mseto/results, directory — **si** fees, attendance write, sabaq |
| **Ofisi** (User bila Mwalimu) | Kupitia Django perms pekee (`add_malipo`, `view_mwanafunzi`, n.k.) |

Utekelezaji: [`usimamizi/permissions.py`](../usimamizi/permissions.py).

## Reads nyeti

- Wasifu / ripoti / PDF za mwanafunzi → `view_students`
- Malipo / risiti → `fees`
- Matokeo / PDF / CSV za mtihani → `exams` / `mseto`
- Mwaka / muhula (`/madrasa/mwaka/`) → `mseto` (Mkuu + Jaji)
- Ukaguzi (`/madrasa/ukaguzi/`) → `manage_students` au `fees` (nani alirekodi mahudhurio/malipo)
- Mawasiliano / call log (`/madrasa/mawasiliano/`) → `parent_contact` (Mkuu; ofisi yenye `fees` au ruhusa za `RekodiSimuMzazi`)

## Wasifu wa Mwalimu

- **Sabaq** inahitaji `Mwalimu` aliyeunganishwa na User — ujumbe wa Kiswahili + redirect (si 404).
- **Malipo** yanaweza kuwekwa na ofisi bila wasifu; `mpokeaji` inaweza kuwa tupu.
