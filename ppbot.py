import os
import asyncio
import threading
import secrets
import requests
import httpx
from http.server import HTTPServer, SimpleHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, ContextTypes)

# --- CONFIGURAZIONI ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
# Il tuo API KEY di ShrinkMe è gestito tramite variabili d'ambiente su Render
SHRINKME_API = os.environ.get("SHRINKME_API")
user_lang = {}
user_premium = {}
pending_tokens = {} 

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()
   
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- DIZIONARIO LINGUE (Invariato) ---
STRINGS = {
   "it": {"btn_guida": "📖 Guida & Info", "btn_genera": "🚀 Genera Email", "btn_controlla":"🔄 Controlla Posta", "btn_sms": "📱 Numeri SMS", "sms_choice": "📱 Scegli il tipo di numero:", "sms_free_btn": "🆓 Gratis (Pubblici)", "sms_premium_btn":"💎 Premium (Privati)", "sms_loading": "⏳ Recupero numeri in corso...", "sms_error": "❌ Impossibile recuperare i numeri. Riprova.", "sms_select": "📋 Seleziona un numero per vedere i messaggi:", "sms_msgs_header":"📨 Messaggi per {number}:\n", "sms_no_msgs": "📭 Nessun messaggio per questo numero. Riprova tra poco.", "sms_msg_block":"━━━━━━━━━━━━━━━━\n👤 Da: {sender}\n📝 Testo: {body}\n🕐 {time}", "sms_premium_info":"💎 Numeri Premium (Privati)\n\nI numeri premium sono esclusivi per te e garantiscono la ricezione dell'SMS.\n\n🔧 Funzione in arrivo!", "welcome": "🛡️ PrivacyGuard Bot\n*Il tuo scudo per la privacy digitale.*\n\nCrea email e numeri temporanei per navigare senza spam.\n\nScegli un'opzione:", "guida": "ℹ️ GUIDA & INFO\n• Le email rimangono attive poche ore.\n• Per superare il link pubblicitario, attendi il countdown senza cliccare i falsi tasti Download.", "generating": "⏳ Creazione email in corso...", "gen_error_api":"❌ Impossibile contattare il servizio email. Riprova.", "gen_error_acc":"❌ Errore nella creazione dell'email. Riprova.", "gen_ready": "✨ Email Temporanea generata!\n\n🔒 Clicca il pulsante per verificare il tuo indirizzo.", "btn_vedi": "👁 Vedi la tua Email", "unlock_ok": "✅ Verifica completata!\n\n📧 La tua Email Temporanea è:\n{email}\n\nPremi il pulsante per controllare la casella:", "token_invalid":"❌ Token non valido o già utilizzato.", "session_expired":"⚠️ Sessione scaduta. Genera una nuova email.", "auth_error": "❌ Errore nel controllo posta. Riprova.", "no_messages": "📭 Nessun messaggio ricevuto, riprova tra un momento.", "inbox_header": "📬 Casella: {email}\n", "msg_block": "━━━━━━━━━━━━━━━━\n👤 Da: {sender}\n📌 Oggetto: {subject}\n📝 Testo:\n{body}", "adv_message": "📢 Messaggio Sponsorizzato — Attendi 5 secondi per completare l'operazione..."},
   "en": {"btn_guida": "📖 Guide & Info", "btn_genera": "🚀 Generate Email", "btn_controlla":"🔄 Check Inbox", "btn_sms": "📱 SMS Numbers", "sms_choice": "📱 Choose number type:", "sms_free_btn": "🆓 Free (Public)", "sms_premium_btn":"💎 Premium (Private)", "sms_loading": "⏳ Fetching numbers...", "sms_error": "❌ Could not fetch numbers. Please try again.", "sms_select": "📋 Select a number to view its messages:", "sms_msgs_header":"📨 Messages for {number}:\n", "sms_no_msgs": "📭 No messages yet for this number. Try again in a moment.", "sms_msg_block":"━━━━━━━━━━━━━━━━\n👤 From: {sender}\n📝 Text: {body}\n🕐 {time}", "sms_premium_info":"💎 Premium Numbers (Private)\n\nPremium numbers are exclusive to you and guarantee SMS delivery.\n\n🔧 Feature coming soon!", "welcome": "🛡️ PrivacyGuard Bot\n*Your shield for digital privacy.*\n\nCreate disposable emails and numbers to avoid spam.\n\nChoose an option:", "guida": "ℹ️ GUIDE & INFO\n• Emails stay active for a few hours.\n• Wait out the ad countdown without clicking fake download buttons.", "generating": "⏳ Creating your email address...", "gen_error_api":"❌ Could not reach the email service. Please try again.", "gen_error_acc":"❌ Error creating the email. Please try again.", "gen_ready": "✨ Temporary Email generated!\n\n🔒 Click the button below to verify and reveal your address.", "btn_vedi": "👁 View your Email", "unlock_ok": "✅ Verification complete!\n\n📧 Your Temporary Email is:\n{email}\n\nPress the button to check your inbox:", "token_invalid":"❌ Invalid or already used token.", "session_expired":"⚠️ Session expired. Please generate a new email.", "auth_error": "❌ Inbox check error. Please try again.", "no_messages": "📭 No messages received yet, try again in a moment.", "inbox_header": "📬 Inbox: {email}\n", "msg_block": "━━━━━━━━━━━━━━━━\n👤 From: {sender}\n📌 Subject: {subject}\n📝 Body:\n{body}", "adv_message": "📢 Sponsored Message — Please wait 5 seconds to complete the operation..."},
   "es": {"btn_guida": "📖 Guía e Info", "btn_genera": "🚀 Generar Email", "btn_controlla":"🔄 Revisar Bandeja", "btn_sms": "📱 Números SMS", "sms_choice": "📱 Elige el tipo di número:", "sms_free_btn": "🆓 Gratis (Públicos)", "sms_premium_btn":"💎 Premium (Privados)", "sms_loading": "⏳ Obteniendo números...", "sms_error": "❌ No se pudieron obtener los números. Inténtalo de nuevo.", "sms_select": "📋 Selecciona un número para ver sus mensajes:", "sms_msgs_header":"📨 Mensajes para {number}:\n", "sms_no_msgs": "📭 Aún no hay mensajes. Inténtalo de nuevo en un momento.", "sms_msg_block":"━━━━━━━━━━━━━━━━\n👤 De: {sender}\n📝 Texto: {body}\n🕐 {time}", "sms_premium_info":"💎 Números Premium (Privados)\n\nLos números premium son exclusivos para ti.\n\n🔧 ¡Función próximamente disponible!", "welcome": "🛡️ PrivacyGuard Bot\n*Tu escudo de privacidad.*\n\nCrea correos y números temporales para evitar el spam.\n\nElige una opción:", "guida": "ℹ️ INFORMACIÓN\n• Los correos duran unas horas.\n• Espera a que la publicidad termine sin tocar botones falsos.", "generating": "⏳ Creando tu dirección di correo...", "gen_error_api":"❌ No se pudo conectar al servicio. Inténtalo de nuevo.", "gen_error_acc":"❌ Error al crear el email. Inténtalo de nuevo.", "gen_ready": "✨ ¡Email temporal generado!\n\n🔒 Pulsa el botón para verificar y ver tu dirección.", "btn_vedi": "👁 Ver mi Email", "unlock_ok": "✅ ¡Verificación completada!\n\n📧 Tu Email Temporal es:\n{email}\n\nPulsa el botón para revisar tu bandeja:", "token_invalid":"❌ Token inválido o ya utilizado.", "session_expired":"⚠️ Sesión caducada. Crea un nuevo email.", "auth_error": "❌ Error de autenticación. Inténtalo de nuevo.", "no_messages": "📭 No se han recibido mensajes.", "inbox_header": "📬 Bandeja: {email}\n", "msg_block": "━━━━━━━━━━━━━━━━\n👤 De: {sender}\n📌 Asunto: {subject}\n📝 Texto:\n{body}", "adv_message": "📢 Mensaje Patrocinado — Por favor, espera 5 segundos..."},
   "ar": {"btn_guida": "📖 الدليل والمعلومات", "btn_genera": "🚀 إنشاء بريد إلكتروني", "btn_controlla":"🔄 فحص البريد الوارد", "btn_sms": "📱 أرقام SMS", "sms_choice": "📱 اختر نوع الرقم:", "sms_free_btn": "🆓 مجاني (عام)", "sms_premium_btn":"💎 بريميوم (خاص)", "sms_loading": "⏳ جارٍ جلب الأرقام...", "sms_error": "❌ تعذّر جلب الأرقام. حاول مرة أخرى.", "sms_select": "📋 اختر رقمًا لعرض رسائله:", "sms_msgs_header":"📨 الرسائل الواردة على {number}:\n", "sms_no_msgs": "📭 لا توجد رسائل لهذا الرقم بعد.", "sms_msg_block":"━━━━━━━━━━━━━━━━\n👤 من: {sender}\n📝 النص: {body}\n🕐 {time}", "sms_premium_info":"💎 أرقام بريميوم (خاصة)\n\nأرقام البريميوم حصرية لك وتضمن استلام الرسائل.\n\n🔧 الميزة قادمة قريبًا!", "welcome": "🛡️ PrivacyGuard Bot\n*درعك للخصوصية الرقمية.*\n\nأنشئ إيميلات وأرقام مؤقتة للتصفح بدون إزعاج.\n\nاختر خيارًا:", "guida": "ℹ️ معلومات الخدمة\n• الإيميلات تبقى نشطة لبضع ساعات.\n• انتظر العداد حتى ينتهي وتجنب الإعلانات المزيفة.", "generating": "⏳ جارٍ إنشاء عنوان بريدك...", "gen_error_api": "❌ تعذّر الوصول إلى الخدمة. حاول مرة أخرى.", "gen_error_acc": "❌ خطأ في إنشاء البريد. حاول مرة أخرى.", "gen_ready": "✨ تم إنشاء البريد الإلكتروني المؤقت!\n\n🔒 اضغط على الزر أدناه للتحقق وعرض عنوانك.", "btn_vedi": "👁 عرض بريدي الإلكتروني", "unlock_ok": "✅ اكتملت عملية التحقق!\n\n📧 بريدك الإلكتروني المؤقت هو:\n{email}\n\nاضغط على الزر لفحص صندوق الوارد:", "token_invalid":"❌ رمز غير صالح أو مستخدم بالفعل.", "session_expired":"⚠️ انتهت الجلسة. يرجى إنشاء بريد جديد.", "auth_error": "❌ خطأ في فحص البريد. حاول مرة أخرى.", "no_messages": "📭 لم يتم استلام أي رسائل بعد.", "inbox_header": "📬 صندوق الوارد: {email}\n", "msg_block": "━━━━━━━━━━━━━━━━\n👤 من: {sender}\n📌 الموضوع: {subject}\n📝 النص:\n{body}", "adv_message": "📢 رسالة إعلانية — يرجى الانتظار 5 ثوانٍ..."},
   "zh": {"btn_guida": "📖 指南与信息", "btn_genera": "🚀 生成临时邮箱", "btn_controlla":"🔄 检查收件箱", "btn_sms": "📱 短信号码", "sms_choice": "📱 选择号码类型：", "sms_free_btn": "🆓 免费（公共）", "sms_premium_btn":"💎 高级（私人）", "sms_loading": "⏳ 正在获取号码...", "sms_error": "❌ 无法获取号码。请重试。", "sms_select": "📋 选择一个号码查看消息：", "sms_msgs_header":"📨 {number} 的消息：\n", "sms_no_msgs": "📭 该号码暂无消息。请稍后重试。", "sms_msg_block":"━━━━━━━━━━━━━━━━\n👤 来自： {sender}\n📝 内容： {body}\n🕐 {time}", "sms_premium_info":"💎 高级号码（私人）\n\n专属私人号码，保证短信送达。\n\n🔧 功能即将推出！", "welcome": "🛡️ PrivacyGuard Bot\n*您的数字隐私盾牌.*\n\n创建临时邮箱和号码，远离垃圾邮件。\n\n请选择：", "guida": "ℹ️ 服务指南\n• 临时邮箱仅有效几个小时。\n• 请等待广告倒计时结束，不要点击虚假的下载按钮。", "generating": "⏳ 正在生成邮箱地址...", "gen_error_api":"❌ 无法连接到邮箱服务。请重试。", "gen_error_acc":"❌ 创建邮箱失败。请重试。", "gen_ready": "✨ 临时邮箱已生成！\n\n🔒 点击下方按钮验证并查看您的地址。", "btn_vedi": "👁 查看您的邮箱", "unlock_ok": "✅ 验证成功！\n\n📧 您的临时邮箱是：\n{email}\n\n点击按钮检查收件箱：", "token_invalid":"❌ 令牌无效或已被使用。", "session_expired":"⚠️ 会话已过期。请重新生成邮箱。", "auth_error": "❌ 检查收件箱出错。请重试。", "no_messages": "📭 暂未收到任何消息。", "inbox_header": "📬 收件箱： {email}\n", "msg_block": "━━━━━━━━━━━━━━━━\n👤 来自： {sender}\n📌 主题： {subject}\n📝 内容：\n{body}", "adv_message": "📢 赞助商广告 — 请等待 5 秒钟以完成操作..."},
   "fr": {"btn_guida": "📖 Guide & Info", "btn_genera": "🚀 Générer E-mail", "btn_controlla":"🔄 Vérifier la boîte", "btn_sms": "📱 Numéros SMS", "sms_choice": "📱 Choisissez le type :", "sms_free_btn": "🆓 Gratuit (Public)", "sms_premium_btn":"💎 Premium (Privé)", "sms_loading": "⏳ Récupération...", "sms_error": "❌ Erreur de récupération. Riprova.", "sms_select": "📋 Sélectionnez un numéro :", "sms_msgs_header":"📨 Messages pour {number}:\n", "sms_no_msgs": "📭 Aucun message pour le moment.", "sms_msg_block":"━━━━━━━━━━━━━━━━\n👤 De: {sender}\n📝 Texte: {body}\n🕐 {time}", "sms_premium_info":"💎 Numéros Premium\n\nExclusifs pour vous.\n\n🔧 Bientôt disponible!", "welcome": "🛡️ PrivacyGuard Bot\n*Votre bouclier numérique.*\n\nGénérez des e-mails et numéros jetables.\n\nSélectionnez :", "guida": "ℹ️ INFO\n• E-mails actifs quelques heures.\n• Attendez les 5s de pub sans cliquer ailleurs.", "generating": "⏳ Génération en cours...", "gen_error_api":"❌ Service inaccessible.", "gen_error_acc":"❌ Erreur de création.", "gen_ready": "✨ E-mail généré!\n\n🔒 Cliquez pour vérifier.", "btn_vedi": "👁 Voir l'E-mail", "unlock_ok": "✅ Verified!\n\n📧 Votre E-mail :\n{email}", "token_invalid":"❌ Token invalide.", "session_expired":"⚠️ Session expirée.", "auth_error": "❌ Échec d'authentification.", "no_messages": "📭 Aucun message.", "inbox_header": "📬 Boîte : {email}\n", "msg_block": "━━━━━━━━━━━━━━━━\n👤 De: {sender}\n📌 Sujet: {subject}\n📝 Texte:\n{body}", "adv_message": "📢 Message Sponsorisé — Patientez 5 secondes..."},
   "de": {"btn_guida": "📖 Anleitung & Info", "btn_genera": "🚀 E-Mail erstellen", "btn_controlla":"🔄 Posteingang prüfen", "btn_sms": "📱 SMS-Nummern", "sms_choice": "📱 Typ wählen:", "sms_free_btn": "🆓 Kostenlos", "sms_premium_btn":"💎 Premium", "sms_loading": "⏳ Nummern laden...", "sms_error": "❌ Fehler. Erneut versuchen.", "sms_select": "📋 Nummer wählen:", "sms_msgs_header":"📨 Nachrichten für {number}:\n", "sms_no_msgs": "📭 Keine Nachrichten vorhanden.", "sms_msg_block":"━━━━━━━━━━━━━━━━\n👤 Von: {sender}\n📝 Text: {body}\n🕐 {time}", "sms_premium_info":"💎 Premium-Nummern\n\nExklusiv für Sie.\n\n🔧 In Kürze verfügbar!", "welcome": "🛡️ PrivacyGuard Bot\n*Ihr Schutzschild.*\n\nTemporäre E-Mails und SMS-Nummern.\n\nWählen Sie:", "guida": "ℹ️ INFO\n• E-Mails sind nur kurz aktiv.", "generating": "⏳ Wird erstellt...", "gen_error_api":"❌ Dienst nicht erreichbar.", "gen_error_acc":"❌ Fehler beim Erstellen.", "gen_ready": "✨ E-Mail generiert!\n\n🔒 Klicken zum Verifizieren.", "btn_vedi": "👁 E-Mail anzeigen", "unlock_ok": "✅ Verifiziert!\n\n📧 Ihre E-Mail:\n{email}", "token_invalid":"❌ Ungültiger Token.", "session_expired":"⚠️ Sitzung abglaufen.", "auth_error": "❌ Authentifizierungsfehler.", "no_messages": "📭 Keine Nachrichten.", "inbox_header": "📬 Posteingang: {email}\n", "msg_block": "━━━━━━━━━━━━━━━━\n👤 Von: {sender}\n📌 Betreff: {subject}\n📝 Text:\n{body}", "adv_message": "📢 Sponsor-Nachricht — Bitte warten Sie 5 Sekunden..."},
   "ru": {"btn_guida": "📖 Справка и Инфо", "btn_genera": "🚀 Создать почту", "btn_controlla":"🔄 Проверить почту", "btn_sms": "📱 SMS Номера", "sms_choice": "📱 Выберите тип номера:", "sms_free_btn": "🆓 Бесплатно", "sms_premium_btn":"💎 Премиум", "sms_loading": "⏳ Получение номеров...", "sms_error": "❌ Не удалось получить номера.", "sms_select": "📋 Выберите номер:", "sms_msgs_header":"📨 Сообщения для {number}:\n", "sms_no_msgs": "📭 Нет сообщений.", "sms_msg_block":"━━━━━━━━━━━━━━━━\n👤 От: {sender}\n📝 Текст: {body}\n🕐 {time}", "sms_premium_info":"💎 Премиум номера\n\nЭксклюзивно для вас.\n\n🔧 Функция скоро появится!", "welcome": "🛡️ PrivacyGuard Bot\n*Ваш щит конфиденциальности.*\n\nВременная почта и номера.\n\nВыберите:", "guida": "ℹ️ ИНФО\n• Почта активна несколько часов.", "generating": "⏳ Генерация...", "gen_error_api":"❌ Сервис недоступен.", "gen_error_acc":"❌ Ошибка создания.", "gen_ready": "✨ Почта создана!\n\n🔒 Нажмите для проверки.", "btn_vedi": "👁 Посмотреть почту", "unlock_ok": "✅ Проверено!\n\n📧 Ваша почта:\n{email}", "token_invalid":"❌ Неверный токен.", "session_expired":"⚠️ Сессия истекла.", "auth_error": "❌ Ошибка авторизации.", "no_messages": "📭 Сообщений нет.", "inbox_header": "📬 Ящик: {email}\n", "msg_block": "━━━━━━━━━━━━━━━━\n👤 От: {sender}\n📌 Тема: {subject}\n📝 Текст:\n{body}", "adv_message": "📢 Спонсорское сообщение — Пожалуйста, подождите 5 секунд..."}
}

def t(user_id: int, key: str) -> str:
    lang = user_lang.get(user_id, "en")
    return STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, ""))

# --- LOGICA ---
async def gestisci_pubblicita(user_id: int, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    if user_premium.get(user_id, False): return
    await context.bot.send_message(chat_id=chat_id, text=t(user_id, "adv_message"), parse_mode="HTML")
    await asyncio.sleep(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   # --- MODIFICA: Validazione Token per Sblocco ---
   if context.args:
       token = context.args[0]
       if token in pending_tokens:
           email = pending_tokens.pop(token)
           user_lang[update.effective_user.id] = user_lang.get(update.effective_user.id, "en")
           # Creiamo il pulsante per controllare la posta della nuova email
           keyboard = [[InlineKeyboardButton(t(update.effective_user.id, "btn_controlla"), callback_data="controlla")]]
           reply_markup = InlineKeyboardMarkup(keyboard)
           
           await update.message.reply_text(
               t(update.effective_user.id, "unlock_ok").format(email=email), 
               reply_markup=reply_markup, 
               parse_mode="HTML"
           )
           return
       else:
           await update.message.reply_text(t(update.effective_user.id, "token_invalid"), parse_mode="HTML")
           return

   keyboard = [
       [InlineKeyboardButton("IT", callback_data="lang_it"), InlineKeyboardButton("EN", callback_data="lang_en")],
       [InlineKeyboardButton("ES", callback_data="lang_es"), InlineKeyboardButton("AR", callback_data="lang_ar")],
       [InlineKeyboardButton("ZH", callback_data="lang_zh"), InlineKeyboardButton("FR", callback_data="lang_fr")],
       [InlineKeyboardButton("DE", callback_data="lang_de"), InlineKeyboardButton("RU", callback_data="lang_ru")]
   ]
   await update.message.reply_text("🌍 Seleziona lingua / Select language:", reply_markup=InlineKeyboardMarkup(keyboard))

async def imposta_lingua(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("lang_", "")
    user_lang[query.from_user.id] = lang
    await query.message.edit_text(f"✅ Lingua impostata: {lang.upper()}")
    keyboard = [
       [InlineKeyboardButton(t(query.from_user.id, "btn_guida"), callback_data="guida"), InlineKeyboardButton(t(query.from_user.id, "btn_genera"), callback_data="genera")],
       [InlineKeyboardButton(t(query.from_user.id, "btn_sms"), callback_data="sms")]
    ]
    await query.message.reply_text(t(query.from_user.id,"welcome"), reply_markup=InlineKeyboardMarkup(keyboard),parse_mode="HTML")

async def gestisci_guida(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
     query = update.callback_query
     await query.answer()
     await query.message.edit_text(t(query.from_user.id, "guida"), parse_mode="HTML")
    
async def gestisci_genera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    await query.message.edit_text(t(user_id, "generating"), parse_mode="HTML")
    await gestisci_pubblicita(user_id, context, query.message.chat.id)

    async with httpx.AsyncClient() as client:
        try:
            domains_resp = await client.get("https://api.mail.tm/domains")
            if domains_resp.status_code != 200:
                await query.message.edit_text("❌ Errore API domini.")
                return
            
            domain = domains_resp.json()['hydra:member'][0]['domain']
            
            username = f"user{secrets.token_hex(3)}"
            payload = {
                "address": f"{username}@{domain}",
                "password": "password123"
            }
            
            response = await client.post("https://api.mail.tm/accounts", json=payload)
        except Exception as e:
            await query.message.edit_text(f"❌ Errore di connessione: {str(e)}")
            return
        
    if response.status_code == 201:
        email = response.json().get("address")
        token = secrets.token_hex(4)
        pending_tokens[token] = email
    else:
        await query.message.edit_text(f"❌ Errore API {response.status_code}: {response.text}")
        return 
    
    # --- CREAZIONE DINAMICA LINK MONETIZZATO SHRINKME ---
    target_url = f"https://t.me/PrivacyGuard_RealBot?start={token}"
    
    try:
        async with httpx.AsyncClient() as client:
            shrink_api_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={target_url}"
            shrink_resp = await client.get(shrink_api_url)
            data = shrink_resp.json()
            
            if data.get("status") == "success":
                link = data.get("shortenedUrl")
            else:
                link = target_url
    except Exception:
        link = target_url

    keyboard = [[InlineKeyboardButton(t(user_id, "btn_vedi"), url=link)]]
    await query.message.edit_text(t(user_id, "gen_ready"), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def gestisci_controlla(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    # Rimandiamo il messaggio di nessun messaggio MA manteniamo il pulsante per poter ricontrollare ancora
    keyboard = [[InlineKeyboardButton(t(user_id, "btn_controlla"), callback_data="controlla")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"{t(user_id, 'no_messages')}", 
        reply_markup=reply_markup, 
        parse_mode="HTML"
    )

async def gestisci_sms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(t(query.from_user.id, "sms_choice"), parse_mode="HTML")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(imposta_lingua, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(gestisci_guida, pattern="^guida$"))
    app.add_handler(CallbackQueryHandler(gestisci_genera, pattern="^genera$"))
    app.add_handler(CallbackQueryHandler(gestisci_controlla, pattern="^controlla$"))
    app.add_handler(CallbackQueryHandler(sms_callback := CallbackQueryHandler(gestisci_sms, pattern="^sms$")))
    
    print("Bot avviato con successo!")
    app.run_polling()

if __name__ == "__main__":
   main()
