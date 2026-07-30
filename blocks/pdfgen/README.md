# PDF Generation Block

PDF generation — invoices, reports, and certificates from HTML templates with QR code and barcode support via WeasyPrint.

**Triggers**: pdf, invoice, report, print, receipt, document, certificate, bill

**Env vars**:
| Variable | Default | Description |
|----------|---------|-------------|
| `PDF_STORAGE` | `data/pdfs` | Directory for generated PDFs |

**API endpoints**: `/api/pdf/generate`, `/api/pdf/templates`, `/api/pdf/invoice`

**Dependencies**: `pip: weasyprint>=60.0.0, qrcode>=7.4.0`
