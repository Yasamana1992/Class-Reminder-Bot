import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from database import (
    get_admin_role,
    add_admin,
    remove_admin,
    add_student,
    get_students,
    delete_student
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if OWNER_ID == 0:
    raise RuntimeError("OWNER_ID is missing from .env")

if not TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN is missing. Check your .env file."
    )

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if is_owner(user.id):
        print("Owner logged in")
    else:
        print("Regular user logged in")

    await update.message.reply_text(
        "سلام! 👋\nبه ربات یادآوری کلاس‌ها خوش اومدی."
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = get_admin_role(user.id)

    if role is None:
        await update.message.reply_text("⛔ دسترسی غیرمجاز!")
        return

    if role == "owner":
        await update.message.reply_text("👑 پنل مدیریت مالک")
    elif role == "admin":
        await update.message.reply_text("🛠️ پنل مدیریت")
    else:
        await update.message.reply_text("⛔ نقش کاربری معتبر نیست.")

async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # فقط مالک اصلی اجازه دارد
    if not is_owner(user.id) or get_admin_role(user.id) != "owner":
        await update.message.reply_text("⛔ فقط مالک اجازه این کار را دارد.")
        return

    # بررسی شناسه ورودی
    if len(context.args) != 1:
        await update.message.reply_text(
            "روش استفاده:\n/add_admin USER_ID"
        )
        return

    try:
        new_admin_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("شناسه باید عددی باشد.")
        return

    if new_admin_id <= 0:
        await update.message.reply_text("شناسه واردشده معتبر نیست.")
        return

    # ثبت مدیر جدید
    added = add_admin(new_admin_id)

    if added:
        await update.message.reply_text(
            f"✅ مدیر جدید با شناسه {new_admin_id} ثبت شد."
        )
    else:
        await update.message.reply_text(
            "این شناسه از قبل در دیتابیس ثبت شده است."
        )

async def remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_owner(user.id) or get_admin_role(user.id) != "owner":
        await update.message.reply_text(
            "⛔ فقط مالک اجازه حذف مدیر را دارد."
        )
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "روش استفاده:\n/remove_admin USER_ID"
        )
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("شناسه باید عددی باشد.")
        return

    if target_id <= 0:
        await update.message.reply_text("شناسه معتبر نیست.")
        return

    removed = remove_admin(target_id)

    if removed:
        await update.message.reply_text("✅ مدیر با موفقیت حذف شد.")
    else:
        await update.message.reply_text(
            "این شناسه مدیر نیست یا اجازه حذف آن وجود ندارد."
        )
    
async def add_student_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = get_admin_role(user.id)

    # بررسی دسترسی
    if role not in ("owner", "admin"):
        await update.message.reply_text(
            "⛔️ فقط مالک و مدیر اجازه افزودن دانش‌آموز را دارند."
        )
        return

    # بررسی تعداد ورودی‌ها
    if len(context.args) < 3:
        await update.message.reply_text(
            "روش استفاده:\n/add_student FirstName LastName Phone"
        )
        return

    # جداسازی نام و شماره تلفن
    full_name = " ".join(context.args[:-1])
    phone = context.args[-1]

    # ذخیره در دیتابیس
    try:
        added = add_student(full_name=full_name, phone=phone)

        if added:
            await update.message.reply_text(
                f"✅ دانش‌آموز {full_name} با موفقیت ثبت شد."
            )
        else:
            await update.message.reply_text(
                "ثبت دانش‌آموز انجام نشد."
            )

    except ValueError as error:
        await update.message.reply_text(
            f"⚠️ خطا: {error}"
        )

async def students_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = get_admin_role(user.id)

    # بررسی دسترسی
    if role not in ("owner", "admin"):
        await update.message.reply_text(
            "⛔️ فقط مالک و مدیر اجازه مشاهده فهرست دانش‌آموزان را دارند."
        )
        return

    # دریافت فهرست از دیتابیس
    students = get_students()

    if not students:
        await update.message.reply_text(
            "هنوز هیچ دانش‌آموزی ثبت نشده است."
        )
        return

    # آماده‌سازی متن فهرست
    message = "📚 فهرست دانش‌آموزان:\n\n"

    for student in students:
        student_id, full_name, phone, telegram_id, created_at = student

        message += (
            f"🆔 شناسه: {student_id}\n"
            f"👤 نام: {full_name}\n"
            f"📞 تلفن: {phone or 'ثبت نشده'}\n"
            "--------------------\n"
        )

    await update.message.reply_text(message)

async def delete_student_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = get_admin_role(user.id)

    # بررسی دسترسی
    if role not in ("owner", "admin"):
        await update.message.reply_text(
            "⛔️ فقط مالک و مدیر اجازه حذف دانش‌آموز را دارند."
        )
        return

    # بررسی شناسه ورودی
    if len(context.args) != 1:
        await update.message.reply_text(
            "روش استفاده:\n/delete_student STUDENT_ID"
        )
        return

    try:
        student_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "⚠️ شناسه دانش‌آموز باید عددی باشد."
        )
        return

    if student_id <= 0:
        await update.message.reply_text(
            "⚠️ شناسه واردشده معتبر نیست."
        )
        return

    # حذف از دیتابیس
    removed = delete_student(student_id)

    if removed:
        await update.message.reply_text(
            f"✅ دانش‌آموز با شناسه {student_id} حذف شد."
        )
    else:
        await update.message.reply_text(
            "دانش‌آموزی با این شناسه پیدا نشد."
        )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("add_admin", add_admin_command))
    app.add_handler(CommandHandler("remove_admin", remove_admin_command))
    app.add_handler(CommandHandler("add_student", add_student_command))
    app.add_handler(CommandHandler("students", students_command))
    app.add_handler(CommandHandler("delete_student", delete_student_command))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()