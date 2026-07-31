from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse, Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.decorators import diagnostician_required, patient_required
from .models import MedicalReport, validate_pdf_extension, validate_max_file_size
from diagnostics.models import Booking
from notifications.models import Notification

@login_required
def report_list_view(request):
    if request.user.is_patient():
        reports = MedicalReport.objects.filter(patient=request.user)
    elif request.user.is_diagnostician():
        lab_profile = getattr(request.user, 'diagnostician_profile', None)
        reports = MedicalReport.objects.filter(diagnostician=lab_profile)
    else:
        reports = MedicalReport.objects.all()[:20]

    return render(request, 'reports/list.html', {
        'reports': reports
    })


@diagnostician_required
def upload_report_view(request, booking_id):
    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    booking = get_object_or_404(Booking, id=booking_id, diagnostician=lab_profile)

    if request.method == 'POST':
        title = request.POST.get('report_title', '').strip()
        report_type = request.POST.get('report_type', 'BLOOD').strip()
        notes = request.POST.get('summary_notes', '').strip()
        pdf_file = request.FILES.get('pdf_file')

        if not pdf_file:
            messages.error(request, "PDF File is required.")
        else:
            try:
                # Backend File Validation
                validate_pdf_extension(pdf_file)
                validate_max_file_size(pdf_file)

                report = MedicalReport.objects.create(
                    booking=booking,
                    patient=booking.patient,
                    diagnostician=lab_profile,
                    report_title=title or f"Report for Booking #{booking.booking_number}",
                    report_type=report_type,
                    pdf_file=pdf_file,
                    summary_notes=notes
                )

                # Update booking status to REPORT_UPLOADED
                booking.status = Booking.Status.REPORT_UPLOADED
                booking.save()

                # Notify Patient
                Notification.objects.create(
                    user=booking.patient,
                    title="Electronic Medical Report Ready!",
                    message=f"Your report '{report.report_title}' has been uploaded by {lab_profile.lab_name}.",
                    link=f"/reports/list/"
                )

                messages.success(request, f"Medical report uploaded successfully for Patient {booking.patient.username}.")
                return redirect('diagnostics:booking_list')

            except Exception as e:
                messages.error(request, f"File validation error: {str(e)}")

    return render(request, 'reports/upload.html', {
        'booking': booking
    })


@login_required
def view_report_view(request, report_id):
    report = get_object_or_404(MedicalReport, id=report_id)

    # Security check: owner patient, uploading lab, or admin only
    if report.patient != request.user and (not hasattr(request.user, 'diagnostician_profile') or report.diagnostician != request.user.diagnostician_profile) and not request.user.is_admin_role():
        messages.error(request, "Access Denied. You are not authorized to view this report.")
        return redirect('landing')

    return render(request, 'reports/view_report.html', {
        'report': report
    })


@login_required
def download_report_pdf_view(request, report_id):
    report = get_object_or_404(MedicalReport, id=report_id)

    # Security Check: Owner or authorized staff only
    if report.patient != request.user and (not hasattr(request.user, 'diagnostician_profile') or report.diagnostician != request.user.diagnostician_profile) and not request.user.is_admin_role():
        messages.error(request, "Access Denied. Unauthorized report download request.")
        return redirect('landing')

    if not report.pdf_file or not hasattr(report.pdf_file, 'path'):
        # Dynamic fallback response if file on disk was cleared/simulated
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="MediHome_Report_{report.id}.pdf"'
        response.write(f"%PDF-1.4 MediHome Medical Report #{report.id}\nPatient: {report.patient.username}\nTitle: {report.report_title}".encode('utf-8'))
        return response

    try:
        return FileResponse(open(report.pdf_file.path, 'rb'), content_type='application/pdf', as_attachment=True, filename=f"MediHome_Report_{report.id}.pdf")
    except Exception:
        raise Http404("Report file not found on disk.")


@patient_required
def request_hard_copy_view(request, report_id):
    report = get_object_or_404(MedicalReport, id=report_id, patient=request.user)
    report.is_hard_copy_requested = True
    report.save()

    if report.diagnostician:
        Notification.objects.create(
            user=report.diagnostician.user,
            title="Hard Copy Report Delivery Requested",
            message=f"Patient {request.user.username} requested a printed hard copy for report '{report.report_title}'.",
            link="/reports/list/"
        )

    messages.success(request, f"Hard copy request submitted for report '{report.report_title}'. Lab will dispatch physical copy.")
    return redirect('reports:list')
