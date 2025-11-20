import os
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn


def create_analysis_docx(patient, analysis, results_list, output_path,
                         header_image_path="/mnt/data/51cfb6cc-75b8-476e-a370-7a187b7af31b.png",
                         analysis_title="Анализ", doctor_name=""):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    style.font.size = Pt(11)
    if header_image_path and os.path.exists(header_image_path):
        try:
            p = doc.add_paragraph()
            r = p.add_run()
            r.add_picture(header_image_path, width=Inches(5.5))  # adjust size as needed
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            doc.add_paragraph()  # space
        except Exception:
            pass

    title = doc.add_paragraph()
    title_run = title.add_run("Brosmed Laboratoriya\n")
    title_run.bold = True
    title_run.font.size = Pt(14)
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    subtitle = doc.add_paragraph()
    subtitle_run = subtitle.add_run(f"{analysis_title}\n")
    subtitle_run.italic = True
    subtitle_run.font.size = Pt(13)
    subtitle.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    doc.add_paragraph()
    doc.add_paragraph()
    info_table = doc.add_table(rows=4, cols=2)
    info_table.style = 'Table Grid'
    info_table.autofit = True
    info_table.cell(0, 0).text = "Bemor I.F.O"
    info_table.cell(0, 1).text = f"{(patient.name or '')} {(patient.last_name or '')} {(patient.middle_name or '')}"
    info_table.cell(1, 0).text = "Tugilgan sanasi"
    info_table.cell(1, 1).text = patient.birth_date.strftime("%Y-%m-%d") if getattr(patient, 'birth_date', None) else ""
    info_table.cell(2, 0).text = "Telefon raqami"
    info_table.cell(2, 1).text = patient.phone_number or ""
    info_table.cell(3, 0).text = "Tekshiruv sanasi"
    info_table.cell(3, 1).text = analysis.created_at.strftime("%Y-%m-%d %H:%M") if getattr(analysis, 'created_at',
                                                                                           None) else ""
    doc.add_paragraph()
    n_rows = max(1, len(results_list)) + 1
    table = doc.add_table(rows=n_rows, cols=3)
    table.style = 'Table Grid'
    table.autofit = False
    table.columns[0].width = Inches(3)
    table.columns[1].width = Inches(1.5)
    table.columns[2].width = Inches(2)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Tahlil nomi"
    hdr_cells[1].text = "Tahlil natijasi"
    hdr_cells[2].text = "Norma"

    for i, row in enumerate(results_list, start=1):
        tcell = table.rows[i].cells
        tcell[0].text = row.get('title', '')
        tcell[1].text = row.get('value', '')
        tcell[2].text = row.get('norma', '')

    doc.add_paragraph()
    podpis = doc.add_paragraph()
    final_doctor_text = f"Laborant: {doctor_name}" if doctor_name else "Laborant: ____________________"
    podpis_run = podpis.add_run(final_doctor_text)
    podpis_run.font.size = Pt(12)
    podpis.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    doc.save(output_path)
