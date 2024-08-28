import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = 'ХХХ'
ADMIN_ID = ХХХ
MAIN_ADMIN_ID = ХХХ  # Ваш ID

# Путь к папке на диске C
DATABASE_DIR = 'C:/БД Бота'
os.makedirs(DATABASE_DIR, exist_ok=True)

# Файл для сохранения каталога
CATALOG_FILE = os.path.join(DATABASE_DIR, 'catalog_backup.json')
ADMINS_FILE = os.path.join(DATABASE_DIR, 'admins.json')

# Функция для сохранения каталога в файл
def save_catalog():
    try:
        with open(CATALOG_FILE, 'w') as file:
            json.dump(catalog, file)
        logger.info(f"Каталог успешно сохранен в {CATALOG_FILE}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении каталога: {e}")

# Функция для загрузки каталога из файла
def load_catalog():
    if os.path.exists(CATALOG_FILE):
        try:
            with open(CATALOG_FILE, 'r') as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Ошибка при загрузке каталога: {e}")
    return {
        'carpets': {'photos': [], 'descriptions': []},
        'runners': {'photos': [], 'descriptions': []},
        'palaces': {'photos': [], 'descriptions': []},
        'bath': {'photos': [], 'descriptions': []},
    }

def load_admins():
    if os.path.exists(ADMINS_FILE):
        try:
            with open(ADMINS_FILE, 'r') as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Ошибка при загрузке администраторов: {e}")
    return [ADMIN_ID]  # Изначально только один администратор

def save_admins(admins):
    try:
        with open(ADMINS_FILE, 'w') as file:
            json.dump(admins, file)
        logger.info(f"Список администраторов успешно сохранен в {ADMINS_FILE}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении администраторов: {e}")

# Инициализация каталога
catalog = load_catalog()

# Главное меню
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Ковры", callback_data='view_carpets')],
        [InlineKeyboardButton("Дорожки", callback_data='view_runners')],
        [InlineKeyboardButton("Паласы", callback_data='view_palaces')],
        [InlineKeyboardButton("Комплекты для ванной", callback_data='view_bath')],
        [InlineKeyboardButton("Контакты", callback_data='contacts')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        'Добро пожаловать в ВоронежКарпет & Inna! Выберите категорию:', reply_markup=reply_markup)
    
# Обработчик кнопки "Назад"
async def handle_back(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    # Удаляем предыдущее сообщение с медиа
    await query.message.delete()

    # Удаляем сообщения с фотографиями, если они есть
    if 'media_messages' in context.user_data:
        for message_id in context.user_data['media_messages']:
            try:
                await query.message.chat.delete_message(message_id)
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения с фото: {e}")
        # Убираем сохраненные сообщения из контекста
        del context.user_data['media_messages']

def is_admin(user_id):
    admins = load_admins()
    return user_id in admins

async def edit(update: Update, context: CallbackContext) -> None:
    if is_admin(update.message.from_user.id):
        keyboard = [
            [InlineKeyboardButton("Добавить Ковры", callback_data='add_carpets')],
            [InlineKeyboardButton("Добавить Дорожки", callback_data='add_runners')],
            [InlineKeyboardButton("Добавить Паласы", callback_data='add_palaces')],
            [InlineKeyboardButton("Добавить Комплекты для ванной", callback_data='add_bath')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Выберите раздел для добавления:', reply_markup=reply_markup)
    else:
        await update.message.reply_text("У вас нет прав для использования этой команды.")

# Функция для начала добавления фото и описания
async def add_section(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    section = query.data.split('_')[1]
    context.user_data['add_section'] = section
    await query.message.edit_text(f"Вы добавляете товар в раздел: {section.capitalize()}. Отправьте фото товара.")

# Команда /reedit для изменения или удаления фото и описаний
async def reedit(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("Изменить/Удалить Ковры", callback_data='reedit_carpets')],
            [InlineKeyboardButton("Изменить/Удалить Дорожки", callback_data='reedit_runners')],
            [InlineKeyboardButton("Изменить/Удалить Паласы", callback_data='reedit_palaces')],
            [InlineKeyboardButton("Изменить/Удалить Комплекты для ванной", callback_data='reedit_bath')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Выберите раздел для изменения/удаления:', reply_markup=reply_markup)
    else:
        await update.message.reply_text("У вас нет прав для использования этой команды.")

# Выбор раздела для редактирования
async def reedit_section(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    section = query.data.split('_')[1]
    if section in catalog and catalog[section]['photos']:
        context.user_data['reedit_section'] = section
        keyboard = [
            [InlineKeyboardButton(f"Фото {i+1}", callback_data=f'select_reedit_photo_{i}') for i in range(len(catalog[section]['photos']))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(f"Вы выбрали раздел: {section.capitalize()}. Выберите фото для редактирования:", reply_markup=reply_markup)
    else:
        await query.message.reply_text("Раздел пуст или не найден.")

# Выбор фото для редактирования
async def select_reedit_photo(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    index = int(query.data.split('_')[-1])
    section = context.user_data.get('reedit_section')
    if section and index < len(catalog[section]['photos']):
        context.user_data['selected_reedit_photo_index'] = index
        keyboard = [
            [InlineKeyboardButton("Изменить описание", callback_data='edit_reedit_description')],
            [InlineKeyboardButton("Удалить фото", callback_data='delete_reedit_photo')],
            [InlineKeyboardButton("Назад", callback_data='reedit_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(f"Выбрано фото {index + 1} из раздела {section.capitalize()}. Что вы хотите сделать?", reply_markup=reply_markup)
    else:
        await query.message.reply_text("Фото не найдено.")

# Функция для редактирования описания
async def edit_reedit_description(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    section = context.user_data.get('reedit_section')
    index = context.user_data.get('selected_reedit_photo_index')
    await query.message.edit_text("Отправьте новое описание для этого фото.")

# Обработчик текста и изменения описания
async def handle_reedit_text(update: Update, context: CallbackContext) -> None:
    # Проверка, есть ли контекст для редактирования раздела и фото
    section = context.user_data.get('reedit_section')
    index = context.user_data.get('selected_photo_index')

    if section and index is not None:
        if section in catalog and 0 <= index < len(catalog[section]['photos']):
            catalog[section]['descriptions'][index] = update.message.text
            save_catalog()
            await update.message.reply_text(f"Описание для фото {index + 1} в разделе {section.capitalize()} обновлено.")

            # Очистка контекста после успешного редактирования
            del context.user_data['selected_photo_index']
            del context.user_data['reedit_section']
        else:
            await update.message.reply_text("Ошибка: выбранный раздел или фото не найдены.")
    else:
        await update.message.reply_text("Ошибка: непредвиденное сообщение.")

# Удаление фото
async def delete_reedit_photo(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    section = context.user_data.get('reedit_section')
    index = context.user_data.get('selected_reedit_photo_index')
    if section and index is not None:
        del catalog[section]['photos'][index]
        del catalog[section]['descriptions'][index]
        save_catalog()
        await query.message.edit_text(f"Фото {index + 1} удалено из раздела {section.capitalize()}.")
        del context.user_data['selected_reedit_photo_index']
    else:
        await query.message.reply_text("Ошибка при удалении фото.")

# Обработчик кнопки "Назад" при редактировании
async def handle_reedit_back(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if 'reedit_section' in context.user_data:
        section = context.user_data['reedit_section']
        if section in catalog:
            await reedit_section(update, context)
        else:
            await query.message.reply_text("Ошибка: выбранный раздел не найден.")
    else:
        await query.message.reply_text("Ошибка: не установлен выбранный раздел.")

# Обработчик выбора раздела для просмотра
async def show_section(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    section = query.data.split('_')[1]
    
    if section in catalog:
        photos = catalog[section]['photos']
        descriptions = catalog[section]['descriptions']
        if photos:
            # Отправляем медиагруппу
            media = [InputMediaPhoto(photo_id, caption=desc) for photo_id, desc in zip(photos, descriptions)]
            media_messages = await query.message.reply_media_group(media)
            # Сохраняем идентификаторы сообщений с фотографиями
            context.user_data['media_messages'] = [msg.message_id for msg in media_messages]
            
            # Создаем кнопку "Назад"
            keyboard = [
                [InlineKeyboardButton("Назад", callback_data='back')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Отправляем кнопку "Назад" в отдельном сообщении
            await query.message.reply_text(text="Вернуться к предыдущему меню:", reply_markup=reply_markup)
        else:
            await query.message.reply_text(f"Раздел {section.capitalize()} пуст.")
    else:
        await query.message.reply_text("Ошибка: раздел не найден.")

# Обработчик текстовых сообщений для добавления описаний
async def handle_text_message(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data

    # Проверка, есть ли контекст для добавления описания
    if 'add_section' in user_data:
        section = user_data['add_section']
        if section in catalog and catalog[section]['photos']:
            # Проверка, что текстовое сообщение должно быть добавлено в описание
            if catalog[section]['descriptions'][-1] == "Описание отсутствует.":
                catalog[section]['descriptions'][-1] = update.message.text
                save_catalog()
                await update.message.reply_text("Описание добавлено.")
                del user_data['add_section']  # Очистка контекста
            else:
                await update.message.reply_text("Сначала отправьте фото для добавления.")
        else:
            await update.message.reply_text("Ошибка: выбранный раздел не найден.")
    elif 'reedit_section' in user_data and 'selected_reedit_photo_index' in user_data:
        # Проверка контекста для редактирования существующего фото
        section = user_data.get('reedit_section')
        index = user_data.get('selected_reedit_photo_index')

        if section and index is not None:
            if index < len(catalog[section]['descriptions']):
                catalog[section]['descriptions'][index] = update.message.text
                save_catalog()
                await update.message.reply_text(f"Описание для фото {index + 1} в разделе {section.capitalize()} обновлено.")
                
                # Очистка контекста после успешного редактирования
                del user_data['selected_reedit_photo_index']
                del user_data['reedit_section']
            else:
                await update.message.reply_text("Ошибка: индекс фото вне диапазона.")
        else:
            await update.message.reply_text("Ошибка: выбранный раздел или фото не найдены.")
    else:
        await update.message.reply_text("Ошибка: непредвиденное сообщение.")

# Обработчик сообщений (фото) для добавления
async def handle_photo_message(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    section = user_data.get('add_section')
    
    if section and update.message.photo:
        file_id = update.message.photo[-1].file_id
        catalog[section]['photos'].append(file_id)
        catalog[section]['descriptions'].append("Описание отсутствует.")
        save_catalog()
        await update.message.reply_text("Фото добавлено. Теперь отправьте описание.")
    else:
        await update.message.reply_text("Ошибка: непредвиденное сообщение.")

# Обработчик команды "Контакты"
async def contacts(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Назад", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        "Контакты:\n📍 Адрес: г. Воронеж, ул. Минёров, 3а\n📞 Телефон: 8 (910) 347-67-29 — Инна",
        reply_markup=reply_markup
    )

# Команда для добавления нового администратора
async def add_admin(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == MAIN_ADMIN_ID:
        if context.args:
            new_admin_id = int(context.args[0])
            admins = load_admins()
            if new_admin_id not in admins:
                admins.append(new_admin_id)
                save_admins(admins)
                await update.message.reply_text(f"Пользователь {new_admin_id} добавлен в администраторы.")
            else:
                await update.message.reply_text("Этот пользователь уже является администратором.")
        else:
            await update.message.reply_text("Укажите ID пользователя для добавления.")
    else:
        await update.message.reply_text("У вас нет прав для использования этой команды.")

# Команда для удаления администратора
async def remove_admin(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == MAIN_ADMIN_ID:
        if context.args:
            admin_id_to_remove = int(context.args[0])
            admins = load_admins()
            if admin_id_to_remove in admins:
                admins.remove(admin_id_to_remove)
                save_admins(admins)
                await update.message.reply_text(f"Пользователь {admin_id_to_remove} удален из администраторов.")
            else:
                await update.message.reply_text("Этот пользователь не является администратором.")
        else:
            await update.message.reply_text("Укажите ID пользователя для удаления.")
    else:
        await update.message.reply_text("У вас нет прав для использования этой команды.")

async def admin_list(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == MAIN_ADMIN_ID:
        admins = load_admins()
        if admins:
            admin_ids = "\n".join(str(admin_id) for admin_id in admins)
            await update.message.reply_text(f"Список администраторов:\n{admin_ids}")
        else:
            await update.message.reply_text("Список администраторов пуст.")
    else:
        await update.message.reply_text("У вас нет прав для использования этой команды.")

# Обработчик кнопок
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if query.data.startswith('view_'):
        await show_section(update, context)
    elif query.data.startswith('add_'):
        await add_section(update, context)
    elif query.data.startswith('reedit_'):
        await reedit_section(update, context)
    elif query.data.startswith('select_reedit_photo_'):
        await select_reedit_photo(update, context)
    elif query.data == 'edit_reedit_description':
        await edit_reedit_description(update, context)
    elif query.data == 'delete_reedit_photo':
        await delete_reedit_photo(update, context)
    elif query.data == 'reedit_back':
        await handle_reedit_back(update, context)

# Основная функция для запуска бота
def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('edit', edit))
    application.add_handler(CommandHandler('reedit', reedit))
    application.add_handler(CommandHandler('add_admin', add_admin, filters=filters.TEXT))
    application.add_handler(CommandHandler('remove_admin', remove_admin, filters=filters.TEXT))
    application.add_handler(CommandHandler('admin_list', admin_list))  # Новый обработчик команды
    application.add_handler(CallbackQueryHandler(contacts, pattern='contacts'))  # Обработчик для контактов
    application.add_handler(CallbackQueryHandler(handle_back, pattern='back'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == '__main__':
    main()
