from datetime import datetime, timedelta
from app.models import Appointment, Service

def get_available_slots(date, service_id):
    """
    Retorna slots disponíveis considerando:
    1. Horário de funcionamento (08:00 - 18:00)
    2. Horários que já passaram (se for hoje)
    3. Conflitos de Equipamentos/Salas (RF002)
    """
    service = Service.query.get(service_id)
    if not service:
        return []

    service_duration = service.duration_minutes
    
    # Definição da janela de trabalho
    start_time = datetime.combine(date, datetime.strptime("08:00", "%H:%M").time())
    end_time = datetime.combine(date, datetime.strptime("18:00", "%H:%M").time())
    
    available_slots = []
    current_slot = start_time
    now = datetime.now()

    while current_slot + timedelta(minutes=service_duration) <= end_time:
        slot_end = current_slot + timedelta(minutes=service_duration)
        
        # REGRA 1: Bloquear horários que já passaram hoje
        if current_slot < now:
            is_free = False
        else:
            # REGRA 2: Verificar conflito de Recurso (Sala/Equipamento)
            # Usamos o método estático que criamos no Model Appointment
            has_conflict = Appointment.check_resource_conflict(
                service_id=service.id,
                start_dt=current_slot,
                end_dt=slot_end
            )
            is_free = not has_conflict
        
        if is_free:
            available_slots.append(current_slot)
        
        # Intervalo entre o início de cada slot (ex: de 30 em 30 min)
        current_slot += timedelta(minutes=30)
        
    return available_slots