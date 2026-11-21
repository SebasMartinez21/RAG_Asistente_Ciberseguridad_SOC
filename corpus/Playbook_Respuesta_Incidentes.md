# Playbook de Respuesta a Incidentes SOC (PB-01 a PB-03)

**Organización:** NovaCloud Corp — Centro de Operaciones de Seguridad (SOC)  
**Versión:** 2.1  
**Audiencia:** Analistas SOC Nivel 1 y Nivel 2  

---

## 1. Fases Generales del Manejo de Incidentes

Todo incidente de seguridad en NovaCloud Corp debe gestionarse siguiendo el ciclo de cinco fases basado en NIST SP 800-61:

1. **Detección y Triaje:** Confirmar si la alerta es un verdadero positivo, clasificar la severidad (`P1` a `P4`) según la `Matriz_SLA_y_Escalamiento.docx` y abrir el ticket correspondiente.
2. **Contención:** Limitar el alcance del incidente de forma inmediata (aislamiento de red, revocación de sesiones o bloqueo de IPs) sin destruir evidencia volátil.
3. **Erradicación:** Eliminar la causa raíz (cuentas comprometidas, binarios maliciosos, reglas persistentes o vulnerabilidades explotadas).
4. **Recuperación:** Restaurar servicios desde respaldos verificados, monitorear comportamiento anómalo durante 48 horas y validar con el propietario del activo.
5. **Lecciones Aprendidas:** Documentar el post-mortem y actualizar reglas de detección en el SIEM.

---

## 2. Playbook PB-01: Phishing y Robo de Credenciales

**Disparadores:** Reporte de usuario de correo sospechoso, alerta de inicio de sesión desde ubicación imposible o detección en el gateway de correo.

### Pasos obligatorios
1. **Verificar alcance:** Revisar en los logs del proveedor de identidad (IdP) si el usuario ingresó credenciales o aprobó una solicitud MFA sospechosa.
2. **Contención de identidad:** Si hubo interacción con el enlace malicioso, revocar inmediatamente todas las sesiones activas en el IdP, forzar el restablecimiento de contraseña y rotar tokens de acceso o llaves API del usuario.
3. **Análisis de correo:** Inspeccionar cabeceras (`SPF`, `DKIM`, `DMARC`), extraer URLs y adjuntos en entorno aislado (sandbox).
4. **Bloqueo perimetral:** Bloquear el dominio remitente y las URLs maliciosas en el gateway de correo y proxy web; purgar correos idénticos de otros buzones corporativos.
5. **Escalamiento:** Si la cuenta comprometida posee privilegios administrativos o acceso a datos `Restringido`, el incidente debe reclasificarse automáticamente a severidad **P1** y escalarse según la `Matriz_SLA_y_Escalamiento.docx`.

---

## 3. Playbook PB-02: Sospecha de Ransomware

**Disparadores:** Alerta del EDR por cifrado masivo de archivos, detección de eliminación de Shadow Copies o nota de rescate en el sistema de archivos.

### Pasos obligatorios
1. **Aislamiento inmediato sin apagar:** Aislar el host de la red mediante la consola del EDR o desconectando el cable de red. **Nunca apagar el equipo** en esta etapa para preservar la memoria volátil (RAM) y posibles llaves de cifrado en memoria.
2. **Contención de cuentas:** Deshabilitar temporalmente las cuentas de usuario y de servicio con sesión activa en el equipo afectado.
3. **Preservación de evidencia:** Capturar volcado de memoria RAM e imagen forense del disco antes de iniciar la limpieza.
4. **Verificación de respaldos:** Validar que los respaldos inmutables en almacenamiento WORM no hayan sido alcanzados ni alterados.
5. **Notificación:** Todo incidente de ransomware activo se clasifica como **P1 (Crítico)** y exige notificación inmediata al CISO y al Nivel 2.

---

## 4. Playbook PB-03: Ataque de Fuerza Bruta SSH o VPN

**Disparadores:** Múltiples eventos de autenticación fallida en `/var/log/auth.log`, concentrador VPN o alertas correlacionadas en el SIEM.

### Pasos obligatorios
1. **Evaluación de umbral:** Verificar si una misma IP externa supera **20 intentos fallidos en un lapso de 5 minutos** contra servicios SSH o VPN.
2. **Verificación de éxito:** Comprobar en los logs si existió algún inicio de sesión exitoso posterior desde la IP atacante o desde la misma subred.
3. **Bloqueo:** Si no hubo compromiso, bloquear la IP atacante en el firewall perimetral durante **24 horas** y registrar el evento como severidad **P3**.
4. **Escalamiento por compromiso:** Si se detecta un inicio de sesión exitoso tras los intentos fallidos, escalar a **P2** (o **P1** si es cuenta privilegiada), revocar llaves SSH o certificados VPN afectados y revisar persistencia en el servidor.
