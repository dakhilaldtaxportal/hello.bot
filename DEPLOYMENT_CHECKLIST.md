# Deployment checklist

1. Create Telegram bot with BotFather and copy BOT_TOKEN.
2. Obtain Telegram API ID/API hash from Telegram's official developer portal.
3. Create PostgreSQL on Render.
4. Set all required environment variables.
5. Deploy from GitHub using render.yaml or Dockerfile.
6. Verify `/health`.
7. Configure UptimeRobot to ping the Render `/health` URL.
8. Test rider registration.
9. Test home-zone setting.
10. Test online + live location.
11. Test vendor order posting.
12. Test accept/reject/timeout/release/complete.
13. Test admin pricing and vendor controls.

Credentials and third-party accounts cannot be embedded into a ZIP safely; those are the only unavoidable external setup steps.
