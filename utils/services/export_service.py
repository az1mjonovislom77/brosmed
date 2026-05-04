from openpyxl import Workbook
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import HttpResponse

def export_stats_to_excel(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "Clinic Stats"

    ws.append(["Umumiy Statistikalar"])
    for key, value in data["umumiy"].items():
        ws.append([key, value])

    ws.append([])
    ws.append(["Bo‘limlar Statistikasi"])
    ws.append(["Department", "Bemorlar", "Konsultatsiyalar", "Tahlillar", "To‘lovlar"])

    for dep in data["departments"]:
        ws.append(
            [dep["department"], dep["jami_bemorlar"], dep["konsultatsiyalar"], dep["tahlillar"], dep["tolovlar"]])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    response = HttpResponse(stream,
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="clinic_stats.xlsx"'
    return response

def export_stats_to_pdf(data):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    y = 800
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Klinika statistikasi")
    y -= 30

    start_date = data["umumiy"]["start_date"]
    end_date = data["umumiy"]["end_date"]
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Hisobot davri: {start_date} - {end_date}")
    y -= 30

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "UMUMIY:")
    y -= 20
    pdf.setFont("Helvetica", 12)

    for key, value in data["umumiy"].items():
        if key in ['start_date', 'end_date']:
            continue
        pdf.drawString(60, y, f"{key}: {value}")
        y -= 18

    y -= 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "DEPARTAMENTLAR:")
    y -= 20
    pdf.setFont("Helvetica", 12)

    for dep in data["departments"]:
        pdf.drawString(60, y,
                       f"{dep['department']} → Bemor: {dep['jami_bemorlar']}, Konsultatsiya: {dep['konsultatsiyalar']}, Tahlil: {dep['tahlillar']}, To‘lov: {dep['tolovlar']}")
        y -= 18

    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response["Content-Disposition"] = f'attachment; filename="clinic_stats_{start_date}_{end_date}.pdf"'
    return response
