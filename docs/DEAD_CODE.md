# Dead-code decisions (M-010)

| Item | Decision | Rationale |
|------|----------|-----------|
| `RekodiMaendeleoMchana` | **Removed** (migration `0013`) | Never wired to views, forms, admin, or templates. Day-progress parity with sabaq stays a future feature if needed. |
| `ripoti_pdf_template.html` + `ripoti_pdf.css` | **Removed** | Unreferenced; live PDFs use `pdf_mahudhurio.html`, `pdf_sabaq.html`, `pdf_matokeo*.html`, `pdf_risiti.html`. |
| DRF + `/api-token-auth/` | **Kept installed, URL gated** | Authtoken tables may already exist; endpoint off unless `DJANGO_ENABLE_TOKEN_AUTH=True`. See [API.md](API.md). |

Reintroduce day-class progress only with a full UI flow (not a silent model).
