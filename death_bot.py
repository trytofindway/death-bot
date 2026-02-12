import telebot
import time
import threading
from datetime import datetime

# ====== НАСТРОЙКИ ======
TOKEN = "7724574575:AAExnMBRGmn0L1vNZ_pgtkxaP1FEO1ABGqc"  # Твой бот
YOUR_ID = 405063690  # ТВОЙ ID (узнай у @userinfobot)
SOURCE_BOT = "@MWEssence_bot"  # Чей бот слушаем
# =======================

bot = telebot.TeleBot(TOKEN)
active_alerts = {}  # Активные уведомления
alert_counter = 0

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    global alert_counter
    
    # Проверяем что сообщение от нужного бота и для нас
    if (message.forward_from and 
        message.forward_from.username == "MWEssence_bot" and 
        message.chat.id == YOUR_ID):
        
        text = message.text or message.caption or ""
        
        # Проверяем что это сообщение о смерти
        if "пал от руки" in text or "убил" in text or "смерть" in text.lower():
            # Извлекаем информацию о смерти
            lines = text.split('\n')
            death_info = {
                'time': datetime.now(),
                'raw_text': text,
                'character': extract_character(text),
                'killer': extract_killer(text),
                'spam_count': 0,
                'original_message': message
            }
            
            alert_counter += 1
            alert_id = alert_counter
            active_alerts[alert_id] = death_info
            
            # Сразу отправляем подтверждение о получении
            bot.send_message(
                YOUR_ID,
                f"⚠️ ПОЛУЧЕНО УВЕДОМЛЕНИЕ О СМЕРТИ #{alert_id}\n"
                f"👤 Перс: {death_info['character']}\n"
                f"⚔️ Убийца: {death_info['killer']}\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"🔴 НАЧИНАЮ СПАМ! ЖМИ КНОПКУ!",
                reply_markup=get_confirm_keyboard(alert_id)
            )
            
            # Запускаем спам-машину
            thread = threading.Thread(target=spam_alert, args=(alert_id, death_info))
            thread.daemon = True
            thread.start()

def extract_character(text):
    """Вытаскивает имя персонажа из сообщения"""
    import re
    match = re.search(r"'([^']+)'", text)
    if match:
        return match.group(1)
    return "Неизвестно"

def extract_killer(text):
    """Вытаскивает имя убийцы из сообщения"""
    import re
    # Ищем после "от руки"
    if "от руки" in text:
        parts = text.split("от руки")
        if len(parts) > 1:
            killer_part = parts[1].split("[")[0].strip()
            return killer_part.strip("'\" ")
    return "Неизвестно"

def get_confirm_keyboard(alert_id):
    """Кнопка подтверждения"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        "✅ Я УВИДЕЛ УВЕДОМЛЕНИЕ", 
        callback_data=f"confirm_{alert_id}"
    ))
    return markup

def spam_alert(alert_id, death_info):
    """СПАМ-МАШИНА - отправляет сообщения каждую секунду"""
    # Ждем 3 секунды перед началом спама
    time.sleep(3)
    
    while alert_id in active_alerts:
        try:
            death_info['spam_count'] += 1
            
            # Разные сообщения для разнообразия
            messages = [
                f"🔴🔴🔴 СМЕРТЬ! #{alert_id} 🔴🔴🔴\n\n"
                f"Персонаж {death_info['character']} УМЕР!\n"
                f"Убийца: {death_info['killer']}\n"
                f"Сообщение #{death_info['spam_count']}\n\n"
                f"❗ ЖМИ КНОПКУ!",
                
                f"⚠️⚠️⚠️ НАПОМИНАНИЕ #{death_info['spam_count']} ⚠️⚠️⚠️\n\n"
                f"{death_info['character']} до сих пор мертв!\n"
                f"Ты проигнорировал уведомление от @MWEssence_bot!\n\n"
                f"👇 ЖМИ СЮДА 👇",
                
                f"💀 ТЫ УМЕР {death_info['spam_count']} РАЗ? НЕТ, ЭТО ОДНА СМЕРТЬ!\n\n"
                f"Перс: {death_info['character']}\n"
                f"Убийца: {death_info['killer']}\n\n"
                f"🔴 ПОДТВЕРДИ ПОЛУЧЕНИЕ! 🔴"
            ]
            
            # Циклично перебираем сообщения
            msg_index = (death_info['spam_count'] - 1) % len(messages)
            
            bot.send_message(
                YOUR_ID,
                messages[msg_index],
                reply_markup=get_confirm_keyboard(alert_id)
            )
            
            # СПАМ КАЖДУЮ СЕКУНДУ!
            time.sleep(1)
            
        except Exception as e:
            print(f"Ошибка спама: {e}")
            time.sleep(1)

@bot.callback_query_handler(func=lambda call: True)
def handle_confirm(call):
    """Обработка нажатия кнопки"""
    if call.from_user.id != YOUR_ID:
        bot.answer_callback_query(call.id, "❌ Не твоя кнопка!")
        return
    
    if call.data.startswith("confirm_"):
        alert_id = int(call.data.split("_")[1])
        
        if alert_id in active_alerts:
            death_info = active_alerts[alert_id]
            spam_count = death_info['spam_count']
            
            # Удаляем из активных (спам останавливается)
            del active_alerts[alert_id]
            
            # Изменяем сообщение с кнопкой
            bot.edit_message_text(
                chat_id=YOUR_ID,
                message_id=call.message.message_id,
                text=f"✅ ПОДТВЕРЖДЕНО! (ID: {alert_id})\n\n"
                     f"Персонаж: {death_info['character']}\n"
                     f"Убийца: {death_info['killer']}\n"
                     f"Отправлено спам-сообщений: {spam_count}\n"
                     f"Время подтверждения: {datetime.now().strftime('%H:%M:%S')}\n\n"
                     f"🤫 Спам остановлен!"
            )
            
            bot.answer_callback_query(
                call.id, 
                f"✅ Спам остановлен! Было {spam_count} сообщений"
            )
        else:
            bot.answer_callback_query(
                call.id, 
                "❌ Это уведомление уже подтверждено"
            )

@bot.message_handler(commands=['start'])
def start_command(message):
    """Команда старт"""
    if message.chat.id != YOUR_ID:
        bot.reply_to(message, "❌ Это личный бот")
        return
    
    bot.reply_to(
        message,
        f"🤖 Бот-пересыльщик смерти\n\n"
        f"Я слушаю сообщения от {SOURCE_BOT}\n"
        f"При получении уведомления о смерти - начинаю спам каждую секунду\n\n"
        f"📊 Активных уведомлений: {len(active_alerts)}\n"
        f"/status - проверить статус\n"
        f"/stop_all - остановить весь спам"
    )

@bot.message_handler(commands=['status'])
def status_command(message):
    """Статус активных уведомлений"""
    if message.chat.id != YOUR_ID:
        return
    
    if not active_alerts:
        bot.send_message(YOUR_ID, "✅ Нет активных уведомлений")
    else:
        text = "📋 АКТИВНЫЕ УВЕДОМЛЕНИЯ:\n\n"
        for aid, info in active_alerts.items():
            minutes = int((datetime.now() - info['time']).total_seconds() / 60)
            text += f"🆔 #{aid}: {info['character']}\n"
            text += f"   ⚔️ {info['killer']}\n"
            text += f"   ⏰ {minutes} мин назад\n"
            text += f"   🔔 спам-сообщений: {info['spam_count']}\n\n"
        bot.send_message(YOUR_ID, text)

@bot.message_handler(commands=['stop_all'])
def stop_all_command(message):
    """Экстренная остановка всего спама"""
    if message.chat.id != YOUR_ID:
        return
    
    count = len(active_alerts)
    active_alerts.clear()
    bot.send_message(
        YOUR_ID, 
        f"🛑 ЭКСТРЕННАЯ ОСТАНОВКА!\n"
        f"Отменено {count} активных уведомлений"
    )

# Запуск бота
if __name__ == "__main__":
    print("="*60)
    print("🤖 БОТ-ПЕРЕСЫЛЬЩИК СМЕРТИ ЗАПУЩЕН")
    print("="*60)
    print(f"📱 Слушаю бота: {SOURCE_BOT}")
    print(f"👤 Твой ID: {YOUR_ID}")
    print(f"⚠️ Режим: СПАМ КАЖДУЮ СЕКУНДУ")
    print("="*60)
    print("Жду уведомления о смерти...")
    
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("🔄 Перезапуск через 5 секунд...")
        time.sleep(5)
        bot.polling(none_stop=True)