from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_contact_keyboard():
    """Kontakt so'rash tugmasi"""
    contact_button = KeyboardButton(
        text="📞 Kontaktni yuborish",
        request_contact=True
    )

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[contact_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def remove_keyboard():
    """Keyboard olib tashlash"""
    return ReplyKeyboardRemove()