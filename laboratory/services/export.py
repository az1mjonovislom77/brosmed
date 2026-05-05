import os
import json
import logging
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from reception.models import Patient, AnalysisResult, Analysis
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@csrf_exempt
def export_analysis_by_phone(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST"}, status=405)

    try:
        body = json.loads(request.body)
        patient_id = body.get("patient_id")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not patient_id:
        return JsonResponse({"error": "patient_id required"}, status=400)

    try:
        patient = Patient.objects.get(id=int(patient_id))
    except Patient.DoesNotExist:
        return JsonResponse({"error": "Patient not found"}, status=404)

    one_month_ago = timezone.now() - timedelta(days=90)

    analyses = (
        Analysis.objects
        .filter(patient=patient, created_at__gte=one_month_ago)
        .select_related("department_types")
        .order_by("-created_at")
    )

    if not analyses.exists():
        return JsonResponse({"error": "No analysis found"}, status=404)

    files_created = []

    for analysis in analyses:
        if not analysis.department_types:
            continue

        results_list = []
        seen = set()

        qs = (
            AnalysisResult.objects
            .filter(patient=patient, result__department_types=analysis.department_types)
            .select_related("result")
            .order_by("-created_at"))

        for ar in qs:

            value = (ar.analysis_result or "").strip()
            if not value:
                continue

            title = (
                ar.result.title
                if ar.result and ar.result.title
                else "Analiz"
            )

            norma = (
                ar.result.norma
                if ar.result and ar.result.norma
                else "-"
            )

            if title in seen:
                continue

            seen.add(title)

            results_list.append({
                "title": title,
                "value": value,
                "norma": norma
            })

        if not results_list:
            continue

        data = {
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "last_name": patient.last_name,
                "middle_name": getattr(patient, "middle_name", ""),
                "birth_date": str(patient.birth_date) if patient.birth_date else "",
                "phone_number": patient.phone_number
            },
            "analysis": {
                "id": analysis.id,
                "title": analysis.department_types.title,
                "created_at": str(analysis.created_at)
            }, "results": results_list}

        try:
            logger.error(f"PDF DATA: {data}")

            response = requests.post("http://pdf_service:8001/pdf/generate/", json=data, timeout=60)
            response.raise_for_status()
            pdf_url = response.json().get("url")
        except Exception:
            logger.exception("PDF SERVICE ERROR")

            return JsonResponse({"error": "PDF generation failed"}, status=500)

        files_created.append({
            "filename": os.path.basename(pdf_url),
            "url": pdf_url
        })

    return JsonResponse({"files": files_created})
