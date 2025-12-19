from datetime import datetime, timedelta
from app.models import Appointment

def get_available_slots(date, service_duration):
    # Horário de funcionamento: 08:00 às 18:00
    start_time = datetime.combine(date, datetime.strptime("08:00", "%H:%M").time())
    end_time = datetime.combine(date, datetime.strptime("18:00", "%H:%M").time())
    
    # Busca agendamentos (O índice que criamos acima torna esta linha super rápida)
    existing_appointments = Appointment.query.filter(
        Appointment.start_datetime >= start_time,
        Appointment.start_datetime < end_time,
        Appointment.status != 'cancelled'
    ).all()

    available_slots = []
    current_slot = start_time
    now = datetime.now() # Captura o momento exato do acesso

    while current_slot + timedelta(minutes=service_duration) <= end_time:
        slot_end = current_slot + timedelta(minutes=service_duration)
        
        # REGRA SÊNIOR 1: Bloquear horários que já passaram hoje
        if current_slot < now:
            is_free = False
        else:
            is_free = True
            # REGRA SÊNIOR 2: Verificar conflito com agendamentos existentes
            for appt in existing_appointments:
                appt_end = appt.start_datetime + timedelta(minutes=service_duration)
                if current_slot < appt_end and slot_end > appt.start_datetime:
                    is_free = False
                    break
        
        if is_free:
            available_slots.append(current_slot)
        
        current_slot += timedelta(minutes=30)
        
    return available_slots