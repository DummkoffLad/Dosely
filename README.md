💊 Dosely

Recordatorios simples para cuidar tu salud.

Dosely es una aplicación móvil hecha en Python con KivyMD, pensada para recordar la toma de medicamentos de forma práctica y confiable.
Nació del deseo de crear una herramienta ligera, sin publicidad ni necesidad de conexión constante, que realmente ayude a mantener hábitos de salud sin complicaciones.

🧩 ¿Qué hace Dosely?

Permite registrar tus medicamentos con nombre, dosis y frecuencia.

Envía recordatorios automáticos a las horas indicadas (por ejemplo, cada 8 horas o cada día).

Guarda un historial de tomas, para que puedas verificar cuándo tomaste tu última dosis.

Todo se almacena localmente en tu teléfono, sin cuentas ni conexión a internet.

Su meta es que nunca más tengas que preguntarte: “¿ya tomé mi medicina?”
<img width="436" height="795" alt="image" src="https://github.com/user-attachments/assets/31a71831-7e94-438e-8a8a-5a6c604905f0" />
<img width="443" height="806" alt="image" src="https://github.com/user-attachments/assets/c4420af7-3c1a-4813-9049-b67c63d2f4ba" />
<img width="452" height="803" alt="image" src="https://github.com/user-attachments/assets/33a19962-439b-4859-9025-62aac5029177" />
<img width="449" height="937" alt="image" src="https://github.com/user-attachments/assets/c0010eb4-e229-41eb-9880-48ea3a1bdadc" />

⚙️ Requisitos técnicos

Python: 3.11

Framework principal: Kivy 2.3.0

Interfaz: KivyMD 1.2.0

Notificaciones y servicios móviles: Plyer

Herramienta de compilación: Buildozer

Sistema operativo destino: Android 7.0 o superior

🧱 Dificultades del desarrollo

El desarrollo de Dosely fue mucho más complicado de lo que parecía al inicio.

El primer obstáculo apareció con las versiones: Python 3.13 resultó incompatible con KivyMD , así que hubo que retroceder a Python 3.11 y rehacer el entorno completo. Cada librería tenía sus propios requisitos, y más de una dejó de funcionar sin razón aparente.

Los menús también dieron guerra. Muchos componentes no se veían bien en Android y fue necesario ajustarlos manualmente, línea por línea, hasta que la interfaz se comportara de forma consistente en distintos dispositivos.

La parte más difícil fue la compilación con Buildozer. Al tratarse de un proyecto hecho totalmente en Python, cualquier pequeño conflicto entre dependencias podía romper el proceso entero. Cython, en particular, generó errores constantes que requirieron reinstalaciones y pruebas sucesivas.

Finalmente, tras muchos intentos, se logró generar el APK funcional. Sin embargo, todavía persiste un problema en ciertos dispositivos relacionado con el JVM y las notificaciones, cuya solución está en desarrollo.

🔮 Planes a futuro

Dosely está en desarrollo activo. Estas son algunas funciones que planeamos incorporar:

Extensa base de datos de medicamentos

Soporte para perfiles múltiples (familiares o pacientes distintos)

Reportes de adherencia (porcentaje de dosis tomadas)

Recordatorios de compra de medicamentos
