from datetime import datetime, timedelta
from app.models import Appointment

def get_available_slots(date, service_duration):
    """
    Calcula slots livres para uma data específica.
    Regras: 
    1. Horário de funcionamento: 08:00 às 18:00
    2. Intervalo mínimo entre slots: 30 minutos
    """
    # Configuração de expediente (Poderia vir do banco no futuro)
    start_time = datetime.combine(date, datetime.strptime("08:00", "%H:%M").time())
    end_time = datetime.combine(date, datetime.strptime("18:00", "%H:%M").time())
    
    # Busca agendamentos do dia que não foram cancelados
    existing_appointments = Appointment.query.filter(
        Appointment.start_datetime >= start_time,
        Appointment.start_datetime < end_time,
        Appointment.status != 'cancelled'
    ).order_by(Appointment.start_datetime).all()

    available_slots = []
    current_slot = start_time

    while current_slot + timedelta(minutes=service_duration) <= end_time:
        slot_end = current_slot + timedelta(minutes=service_duration)
        
        # Verifica se este slot conflita com algum agendamento existente
        is_free = True
        for appt in existing_appointments:
            # Um slot está ocupado se ele começa antes do fim de um appt 
            # E termina depois do início de um appt
            appt_end = appt.start_datetime + timedelta(minutes=30) # Exemplo fixo ou dinâmico
            if current_slot < appt_end and slot_end > appt.start_datetime:
                is_free = False
                break
        
        if is_free:
            available_slots.append(current_slot)
        
        # Avança 30 minutos para o próximo slot possível
        current_slot += timedelta(minutes=30)
        
    return available_slots