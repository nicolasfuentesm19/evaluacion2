# Arquitectura AWS - Evaluación 2

## Justificación del Diseño: Almacenamiento en S3
Para la implementación del almacenamiento en la nube, se ha optado por la **Alternativa B**: Un bucket S3 centralizado con carpetas por usuario (`evaluacion2-archivos-app/user_{id}/`).

### Razones técnicas:
1. **Escalabilidad y Límites de AWS:** AWS impone un límite blando de 100 buckets por cuenta (ampliable a 1000). Crear un bucket independiente por cada usuario (Alternativa A) no es escalable para plataformas con miles o millones de usuarios.
2. **Gestión Unificada:** Mantener un único bucket permite aplicar políticas globales de ciclo de vida, cifrado, versiones y respaldos de forma mucho más sencilla.
3. **Control de Accesos (IAM):** El aislamiento de la información se logra a través de la aplicación (en el backend) o mediante políticas de IAM basadas en recursos (Resource-based policies) o prefijos condicionales, garantizando la seguridad sin comprometer la escalabilidad.
4. **Cálculo de Espacio:** El backend consulta los metadatos en la base de datos (tabla `UserFile`) para mantener el límite exacto de 2 GB por usuario, optimizando el rendimiento y evitando tener que iterar costosas operaciones en S3 de forma constante.

## Arquitectura de Microservicios Desplegada
La solución comprende múltiples servicios conectados de forma eficiente, siguiendo la rúbrica oficial de arquitectura:

1. **Frontend (Amazon S3):** La aplicación construida en Angular se aloja en un bucket de S3 configurado como "Static Website Hosting", lo que garantiza alta disponibilidad y bajo costo.
2. **API Backend (Amazon ECS Fargate):** Maneja la autenticación, compras y validaciones. Interactúa con S3 mediante `boto3` para el almacenamiento y con RDS para los datos relacionales. Desplegado en clústeres sin servidor.
3. **Servicio de Pagos (Amazon ECS Fargate):** Expone un webhook para recibir confirmaciones de transacciones desde MercadoPago.
4. **Servicio de Notificaciones (Amazon EC2):** Actúa como el motor de comunicación del sistema. Se despliega mediante contenedores Docker directamente en una instancia EC2, como lo especifica la arquitectura.
   - **AWS SES:** Envío de correos electrónicos (Validación de cuentas y recibos de compra/pago).
   - **Twilio WhatsApp API:** Envío de notificaciones vía WhatsApp cuando se suben archivos a la plataforma (se optó por Twilio debido a las estrictas limitaciones del Sandbox de AWS SNS para SMS).

## Pipeline CI/CD (GitHub Actions)
El flujo automatizado garantiza que ante cada cambio en la rama `main`:
1. **Frontend:** Se compila (`ng build`) y los archivos estáticos se sincronizan automáticamente con el Bucket S3.
2. **Backend y Pagos:** Se construyen las imágenes Docker, se suben a **Amazon ECR** y se redespliegan en **Amazon ECS (Fargate)**.
3. **Notificaciones:** Se construye la imagen, se sube a **Amazon ECR**, y mediante una conexión SSH segura se descarga la nueva imagen y se reinicia el contenedor directamente en la instancia **EC2**.
