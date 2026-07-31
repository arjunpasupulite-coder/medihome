import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import TelemedicineConsultation, ChatMessage
from reports.models import validate_pdf_extension, validate_max_file_size
from hospitals.models import Doctor

@login_required
def telemedicine_room_view(request, consultation_id=None):
    if consultation_id:
        consultation = get_object_or_404(TelemedicineConsultation, id=consultation_id)
        if consultation.patient != request.user and consultation.doctor.hospital.user != request.user and not request.user.is_admin_role():
            messages.error(request, "Access Denied to consultation room.")
            return redirect('landing')
    else:
        # Get active consultation or create demo room for test
        consultations = TelemedicineConsultation.objects.filter(patient=request.user) if request.user.is_patient() else TelemedicineConsultation.objects.all()
        if consultations.exists():
            consultation = consultations.first()
        else:
            doc = Doctor.objects.first()
            if not doc:
                messages.warning(request, "No doctors available yet for telemedicine.")
                return redirect('patients:dashboard')
            
            consultation = TelemedicineConsultation.objects.create(
                patient=request.user,
                doctor=doc,
                scheduled_time=request.user.created_at,
                video_room_id=f"ROOM-{uuid.uuid4().hex[:8].upper()}"
            )

    messages_list = ChatMessage.objects.filter(consultation=consultation)

    return render(request, 'telemedicine/room.html', {
        'consultation': consultation,
        'chat_messages': messages_list
    })


@login_required
def send_chat_message_view(request, consultation_id):
    if request.method != 'POST':
        return redirect('telemedicine:room_detail', consultation_id=consultation_id)

    consultation = get_object_or_404(TelemedicineConsultation, id=consultation_id)
    msg_text = request.POST.get('message', '').strip()

    if msg_text:
        ChatMessage.objects.create(
            consultation=consultation,
            sender=request.user,
            message=msg_text
        )

    return redirect('telemedicine:room_detail', consultation_id=consultation.id)


@login_required
def upload_prescription_view(request, consultation_id):
    consultation = get_object_or_404(TelemedicineConsultation, id=consultation_id)
    
    if request.method == 'POST':
        notes = request.POST.get('consultation_notes', '').strip()
        prescription = request.FILES.get('prescription_file')

        consultation.consultation_notes = notes

        if prescription:
            try:
                validate_pdf_extension(prescription)
                validate_max_file_size(prescription)
                consultation.prescription_file = prescription
                messages.success(request, "Prescription PDF uploaded successfully!")
            except Exception as e:
                messages.error(request, f"Prescription upload failed: {str(e)}")

        consultation.save()

    return redirect('telemedicine:room_detail', consultation_id=consultation.id)
