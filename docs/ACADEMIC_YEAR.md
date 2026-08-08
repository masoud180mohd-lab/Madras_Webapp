# Mwaka wa masomo na muhula (M-009)

Mfumo sasa una kipindi cha kitaaluma kinachounganisha ripoti za mitihani.

## Miundo

- **MwakaWaMasomo** — mfano `2025/2026`; moja inaweza kuwa `ni_hai`
- **Muhula** — muhula 1/2/3 ndani ya mwaka; moja inaweza kuwa `ni_hai`
- **MsetoMtihani.muhula** — mseto wa darasa unaunganishwa (hiari) na muhula

## Matumizi

1. Admin: **Mwaka wa masomo** (+ muhula inline) au ukurasa wa app `/madrasa/mwaka/`
2. Mwalimu Mkuu / Jaji (`CAP_MSETO`): weka mwaka/muhula hai
3. Unda mseto wa darasa — fomu inapendekeza muhula hai na jina lake
4. Ripoti ya jumla inaendelea kutoka mseto; muhula ni backbone ya ripoti kwa miaka

## Seed

Migration `0012_academic_year_term` inaunda mwaka wa kalenda ya sasa + Muhula 1 (hai) na Muhula 2 ikiwa hakuna data bado.

## Promotion (hamisha darasa) — M-012

Mwisho wa mwaka: **Hamisha darasa** (`/madrasa/hamisha-darasa/`, Mkuu tu) — menyu: **Mwaka wa masomo → Hamisha darasa**.

1. Chagua darasa la **kutoka**
2. Chagua darasa la **kwenda** + wanafunzi hai
3. **Endelea kuthibitisha** → **Thibitisha uhamisho**
4. `Mwanafunzi.darasa` inasasishwa kwa transaction; ukaguzi `hamisha_darasa` unaandikwa

Wanafunzi waliotunzwa (archive) hawaonyeshwi. Hakuna historia tofauti ya darasa bado — ukaguzi ni audit trail.
