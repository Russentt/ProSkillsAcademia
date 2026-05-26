# ProSkills Academia (SGAP) 🚀

**ProSkills Academia** (Sistema de Gestión Académica ProSkills) es una solución de software independiente y autónoma diseñada para digitalizar, centralizar y optimizar la administración de cursos y el seguimiento académico del Centro de Capacitación ProSkills.

El sistema reemplaza los flujos de trabajo manuales basados en planillas Excel por una plataforma web segura, interactiva y accesible según roles de usuario definidos.

---

## 🎯 Propósito del Sistema

> **"Domina las competencias digitales del futuro con ProSkills Academia"**
> _Capacitación profesional, flexible y orientada a resultados, diseñada para potenciar tu desarrollo técnico y acelerar tu crecimiento en el mercado laboral actual._

---

## 🛠️ Stack Tecnológico

El desarrollo de la plataforma se encuentra estrictamente restringido al uso de las siguientes tecnologías web estándar:

- **Backend:** Python con el framework Flask para la lógica de negocio y procesamiento de datos.
- **Frontend:** HTML5, CSS3 (estructurado y estilizado mediante Bootstrap) y JavaScript para comportamientos dinámicos.
- **Persistencia:** Base de datos centralizada para el almacenamiento y gestión segura de la información académica.
- **Protocolos:** Comunicación cliente-servidor mediante protocolos web estándar HTTP/HTTPS, requiriendo obligatoriamente HTTPS para resguardar la confidencialidad de los datos.

---

## ⚙️ Módulos Destacados

### 📂 Inscripciones Digitales

**Gestión ágil de cupos** Regístrate en tus cursos de forma autónoma. El sistema valida la disponibilidad de cupos en tiempo real, garantizando un proceso eficiente y sin errores.

### 📊 Evaluaciones y Notas

**Seguimiento académico** Consulta tu desempeño y progreso de forma transparente. Visualiza calificaciones y avances directamente en la plataforma tras ser registrados por los docentes.

### 📜 Certificación Automática

**Validación de logros** Obtén tu certificado digital de forma inmediata al aprobar los requisitos del curso. Acreditación oficial, estandarizada y lista para descargar.

---

## 👥 Roles de Usuario (Control de Acceso)

La interfaz de usuario se adapta de forma responsiva mediante paneles visuales (_dashboards_) diferenciados según el rol y permisos asignados:

| Rol               | Permisos y Accesos Principales                                                                                                                           |
| :---------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Administrador** | Control global del sistema: gestión de cuentas de usuario, configuración de cursos/programas, control de inscripciones y supervisión general.            |
| **Profesor**      | Acceso exclusivo a los cursos asignados, creación de evaluaciones, registro de calificaciones y monitoreo sistemático del progreso académico.            |
| **Estudiante**    | Visualización de la oferta académica disponible, inscripción autónoma, consulta de calificaciones del semestre y descarga de certificados de aprobación. |

---

## 📊 Criterios de Calidad y Rendimiento (Requisitos No Funcionales)

- **Rendimiento:** Capacidad demostrada para soportar un mínimo de 200 usuarios concurrentes, con tiempos de respuesta en solicitudes menores a 2 segundos en el 95% de los casos.
- **Seguridad:** Cifrado de datos en tránsito con HTTPS y almacenamiento protegido de credenciales de acceso mediante funciones hash SHA-256.
- **Disponibilidad:** Acceso continuo 24/7 con un tiempo de actividad mínimo garantizado del 99.5% del tiempo en horario laboral.
- **Fiabilidad:** Integridad transaccional al 100% para evitar la duplicidad de registros informáticos y generación automatizada de respaldos diarios de la base de datos.
