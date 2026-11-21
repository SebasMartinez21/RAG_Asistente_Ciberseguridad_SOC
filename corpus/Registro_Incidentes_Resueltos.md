# Registro Histórico de Incidentes Resueltos (SOC NovaCloud)

**Propósito:** Base de conocimiento de incidentes atendidos para referencia de analistas en triaje y diagnóstico.

---

## INC-2026-014 — Campaña de Phishing dirigida al área de Finanzas
* **Fecha:** 2026-08-12  
* **Severidad:** P2 (Alto)  
* **Playbook aplicado:** PB-01  
* **Resumen:** Dos analistas financieros reportaron un correo con asunto "Factura vencida #8841". Uno de los usuarios hizo clic en el enlace e ingresó su contraseña, pero rechazó la notificación MFA.  
* **Acciones ejecutadas:** Se revocaron las sesiones activas en el IdP en 18 minutos, se forzó el cambio de contraseña y se bloqueó el dominio `facturas-novacloud[.]com` en el gateway de correo. Se purgaron 11 correos similares de otros buzones.  
* **Lección aprendida:** El rechazo del MFA evitó el acceso no autorizado, demostrando la efectividad de la política de MFA obligatorio sin SMS.

---

## INC-2026-019 — Ataque de fuerza bruta contra bastión SSH
* **Fecha:** 2026-09-03  
* **Severidad:** P3 (Medio)  
* **Playbook aplicado:** PB-03  
* **Resumen:** El SIEM generó una alerta por 142 intentos de autenticación SSH fallidos en 3 minutos desde la IP `185.220.101.45` dirigidos al puerto `2222` del bastión externo.  
* **Acciones ejecutadas:** Se verificó que no hubo ningún inicio de sesión exitoso. Se aplicó bloqueo en el firewall perimetral por 24 horas. Se confirmó que el servidor mantenía `PasswordAuthentication no` y `PermitRootLogin no` conforme a la guía de hardening vigente.  
* **Lección aprendida:** La configuración estricta de llaves Ed25519 impidió cualquier riesgo real de intrusión por diccionario.

---

## INC-2026-023 — Comportamiento anómalo de cifrado masivo en estación de desarrollo
* **Fecha:** 2026-09-28  
* **Severidad:** P1 (Crítico)  
* **Playbook aplicado:** PB-02  
* **Resumen:** El EDR detectó la creación rápida de más de 1.200 archivos con extensión `.enc` en una estación de trabajo del equipo de ingeniería.  
* **Acciones ejecutadas:** El analista de guardia aisló el equipo de la red vía EDR en 12 minutos sin apagarlo, preservando la memoria RAM. Se deshabilitó temporalmente la cuenta del desarrollador y se notificó al CISO. Tras el análisis forense de memoria, se determinó que se trataba de un script de pruebas de cifrado ejecutado por error fuera del entorno sandbox.  
* **Lección aprendida:** Aunque fue un falso positivo malicioso (error humano), mantener el aislamiento sin apagar el equipo permitió confirmar la causa raíz en menos de 1 hora.

---

## INC-2026-027 — Exposición temporal de puerto PostgreSQL en ambiente staging
* **Fecha:** 2026-10-15  
* **Severidad:** P2 (Alto)  
* **Resumen:** Un escaneo semanal detectó el puerto `5432` (PostgreSQL) accesible desde `0.0.0.0/0` en una instancia de pruebas tras un cambio de reglas en el grupo de seguridad.  
* **Acciones ejecutadas:** Se restringió el puerto `5432` exclusivamente a la subred de aplicaciones en 45 minutos. Se revisaron los logs de conexión y se confirmó que no hubo accesos externos ni datos `Restringido` en esa base de datos.  
* **Lección aprendida:** Se agregó una validación automática en el pipeline de infraestructura para impedir reglas `0.0.0.0/0` en puertos de bases de datos.
