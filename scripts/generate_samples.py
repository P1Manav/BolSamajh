"""Generate sample documents for BolSamajh demo and tests."""

import os
from pathlib import Path
import fitz  # PyMuPDF

def generate_sample_pdf(output_path: Path):
    doc = fitz.open()
    
    # Page 1: Coverage and Inpatient Care
    p1 = doc.new_page()
    text_p1 = (
        "Bharat Swasthya Shield Health Insurance Policy (Policy No: BSS-2026-9921)\n\n"
        "SECTION 1: OVERVIEW AND INPATIENT HOSPITALIZATION\n"
        "1.1 Sum Insured: The basic annual sum insured under this tier is Rs 10,00,000 (Ten Lakh Rupees).\n"
        "1.2 Inpatient Hospitalization: Hospitalization expenses incurred for a minimum period of 24 consecutive hours are covered.\n"
        "1.3 Room Rent Limits: Normal room rent is capped at 1% of the Sum Insured per day (Rs 10,000 per day).\n"
        "1.4 ICU Room Charges: Intensive Care Unit (ICU) charges are 100% covered up to a maximum limit of 2% of the Sum Insured per day (Rs 20,000 per day).\n"
        "1.5 Pre and Post Hospitalization: Medical expenses incurred 60 days immediately prior to hospitalization and 90 days immediately following hospital discharge are admissible for reimbursement.\n"
        "1.6 Emergency Ambulance: Ambulance transportation charges are covered up to Rs 2,500 per hospitalization.\n\n"
        "Disclaimer: This document is a synthetic policy schedule provided solely for software demonstration and benchmark verification. It does not constitute professional legal, medical, or financial advice."
    )
    p1.insert_textbox(fitz.Rect(50, 50, 550, 750), text_p1, fontsize=11)

    # Page 2: Waiting Periods and Special Coverages
    p2 = doc.new_page()
    text_p2 = (
        "Bharat Swasthya Shield Health Insurance Policy (Policy No: BSS-2026-9921)\n\n"
        "SECTION 2: SPECIAL TREATMENTS AND WAITING PERIODS\n"
        "2.1 Initial Waiting Period: A mandatory 30-day waiting period applies from the policy inception date for all illnesses except accidental bodily injuries.\n"
        "2.2 Pre-existing Diseases (PED): Pre-existing diseases are covered after an uninterrupted waiting period of 36 continuous months.\n"
        "2.3 Maternity Benefits: Maternity expenses are covered up to a maximum ceiling of Rs 50,000 per delivery after a continuous waiting period of 24 months, limited to two living children.\n"
        "2.4 Cataract Treatment: Cataract surgery expenses are capped at a maximum of Rs 40,000 per eye.\n"
        "2.5 AYUSH Inpatient Treatment: Inpatient treatment under Ayurveda, Yoga, Unani, Siddha, and Homeopathy in government-recognized institutions is covered up to 100% of the Sum Insured.\n"
        "2.6 Day Care Procedures: Medical treatments requiring less than 24 hours of hospitalization due to modern technological advancements (e.g. Dialysis, Chemotherapy, Radiotherapy) are fully covered.\n\n"
        "Disclaimer: This document is a synthetic policy schedule provided solely for software demonstration and benchmark verification. It does not constitute professional legal, medical, or financial advice."
    )
    p2.insert_textbox(fitz.Rect(50, 50, 550, 750), text_p2, fontsize=11)

    # Page 3: Permanent Exclusions and Claims
    p3 = doc.new_page()
    text_p3 = (
        "Bharat Swasthya Shield Health Insurance Policy (Policy No: BSS-2026-9921)\n\n"
        "SECTION 3: PERMANENT EXCLUSIONS AND CLAIM PROCEDURES\n"
        "3.1 General Exclusions: The insurer shall not be liable to make any payment for:\n"
        "    (a) Cosmetic, aesthetic, or plastic surgeries unless necessitated by accidental trauma or burn injuries.\n"
        "    (b) Dental surgeries and treatments, unless resulting from external accidental impact requiring inpatient stay.\n"
        "    (c) Self-inflicted injuries, suicide attempts, or conditions arising from substance abuse and alcohol toxicity.\n"
        "    (d) Experimental or unproven medical therapies, robotic treatments without prior TPA authorization, and space travel or active warfare injuries.\n"
        "3.2 Cashless Claim Settlement: Cashless authorization requests must be submitted to the Network Hospital TPA desk at least 48 hours prior to planned admission, or within 24 hours of emergency admission. Pre-authorization is processed within 6 hours.\n"
        "3.3 Reimbursement Claims: All original bills, pharmacy invoices, diagnostic reports, and final hospital discharge summaries must be submitted within 15 calendar days from the date of discharge.\n\n"
        "Disclaimer: This document is a synthetic policy schedule provided solely for software demonstration and benchmark verification. It does not constitute professional legal, medical, or financial advice."
    )
    p3.insert_textbox(fitz.Rect(50, 50, 550, 750), text_p3, fontsize=11)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    doc.close()
    print(f"Generated sample PDF at {output_path}")

def generate_sample_html(output_path: Path):
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Digital Personal Data Protection Act Circular 2026</title>
</head>
<body>
  <article>
    <h1>Ministry of Electronics and IT Circular: DPDP Guidelines 2026</h1>
    <p><strong>Circular Reference:</strong> MeitY/DPDP/2026/04</p>
    <section>
      <h2>Section 1: Data Localization and Cross-Border Transfers</h2>
      <p>Data fiduciaries handling personal voice records, health transcripts, and financial records of Indian data principals must ensure all critical personal data is stored within servers physically located in the territory of India.</p>
      <p>Cross-border transfer of non-critical data is permitted only to jurisdictions explicitly notified on the government whitelist.</p>
    </section>
    <section>
      <h2>Section 2: Consent and Multilingual Transparency</h2>
      <p>Notice for consent must be made available in English and all 22 languages specified in the Eighth Schedule of the Indian Constitution, including Hindi, Gujarati, Tamil, and Bengali.</p>
      <p>Withdrawal of consent must be as effortless as granting consent.</p>
    </section>
    <section>
      <h2>Section 3: Data Breach Penalties</h2>
      <p>Failure to implement reasonable security safeguards resulting in a significant personal data breach attracts financial penalties of up to Rs 250 Crore per instance.</p>
    </section>
    <footer>
      <p><em>Notice: This document is a synthetic circular for testing multilingual retrieval and software demonstrations.</em></p>
    </footer>
  </article>
</body>
</html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated sample HTML at {output_path}")

if __name__ == "__main__":
    base_dir = Path("d:/Projects/BolSamajh")
    generate_sample_pdf(base_dir / "samples" / "sample_policy.pdf")
    generate_sample_html(base_dir / "samples" / "sample_circular.html")
