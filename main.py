import os
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)

from config import (
    BOT_TOKEN, GET_NAME, MAIN_MENU, CHATTING, JOKE, 
    CHOOSE_CATEGORY, VIEW_PRODUCTS, GET_ADDRESS, PRODUCT_DETAIL
)
from handlers.conversation import (
    start, get_name, main_menu, chatting, joke_handler,
    get_address_handler, end_conversation
)
from handlers.products import (
    choose_category_handler, view_products_handler, product_detail_handler
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Запускает бота"""
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()

        # Настраиваем обработчики диалога
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
                MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
                CHATTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, chatting)],
                JOKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, joke_handler)],
                CHOOSE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_category_handler)],
                VIEW_PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, view_products_handler)],
                PRODUCT_DETAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_detail_handler)],
                GET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address_handler)],
            },
            fallbacks=[CommandHandler('cancel', end_conversation)],
        )

        application.add_handler(conv_handler)

        # Запускаем бота
        logger.info("Бот запущен...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    # Создаем папку для изображений, если её нет
    if not os.path.exists("images"):
        os.makedirs("images")
        logger.info("Создана папка 'images' для изображений товаров")
    
    main()