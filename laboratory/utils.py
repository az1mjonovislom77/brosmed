import os
import re
import json
from django.http import JsonResponse
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn
from django.views.decorators.csrf import csrf_exempt
from bot import normalize_phone
from department.models import Department
from reception.models import Patient, AnalysisResult, Analysis
from user.models import User
from django.conf import settings
from django.utils import timezone
import logging


def create_analysis_docx(patient, analysis, results_list, output_path, header_image_path=None,
                         analysis_title="Analiz", doctor_name=""):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    style.font.size = Pt(11)
    if header_image_path and os.path.exists(header_image_path):
        table = doc.add_table(rows=1, cols=2)
        table.autofit = False
        table.columns[0].width = Inches(1.5)
        table.columns[1].width = Inches(4)

        cell_img = table.cell(0, 0)
        p_img = cell_img.paragraphs[0]
        run_img = p_img.add_run()
        run_img.add_picture(header_image_path, width=Inches(3))
        p_img.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

        # O'ng ustunga matn
        cell_text = table.cell(0, 1)
        p_text = cell_text.paragraphs[0]
        text = ("MANZIL: QARSHI SHAHAR KAT - MFY, NASAF KO' CHASI, 31-UY TEL: (75) 223-47-47\n"
                "MoBIL: (97) 070-47-47 ; (97) 310-21-01")
        run_text = p_text.add_run(text)
        run_text.font.size = Pt(12)
        p_text.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

        doc.add_paragraph()  # biroz space qo'shamiz

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

    # Results table
    n_rows = max(1, len(results_list)) + 1
    table = doc.add_table(rows=n_rows, cols=3)
    table.style = 'Table Grid'
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

    footer_image_path = os.path.join(settings.MEDIA_ROOT, "images", "pechat.jpg")
    if os.path.exists(footer_image_path):
        p = doc.add_paragraph()
        r = p.add_run()
        r.add_picture(footer_image_path, width=Inches(3))
        p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    # Word faylini saqlash
    doc.save(output_path)


logger = logging.getLogger(__name__)


def get_patient_by_phone(raw_phone):
    """
    Telefon raqam bo'yicha bemorni topish.
    normalize_phone bilan moslashtirilgan.
    """
    phone = normalize_phone(raw_phone)
    if not phone:
        return None, "Invalid phone after normalization"

    # Avval to'g'ridan-to'g'ri filter
    patient = Patient.objects.filter(phone_number=phone).first()
    if patient:
        return patient, None

    # Agar topilmasa, barcha bazadagi raqamlarni tekshirish
    for p in Patient.objects.exclude(phone_number__isnull=True).exclude(phone_number__exact=''):
        normalized = normalize_phone(p.phone_number)
        if normalized == phone:
            return p, None

    return None, "Patient not found"


@csrf_exempt
def export_analysis_by_phone(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST"}, status=405)

    try:
        body = json.loads(request.body)
        raw_phone = body.get("phone", "").strip()
        department_type_id = body.get("department_type_id")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    patient, err = get_patient_by_phone(raw_phone)
    if err:
        logger.info(f"Phone search failed: {raw_phone}, reason: {err}")
        return JsonResponse({"error": err}, status=404)

    analyses_qs = Analysis.objects.filter(patient=patient)
    if department_type_id and str(department_type_id).isdigit():
        analyses_qs = analyses_qs.filter(department_types_id=int(department_type_id))

    analyses_qs = analyses_qs.order_by('-created_at')
    if not analyses_qs.exists():
        return JsonResponse({"error": "No analysis found"}, status=404)

    export_dir = os.path.join(settings.MEDIA_ROOT, "temp_exports")
    os.makedirs(export_dir, exist_ok=True)

    header_image_path = os.path.join(settings.MEDIA_ROOT, "images", "logo.jpg")
    if not os.path.exists(header_image_path):
        header_image_path = None

    files_created = []

    for analysis in analyses_qs:
        dept_name = "Umumiy"
        if analysis.department_types and analysis.department_types.title:
            dept_name = analysis.department_types.title.strip()

        created_at = analysis.created_at
        date_str = created_at.strftime("%d.%m.%Y")
        time_str = created_at.strftime("%H-%M")

        safe_dept = re.sub(r'[<>:"/\\|?*]', '_', dept_name)[:40]
        filename = f"{safe_dept}_{date_str}_{time_str}.docx"
        filepath = os.path.join(export_dir, filename)

        results_list = []
        seen_titles = set()
        time_window = timezone.timedelta(hours=2)
        start_time = created_at - time_window
        end_time = created_at + time_window

        candidate_results = AnalysisResult.objects.filter(
            patient=patient,
            created_at__gte=start_time,
            created_at__lte=end_time
        ).select_related('result').order_by('created_at')

        for ar in candidate_results:
            if not ar.result or not ar.result.title:
                continue
            title = ar.result.title.strip()
            if title in seen_titles:
                continue
            seen_titles.add(title)
            results_list.append({
                'title': title,
                'value': ar.analysis_result or '-',
                'norma': ar.result.norma or '-'
            })

        if not results_list:
            results_list = [{'title': 'Natija hali kiritilmagan', 'value': '', 'norma': ''}]

        doctor_name = "Laborant"
        if analysis.department_types:
            departments = Department.objects.filter(department_types=analysis.department_types)
            if departments.exists():
                dept = departments.first()
                staff = User.objects.filter(
                    department=dept,
                    role__in=['l', 'd'],
                    is_active=True,
                    full_name__isnull=False,
                    full_name__gt=''
                ).first()
                if staff:
                    doctor_name = staff.full_name.strip()
                else:
                    doctor_name = f"{dept.title}" if dept.title else "Laborant"

        create_analysis_docx(
            patient=patient,
            analysis=analysis,
            results_list=results_list,
            output_path=filepath,
            header_image_path=header_image_path,
            analysis_title=f"{dept_name} natijasi",
            doctor_name=doctor_name
        )

        file_url = request.build_absolute_uri(f"{settings.MEDIA_URL}temp_exports/{filename}")
        files_created.append({
            "filename": filename,
            "url": file_url
        })

    return JsonResponse({"files": files_created})
