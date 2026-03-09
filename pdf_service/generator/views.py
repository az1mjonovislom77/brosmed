import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .pdf_utils import create_analysis_docx, convert_docx_to_pdf


@csrf_exempt
def generate_pdf(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    patient = body.get("patient") or {}
    analysis = body.get("analysis") or {}
    results = body.get("results") or []

    export_dir = os.path.join(settings.MEDIA_ROOT, "temp_exports")
    os.makedirs(export_dir, exist_ok=True)

    name = patient.get("name") or ""
    last = patient.get("last_name") or ""
    middle = patient.get("middle_name") or ""
    pid = patient.get("id") or ""

    parts = [name, last, middle, str(pid)]
    filename = "_".join([p for p in parts if p]).replace(" ", "_")

    docx_filename = filename + ".docx"
    docx_path = os.path.join(export_dir, docx_filename)

    create_analysis_docx(
        patient=patient,
        analysis=analysis,
        results_list=results,
        output_path=docx_path,
        header_image_path=None,
        analysis_title=analysis.get("title", "Analiz")
    )

    pdf_path = convert_docx_to_pdf(docx_path)

    if os.path.exists(docx_path):
        os.remove(docx_path)

    pdf_url = request.build_absolute_uri(
        f"{settings.MEDIA_URL}temp_exports/{os.path.basename(pdf_path)}"
    )

    return JsonResponse({"url": pdf_url})