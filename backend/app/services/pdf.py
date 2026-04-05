import os
from decimal import Decimal

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.plan import Plan

# Template directory
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


def generate_invoice_pdf(
    invoice: Invoice,
    customer: Customer,
    plan: Plan,
    payments: list,
    total_paid: Decimal,
    branding: dict | None = None,
) -> bytes:
    """Generate a PDF invoice and return bytes."""
    template = env.get_template("invoice.html")
    balance = invoice.amount - total_paid

    # Resolve logo URL to absolute file path for WeasyPrint
    brand = dict(branding or {})
    logo_url = brand.get("company_logo_url", "")
    if logo_url:
        # Convert web path /api/v1/uploads/file.png → file:///app/uploads/file.png
        filename = logo_url.rsplit("/", 1)[-1]
        file_path = os.path.join("/app/uploads", filename)
        if os.path.exists(file_path):
            brand["company_logo_url"] = f"file://{file_path}"
        else:
            brand["company_logo_url"] = ""

    html_content = template.render(
        invoice=invoice,
        customer=customer,
        plan=plan,
        payments=payments,
        total_paid=total_paid,
        balance=balance,
        branding=brand,
    )

    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
