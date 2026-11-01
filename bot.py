import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import sqlite3
from database import (
    get_admin_role,
    add_admin,
    remove_admin,
    add_student,
    get_students,
    delete_student,
    add_class,
    get_classes,
    enroll_student,
    get_student_classes,
    get_class_students,
    add_class_schedule,
    get_class_schedules,
    generate_student_link_code,
    link_student_telegram
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
    message = update.effective_message

    if context.args:
        code = context.args[0]

        try:
            student_id, full_name = link_student_telegram(
                code=code,
                telegram_id=user.id
            )

            await message.reply_text(
                f"سلام {full_name} عزیز! 🌷\n"
                "حساب تلگرام شما با موفقیت به پرونده هنرجویی‌تان متصل شد."
            )

        except ValueError as error:
            await message.reply_text(
                f"اتصال انجام نشد: {error}"
            )

        return

    if is_owner(user.id):
        print("Owner logged in")
    else:
        print("Regular user logged in")

    await message.reply_text(
        "سلام! 👋\n"
        "به ربات یادآوری کلاس‌ها خوش اومدی."
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

async def add_class_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = get_admin_role(user.id)

    if role not in ("owner", "admin"):
        await update.message.reply_text(
            "⛔️ فقط مالک و مدیر اجازه افزودن کلاس را دارند."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "روش استفاده:\n/add_class Class Name"
        )
        return

    class_name = " ".join(context.args)

    try:
        class_id = add_class(class_name)

        await update.message.reply_text(
            f"✅ کلاس {class_name} با موفقیت ثبت شد.\n"
            f"شناسه کلاس: {class_id}"
        )

    except ValueError as error:
        await update.message.reply_text(
            f"⚠️ خطا: {error}"
        )

async def classes_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user
    role = get_admin_role(user.id)

    if role not in ("owner", "admin"):
        await update.message.reply_text(
            "⛔️ فقط مالک و مدیر اجازه مشاهده فهرست کلاس‌ها را دارند."
        )
        return

    classes = get_classes()

    if not classes:
        await update.message.reply_text(
            "هنوز هیچ کلاسی ثبت نشده است."
        )
        return

    message = "📚 فهرست کلاس‌ها:\n\n"

    for class_id, class_name, description, created_at in classes:
        message += (
            f"🆔 شناسه: {class_id}\n"
            f"📖 نام کلاس: {class_name}\n"
            f"📝 توضیحات: {description or 'ندارد'}\n"
            "--------------------\n"
        )

    await update.message.reply_text(message)

async def enroll_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user
    role = get_admin_role(user.id)

    if role not in ("owner", "admin"):
        await update.message.reply_text(
            "⛔️ فقط مالک و مدیر اجازه ثبت‌نام دارند."
        )
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "روش استفاده:\n/enroll STUDENT_ID CLASS_ID"
        )
        return

    try:
        student_id = int(context.args[0])
        class_id = int(context.args[1])
    except ValueError:
        await update.message.reply_text(
            "⚠️ شناسه دانش‌آموز و کلاس باید عددی باشند."
        )
        return

    if student_id <= 0 or class_id <= 0:
        await update.message.reply_text(
            "⚠️ شناسه‌ها باید عدد مثبت باشند."
        )
        return

    try:
        enrolled = enroll_student(student_id, class_id)

        if enrolled:
            await update.message.reply_text(
                "✅ دانش‌آموز با موفقیت در کلاس ثبت‌نام شد."
            )
        else:
            await update.message.reply_text(
                "این دانش‌آموز قبلاً در این کلاس ثبت‌نام شده است."
            )

    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "⚠️ دانش‌آموز یا کلاس با این شناسه وجود ندارد."
        )

async def student_classes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = get_admin_role(user.id)

    if role not in ("owner", "admin"):
        await update.message.reply_text("شما مجوز دسترسی به این بخش را ندارید.")
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text(
            "فرمت دستور نادرست است.\n"
            "روش استفاده:\n"
            "/student_classes شناسه_دانش‌آموز"
        )
        return

    student_id = int(context.args[0])

    if student_id <= 0:
        await update.message.reply_text("شناسه دانش‌آموز نامعتبر است.")
        return

    classes = get_student_classes(student_id)

    if not classes:
        await update.message.reply_text(
            "این دانش‌آموز در هیچ کلاسی ثبت‌نام نشده است."
        )
        return

    message = f"کلاس‌های دانش‌آموز با شناسه {student_id}:\n"

    for class_id, class_name in classes:
        message += f"\nشناسه کلاس: {class_id} | نام کلاس: {class_name}"

    await update.message.reply_text(message)

async def class_students_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = get_admin_role(user.id)

    if role not in ("owner", "admin"):
        await update.effective_message.reply_text(
            "شما مجوز دسترسی به این بخش را ندارید."
        )
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.effective_message.reply_text(
            "فرمت دستور نادرست است.\n"
            "روش استفاده:\n"
            "/class_students شناسه_کلاس"
        )
        return

    class_id = int(context.args[0])

    if class_id <= 0:
        await update.effective_message.reply_text("شناسه کلاس نامعتبر است.")
        return

    students = get_class_students(class_id)

    if not students:
        await update.effective_message.reply_text(
            "هیچ دانش‌آموزی در این کلاس ثبت‌نام نکرده است."
        )
        return

    message = f"دانش‌آموزان کلاس با شناسه {class_id}:\n"

    for student_id, full_name, phone in students:
        message += (
            f"\nشناسه: {student_id}"
            f"\nنام: {full_name}"
            f"\nشماره تماس: {phone}\n"
        )

    await update.effective_message.reply_text(message)

async def add_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = get_admin_role(user.id)

    if role not in ("owner", "admin"):
        await update.effective_message.reply_text(
            "شما مجوز دسترسی به این بخش را ندارید."
        )
        return

    if len(context.args) != 4:
        await update.effective_message.reply_text(
            "فرمت دستور نادرست است.\n"
            "روش استفاده:\n"
            "/add_schedule شناسه_کلاس شماره_روز ساعت_شروع ساعت_پایان\n\n"
            "شماره روزها:\n"
            "۰: شنبه\n۱: یکشنبه\n۲: دوشنبه\n۳: سه‌شنبه\n"
            "۴: چهارشنبه\n۵: پنجشنبه\n۶: جمعه\n\n"
            "مثال:\n"
            "/add_schedule 1 0 10:00 12:00"
        )
        return

    class_id, day, start_time, end_time = context.args

    if not class_id.isdigit() or not day.isdigit():
        await update.effective_message.reply_text(
            "شناسه کلاس و شماره روز باید عدد باشند."
        )
        return

    class_id = int(class_id)
    day = int(day)

    if class_id <= 0 or day not in range(7):
        await update.effective_message.reply_text(
            "شناسه کلاس یا شماره روز نامعتبر است."
        )
        return

    try:
        schedule_id = add_class_schedule(
            class_id, day, start_time, end_time
        )

        days = [
            "شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه",
            "چهارشنبه", "پنجشنبه", "جمعه"
        ]

        await update.effective_message.reply_text(
            f"برنامه کلاس با موفقیت ثبت شد. ✅\n\n"
            f"شناسه برنامه: {schedule_id}\n"
            f"روز: {days[day]}\n"
            f"ساعت: {start_time} تا {end_time}"
        )

    except ValueError as error:
        await update.effective_message.reply_text(
            f"خطا در ثبت برنامه: {error}"
        )

    except sqlite3.IntegrityError:
        await update.effective_message.reply_text(
            "این کلاس وجود ندارد یا اطلاعات ثبت برنامه معتبر نیست."
        )

async def class_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = get_admin_role(user.id)

    if role not in ("owner", "admin"):
        await update.effective_message.reply_text(
            "شما مجوز دسترسی به این بخش را ندارید."
        )
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.effective_message.reply_text(
            "فرمت دستور نادرست است.\n"
            "روش استفاده:\n"
            "/class_schedule شناسه_کلاس"
        )
        return

    class_id = int(context.args[0])

    if class_id <= 0:
        await update.effective_message.reply_text(
            "شناسه کلاس نامعتبر است."
        )
        return

    schedules = get_class_schedules(class_id)

    if not schedules:
        await update.effective_message.reply_text(
            "برای این کلاس هنوز برنامه‌ای ثبت نشده است."
        )
        return

    days = [
        "شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه",
        "چهارشنبه", "پنجشنبه", "جمعه"
    ]

    message = f"برنامه هفتگی کلاس با شناسه {class_id}:\n"

    for schedule_id, day, start_time, end_time in schedules:
        message += (
            f"\n{days[day]}: {start_time} تا {end_time}"
        )

    await update.effective_message.reply_text(message)

async def generate_link_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user
    message = update.effective_message

    role = get_admin_role(user.id)

    if role not in ("owner", "admin"):
        await message.reply_text("شما اجازه انجام این کار رو ندارید.")
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await message.reply_text(
            "فرمت دستور:\n/generate_link STUDENT_ID"
        )
        return

    student_id = int(context.args[0])

    if student_id <= 0:
        await message.reply_text("شناسه هنرجو معتبر نیست.")
        return

    try:
        code = generate_student_link_code(student_id)

        await message.reply_text(
            f"کد اتصال هنرجو:\n{code}\n\n"
            "این کد را به‌صورت خصوصی برای هنرجو بفرستید.\n"
            "اعتبار کد ۲۴ ساعت است."
        )

    except ValueError as error:
        await message.reply_text(str(error))

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("add_admin", add_admin_command))
    app.add_handler(CommandHandler("remove_admin", remove_admin_command))
    app.add_handler(CommandHandler("add_student", add_student_command))
    app.add_handler(CommandHandler("students", students_command))
    app.add_handler(CommandHandler("delete_student", delete_student_command))
    app.add_handler(CommandHandler("add_class", add_class_command))
    app.add_handler(CommandHandler("classes", classes_command))
    app.add_handler(CommandHandler("enroll", enroll_command))
    app.add_handler(CommandHandler("student_classes", student_classes_command))
    app.add_handler(CommandHandler("class_students", class_students_command))
    app.add_handler(CommandHandler("add_schedule", add_schedule_command))
    app.add_handler(CommandHandler("class_schedule", class_schedule_command))
    app.add_handler(CommandHandler("generate_link", generate_link_command))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()