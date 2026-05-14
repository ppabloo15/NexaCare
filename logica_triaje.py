"""
NexaCare — Lógica de triaje médico
Calcula niveles de urgencia y devuelve las preguntas por síntoma.
"""

UMBRAL_ROJO    = 70
UMBRAL_NARANJA = 45
UMBRAL_AMARILLO = 25


def calcular_nivel_triaje(puntuacion: int, puntuacion_maxima: int) -> dict:
    """Devuelve el nivel de triaje (ROJO/NARANJA/AMARILLO/VERDE) según el % de puntuación."""
    porcentaje = (puntuacion / puntuacion_maxima) * 100 if puntuacion_maxima > 0 else 0
    if porcentaje >= UMBRAL_ROJO:
        return {
            "nivel": "ROJO – EMERGENCIA",
            "color": "red",
            "emoji": "🔴",
            "recomendacion": "LLAMA AL 112 INMEDIATAMENTE. Tus síntomas indican una posible emergencia vital. No conduzcas. Espera a los servicios de emergencia.",
            "que_hacer": [
                "📞 Llama al 112 ahora mismo",
                "🛋️ Túmbate y no hagas esfuerzos físicos",
                "🚪 Abre la puerta para que entren los servicios de emergencia",
                "👤 Avisa a alguien que esté contigo si es posible",
            ],
        }
    elif porcentaje >= UMBRAL_NARANJA:
        return {
            "nivel": "NARANJA – URGENTE",
            "color": "orange",
            "emoji": "🟠",
            "recomendacion": "Dirígete a urgencias hospitalarias ahora. No esperes más de 1-2 horas. Si empeoras antes de llegar, llama al 112.",
            "que_hacer": [
                "🏥 Ve a urgencias del hospital más cercano",
                "🚗 Pide a alguien que te lleve, no conduzcas solo",
                "📋 Lleva tu tarjeta sanitaria",
                "📞 Si empeoras de camino, llama al 112",
            ],
        }
    elif porcentaje >= UMBRAL_AMARILLO:
        return {
            "nivel": "AMARILLO – MODERADO",
            "color": "gold",
            "emoji": "🟡",
            "recomendacion": "Acude a tu centro de salud hoy. No es una emergencia inmediata pero necesitas atención médica en las próximas horas.",
            "que_hacer": [
                "🏥 Ve a tu centro de salud hoy",
                "💊 Toma medicación básica si la tienes (paracetamol)",
                "💧 Hidrátate bien y descansa",
                "📞 Si empeoras antes de la cita, llama al 112",
            ],
        }
    else:
        return {
            "nivel": "VERDE – LEVE",
            "color": "green",
            "emoji": "🟢",
            "recomendacion": "Puedes quedarte en casa. Reposa, hidrátate y toma medicación básica si la necesitas. Consulta con tu médico si no mejoras en 48 horas.",
            "que_hacer": [
                "🛋️ Reposa en casa",
                "💧 Bebe agua y líquidos frecuentemente",
                "💊 Paracetamol o ibuprofeno si tienes dolor o fiebre",
                "📅 Pide cita con tu médico si no mejoras en 48h",
            ],
        }


SINTOMAS = [
    ("Fiebre", "🌡️"),
    ("Dolor en el pecho", "💔"),
    ("Dolor de cabeza", "🧠"),
    ("Dificultad para respirar", "🌬️"),
    ("Malestar general", "😔"),
    ("Traumatismos y golpes", "🦴"),
    ("Dolor abdominal", "🤢"),
    ("Problemas urinarios", "💧"),
    ("Problemas en la piel", "🩹"),
    ("Síntomas neurológicos", "⚡"),
]

_PREGUNTAS: dict[str, list[tuple[str, int]]] = {
    "Fiebre": [
        ("¿Tienes temperatura superior a 39°C?", 3),
        ("¿Llevas más de 3 días con fiebre sin mejoría?", 3),
        ("¿Tienes dificultad para respirar junto con la fiebre?", 5),
        ("¿Tienes confusión mental o desorientación?", 5),
        ("¿Tienes erupciones o manchas en la piel junto a la fiebre?", 4),
        ("¿Has viajado al extranjero en los últimos 15 días?", 2),
        ("¿Tienes escalofríos intensos o temblores incontrolables?", 3),
    ],
    "Dolor en el pecho": [
        ("¿El dolor es opresivo, como un peso sobre el pecho?", 4),
        ("¿Se irradia hacia el brazo izquierdo o la mandíbula?", 5),
        ("¿Tienes sudoración fría o sensación de mareo?", 4),
        ("¿Te cuesta respirar al mismo tiempo que tienes el dolor?", 4),
        ("¿El dolor empezó de forma repentina hace menos de 1 hora?", 3),
        ("¿Tienes antecedentes de problemas cardíacos o infartos?", 3),
        ("¿El dolor empeora al hacer un pequeño esfuerzo o moverte?", 2),
    ],
    "Dolor de cabeza": [
        ("¿Es el dolor más intenso que has tenido en toda tu vida?", 5),
        ("¿Tienes rigidez o dolor al intentar mover el cuello?", 4),
        ("¿La luz te molesta de forma extrema o te produce náuseas?", 3),
        ("¿Tienes fiebre junto con el dolor de cabeza?", 3),
        ("¿El dolor empezó de golpe como un 'estallido' repentino?", 5),
        ("¿Tienes dificultad para hablar, ver o mover alguna extremidad?", 5),
        ("¿Estás tomando anticoagulantes como Sintrom o similares?", 2),
    ],
    "Dificultad para respirar": [
        ("¿Te cuesta respirar incluso estando en reposo?", 5),
        ("¿Tus labios, dedos o uñas tienen color azulado o morado?", 6),
        ("¿Empezó de forma repentina sin causa aparente?", 4),
        ("¿Sientes presión o dolor en el pecho al respirar?", 4),
        ("¿Produces un silbido o pitido al respirar?", 3),
        ("¿Has tenido una reacción alérgica grave recientemente?", 4),
        ("¿Tienes fiebre alta junto con la dificultad para respirar?", 3),
    ],
    "Malestar general": [
        ("¿Llevas más de 48 horas con síntomas sin mejoría?", 2),
        ("¿Tienes vómitos o diarrea intensa además del malestar?", 2),
        ("¿Has perdido el conocimiento o casi lo has perdido?", 6),
        ("¿Tienes dolor intenso en alguna zona concreta del cuerpo?", 3),
        ("¿Eres mayor de 65 años o tienes alguna enfermedad crónica?", 2),
        ("¿No puedes levantarte de la cama ni realizar actividades básicas?", 3),
        ("¿Tienes sensación de que algo muy grave te está pasando?", 2),
    ],
    "Traumatismos y golpes": [
        ("¿El golpe ha sido en la cabeza o en el cuello?", 4),
        ("¿Has perdido el conocimiento aunque sea brevemente?", 6),
        ("¿Tienes deformidad visible o hueso que sobresale en la zona?", 5),
        ("¿Hay una hemorragia que no puedes detener con presión?", 5),
        ("¿Sientes hormigueo, entumecimiento o no puedes mover alguna extremidad?", 4),
        ("¿El dolor es tan intenso que no puedes apoyar o mover la zona?", 3),
        ("¿El golpe ha sido por un accidente de tráfico o caída de altura?", 4),
    ],
    "Dolor abdominal": [
        ("¿El dolor es muy intenso y no cede con ninguna postura?", 4),
        ("¿El dolor empezó alrededor del ombligo y se ha movido al lado derecho?", 4),
        ("¿Tienes el abdomen muy duro o rígido al tocarlo?", 5),
        ("¿Tienes vómitos de sangre o heces de color negro?", 6),
        ("¿Estás embarazada o podría estarlo?", 4),
        ("¿Tienes fiebre alta junto con el dolor abdominal?", 3),
        ("¿El dolor lleva más de 6 horas sin mejorar?", 3),
    ],
    "Problemas urinarios": [
        ("¿Tienes fiebre alta junto con el dolor al orinar?", 4),
        ("¿Hay sangre visible en la orina?", 4),
        ("¿Tienes dolor intenso en la zona lumbar o flancos?", 3),
        ("¿No puedes orinar nada a pesar de tener muchas ganas?", 5),
        ("¿El dolor es como un cólico intenso que va y viene?", 3),
        ("¿Tienes náuseas o vómitos junto a los síntomas urinarios?", 2),
        ("¿Los síntomas llevan más de 3 días sin mejorar?", 2),
    ],
    "Problemas en la piel": [
        ("¿La erupción se extiende rápidamente por el cuerpo?", 4),
        ("¿Tienes fiebre alta junto con los problemas en la piel?", 3),
        ("¿Las manchas no desaparecen al presionar con un vaso transparente?", 6),
        ("¿Tienes hinchazón en cara, labios o garganta junto a la erupción?", 6),
        ("¿La zona afectada está muy caliente, hinchada y con pus?", 3),
        ("¿Tienes picor intenso generalizado por todo el cuerpo?", 2),
        ("¿Has tomado algún medicamento nuevo en los últimos días?", 2),
    ],
    "Síntomas neurológicos": [
        ("¿Tienes debilidad o parálisis repentina en un lado del cuerpo?", 6),
        ("¿Tienes dificultad repentina para hablar o entender lo que te dicen?", 6),
        ("¿Tu visión ha cambiado de repente (visión doble, pérdida de visión)?", 5),
        ("¿Has tenido una convulsión o movimientos incontrolados del cuerpo?", 6),
        ("¿Tienes un temblor constante que no puedes controlar?", 3),
        ("¿Tienes mareos intensos con sensación de que todo gira (vértigo)?", 3),
        ("¿Has notado pérdida de memoria repentina o confusión mental?", 4),
    ],
}


def obtener_preguntas(sintoma: str) -> list[tuple[str, int]]:
    """Devuelve la lista de (pregunta, puntos) para el síntoma dado, o [] si no existe."""
    return _PREGUNTAS.get(sintoma, [])


def puntuacion_maxima(sintoma: str) -> int:
    """Suma total de puntos posibles para el síntoma dado."""
    return sum(p for _, p in obtener_preguntas(sintoma))
