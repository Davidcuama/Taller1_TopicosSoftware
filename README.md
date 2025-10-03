# Revisión autocrítica de AI‑Need‑Job

## Contexto

La aplicación **AI‑Need‑Job** surge como proyecto del *Proyecto Integrador 1* y fue retomada para el **Taller 01**.  Su objetivo principal es mejorar la búsqueda de empleo generando currículums optimizados para vacantes específicas mediante un modelo de lenguaje, al mismo tiempo que proporciona a los reclutadores herramientas para publicar y gestionar ofertas laborales.  Esta revisión analiza la calidad del proyecto original en términos de usabilidad, compatibilidad, rendimiento y seguridad, señalando tanto los aciertos como los puntos de mejora.  También se destacan oportunidades para aplicar la inversión de dependencias y patrones de diseño.

## Usabilidad

**Aspectos positivos**

  * **Interfaz sencilla:** Las vistas basadas en plantillas (por ejemplo `home.html`, `feed.html` y `JobseekerPage.html`) presentan una navegación clara para los usuarios.  Las opciones de subir CV, visualizar vacantes y aplicar son intuitivas.
  * **Mensajes de retroalimentación:** El uso de `django.contrib.messages` proporciona avisos visuales al usuario (éxito, advertencia, error) que facilitan comprender el resultado de cada acción.

**Aspectos a mejorar**

  * **Flujo de autenticación:** El proyecto original implementa su propio sistema de autenticación (`User.is_authenticated` y manejo manual de sesiones), lo cual limita funcionalidades como restablecimiento de contraseñas y permisos granulados.  Sería recomendable integrar el sistema de autenticación de Django (`django.contrib.auth`) para aprovechar componentes existentes (gestión de sesiones, grupos y permisos) y simplificar formularios de acceso y registro.
  * **Formularios genéricos:** Algunos formularios (por ejemplo, `UploadFileFormOffer` y `UploadVacancyForm`) podrían beneficiarse de ayudas contextuales y validaciones más detalladas, como restringir extensiones de archivos o validar campos obligatorios antes de intentar procesarlos.
  * **Estructura de navegación:** Las URLs usan rutas vacías (`''`) que redirigen a diferentes vistas según el rol.  Se podría mejorar la claridad separando las vistas de reclutadores y candidatos en rutas distintas (`/jobseeker/`, `/recruiter/`), y usando un layout base que refleje el rol del usuario.

## Compatibilidad

**Aspectos positivos**

  * **Framework estándar:** El uso de Django y bibliotecas populares como PyPDF2, ReportLab y python‑docx facilita la portabilidad entre distintos sistemas operativos siempre que exista un intérprete de Python.
  * **API externa parametrizable:** La clave de API de OpenAI se carga desde un archivo `.env`, lo que permite cambiar de entorno sin modificar el código fuente.

**Aspectos a mejorar**

  * **Dependencia de versiones:** El proyecto se generó con Django 5.1.6 y asume ciertas versiones de librerías.  Es necesario fijar versiones en un archivo `requirements.txt` para evitar incompatibilidades en despliegues futuros.
  * **Internacionalización:** Aunque el público objetivo se encuentra en Colombia, los `settings` originales usan `LANGUAGE_CODE = 'en-us'` y `TIME_ZONE = 'UTC'`.  Ajustar estos valores a `es-co` y `America/Bogota` mejora la coherencia con el usuario final.

## Rendimiento

**Aspectos positivos**

  * **Cálculo offline de embeddings:** Al almacenar los embeddings en campos binarios (`BinaryField`), se evita recalcular vectores para la misma entidad, reduciendo latencia en operaciones repetidas.

**Aspectos a mejorar**

  * **Procesamiento secuencial:** Las funciones `uploadCVS` y `apply_vacancy` procesan archivos y calculan similitudes de forma secuencial.  Cuando se cargan múltiples CVs o vacantes, esto puede provocar cuellos de botella.  Se puede paralelizar el cálculo de embeddings o diferirlo a tareas en segundo plano usando `Celery` y Redis.
  * **Eficiencia en consultas:** Algunas vistas consultan varias veces la base de datos dentro de bucles (p. ej., obtener `Applied_resume` por cada vacante).  Se puede mejorar usando `select_related` o prefetching para reducir el número de consultas.

## Seguridad

**Aspectos positivos**

  * **Uso de hash de contraseñas:** El formulario de registro utiliza `make_password` para almacenar contraseñas de forma segura.
  * **Protección CSRF:** Django incluye middleware CSRF por defecto, lo cual protege los formularios de ataques de falsificación de solicitudes.

**Aspectos a mejorar**

  * **Autenticación y autorización:** La implementación manual del estado de autenticación (`User.is_authenticated`) no ofrece protección contra ataques de fuerza bruta ni mecanismos de bloqueo.  Integrar el módulo de autenticación de Django permitiría utilizar tokens de sesión firmados y verificación automática de usuarios.
  * **Gestión de permisos:** Cualquier usuario autenticado puede acceder a rutas que no le corresponden (por ejemplo, un job seeker podría intentar acceder a `/offer/upload_vacancies/`).  La aplicación debería validar el rol de usuario antes de mostrar o procesar información sensible.
  * **Exposición de claves:** El código original tiene una `SECRET_KEY` incrustada en el repositorio.  Para un despliegue real, estas claves deben almacenarse en variables de entorno y nunca versionarse.

## Oportunidades de inversión de dependencias

* **Servicio de embeddings:** En el proyecto original, las vistas instancian directamente un cliente de OpenAI (`OpenAI(api_key=settings.OPENAI_API_KEY)`) y llaman a métodos concretos.  Esto acopla fuertemente la lógica de negocio a una implementación específica.  Aplicando inversión de dependencias se puede definir una interfaz `EmbeddingService` con un método `embed(text)` e inyectar la implementación deseada (OpenAI, servicio local o un stub para pruebas).  Esto se implementó en el módulo `CVapp/services.py` de la versión reestructurada.

* **Extracción de texto:** La función `uploadCV` decide cómo extraer texto según la extensión del archivo.  Usando el patrón *Strategy* se pueden definir estrategias de extracción (`PdfExtractionStrategy`, `TextExtractionStrategy`) que encapsulen la lógica de cada formato, permitiendo agregar nuevos formatos sin modificar la vista.

* **Capas de servicio:** Muchas vistas contienen lógica de negocio (por ejemplo, cálculo de similitud o creación de registros) mezclada con la lógica de presentación.  Mover esta lógica a objetos de servicio facilita las pruebas unitarias y el reuso.

## Conclusiones

El proyecto **AI‑Need‑Job** ofrece una base funcional, pero algunas decisiones arquitectónicas limitan su mantenibilidad y escalabilidad.  En el refactor se adoptaron patrones de diseño y principios SOLID para separar responsabilidades y facilitar pruebas:

* **Patrón Strategy para la extracción de texto** y un **servicio de embeddings** inyectable, ilustrando inversión de dependencias.
* **Vistas basadas en clases (CBV)** para autenticación e historial, siguiendo patrones recomendados en Django.
* **Configuración localizada** (`TIME_ZONE = 'America/Bogota'`, `LANGUAGE_CODE = 'es-co'`).

Estas mejoras sientan las bases para evolucionar la aplicación de forma ordenada, aplicando otros patrones de diseño de Python y Django según sea necesario.

## Nueva funcionalidad: sistema de notificaciones (BONO)

Para el bono del taller se desarrolló **desde cero** un módulo de notificaciones que informa al candidato cuando su currículum es aceptado o rechazado por un reclutador.  Se aplicó el *patrón Observer* para desacoplar la lógica de negocio de la generación de notificaciones:

- **Sujeto (`NotificationSubject`)**: mantiene una lista de observadores y ofrece métodos para registrar, desregistrar y notificar.  Se implementó un sujeto global (`notification_subject`) que puede ser invocado desde cualquier parte de la aplicación.
- **Observadores**: se definió una interfaz `NotificationObserver` y una implementación concreta `NotificationModelObserver` que persiste los mensajes en la base de datos (`Notification` model).  Otros observadores (como envío de correos o notificaciones en tiempo real) podrían agregarse sin modificar el código existente.
- **Eventos**: en las vistas de `offer` se inyecta el sujeto y, tras aceptar o rechazar un CV, se invoca `notification_subject.notify(user, mensaje)` para informar al candidato.  La vista de notificaciones (`notification_list`) lista los mensajes y permite marcarlos como leídos.

### Justificación del patrón

El *Observer* permite **extender** la funcionalidad de notificaciones sin alterar las vistas ni la lógica de negocio.  Siguiendo el principio de **abierto/cerrado**, las vistas simplemente notifican un evento y delegan la acción a los observadores registrados.  Esto evita repetir código cada vez que se necesite enviar un aviso y facilita pruebas aisladas.  Además, se mantiene la coherencia con la inversión de dependencias: las vistas dependen de una abstracción (`NotificationSubject` / `NotificationObserver`) en lugar de una implementación concreta.
