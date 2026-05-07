import os
from django.conf import settings
from django.http import FileResponse
from pdf_service.generator.pdf_utils import convert_docx_to_pdf, create_analysis_docx


def generate_analysis_pdf(patient, analysis, results_qs):
    results_list = []
    for ar in results_qs:
        title = ar.result.title if ar.result else f"[Noma'lum {ar.id}]"
        norma = ar.result.norma if ar.result else ''
        value = ar.analysis_result or ''
        results_list.append({'title': title, 'value': value, 'norma': norma})

    if not results_list:
        results_list = [{'title': '', 'value': '', 'norma': ''}]

    analysis_title = (
        analysis.department_types.title.strip()
        if analysis.department_types and analysis.department_types.title
        else "Analiz"
    )

    base_name = patient.name or "analysis"
    docx_name = f"{base_name}.docx"
    pdf_name = f"{base_name}.pdf"

    export_dir = getattr(settings, 'MEDIA_ROOT', '/tmp')
    docx_path = os.path.join(export_dir, docx_name)

    header_image_path = os.path.join(settings.BASE_DIR, "laboratory", "loggo.jpg")
    seal_image_path = os.path.join(settings.BASE_DIR, "laboratory", "pechat.jpg")

    create_analysis_docx(
        patient=patient,
        analysis=analysis,
        results_list=results_list,
        output_path=docx_path,
        header_image_path=header_image_path,
        analysis_title=analysis_title,
        seal_image_path=seal_image_path
    )

    pdf_path = convert_docx_to_pdf(docx_path)

    if os.path.exists(docx_path):
        os.remove(docx_path)

    return FileResponse(
        open(pdf_path, 'rb'),
        as_attachment=True,
        filename=pdf_name,
        content_type='application/pdf'
    )
