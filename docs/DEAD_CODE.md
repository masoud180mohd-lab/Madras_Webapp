# Dead-code decisions (M-010+)

| Item | Decision | Rationale |
|------|----------|-----------|
| `RekodiMaendeleoMchana` | **Restored** (migration `0017`) with full UI | Was removed as orphan; now wired: somo → orodha → rekodi → ripoti (+ profile). |
| `ripoti_pdf_template.html` + `ripoti_pdf.css` | **Removed** | Unreferenced; live PDFs use `pdf_mahudhurio.html`, `pdf_sabaq.html`, `pdf_matokeo*.html`, `pdf_risiti.html`. |
| DRF + `/api-token-auth/` | **Kept installed, URL gated** | Authtoken tables may already exist; endpoint off unless `DJANGO_ENABLE_TOKEN_AUTH=True`. See [API.md](API.md). |
