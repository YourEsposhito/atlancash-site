# AtlanCash — Sitio Web (Flask)

Este proyecto agrega una web simple conectada a la misma base de datos `atlancash.db` de tu bot.

## Funciones
- Login por usuario de Telegram + ID (los mismos que ya existen en tu tabla `users`).
- Panel de cliente: balance, earnings, total recargado, intereses/depositos/retiros recientes.
- Solicitar recarga / retiro (quedan en `pending`).
- Panel admin: aprobar/rechazar depósitos y retiros; **⚡ Forzar intereses** con la misma lógica del bot (interés sobre `total_recharged` usando `plan_percent`).

> Recomendación: deja que el **bot** siga corriendo el pago automático de intereses a las 00:00. Usa el botón web solo como emergencia/manual para evitar doble pago.

## Requisitos
```
pip install -r requirements.txt
```
Crea o ajusta el archivo `.env` (ya viene un ejemplo) y define credenciales de admin.

## Ejecutar
```
python app.py
```
Abre http://localhost:5000

- Cliente entra con su `username` y `user_id` (según la tabla `users`).
- Admin entra por `/admin-login` con `ADMIN_USERNAME` y `ADMIN_PASSWORD` del `.env`.

## Notas
- La web crea tablas mínimas si no existen (users, deposits, withdrawals) y asegura `interest_logs.base_principal`.
- Si ya usas el bot, la web leerá/escribirá en las mismas tablas.
