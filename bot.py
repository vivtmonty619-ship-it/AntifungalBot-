import os
import logging
import random
from typing import Dict, List, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==================== CONFIG ====================
PASS_PERCENTAGE = 60

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== QUESTIONS DATABASE ====================
QUESTIONS = [
    {
        "question": "Which of the following antifungal drugs is a polyene that binds to ergosterol?",
        "options": ["Fluconazole", "Amphotericin B", "Caspofungin", "Terbinafine"],
        "correct": 1
    },
    {
        "question": "Which azole antifungal is commonly used for vaginal candidiasis?",
        "options": ["Ketoconazole", "Fluconazole", "Voriconazole", "Itraconazole"],
        "correct": 1
    },
    {
        "question": "Which echinocandin antifungal inhibits β-glucan synthase?",
        "options": ["Amphotericin B", "Flucytosine", "Caspofungin", "Griseofulvin"],
        "correct": 2
    },
    {
        "question": "Terbinafine is primarily used to treat:",
        "options": ["Systemic candidiasis", "Aspergillosis", "Dermatophytosis", "Cryptococcal meningitis"],
        "correct": 2
    },
    {
        "question": "Which antifungal agent is converted to 5-fluorouracil inside fungal cells?",
        "options": ["Fluconazole", "Flucytosine", "Flucitosine", "Fluorouracil"],
        "correct": 1
    },
    {
        "question": "Griseofulvin is derived from species of:",
        "options": ["Penicillium", "Aspergillus", "Candida", "Cryptococcus"],
        "correct": 0
    },
    {
        "question": "Which azole antifungal is the drug of choice for invasive aspergillosis?",
        "options": ["Fluconazole", "Itraconazole", "Voriconazole", "Ketoconazole"],
        "correct": 2
    },
    {
        "question": "Amphotericin B is often combined with which drug to treat cryptococcal meningitis?",
        "options": ["Flucytosine", "Caspofungin", "Terbinafine", "Griseofulvin"],
        "correct": 0
    },
    {
        "question": "Which antifungal drug class inhibits ergosterol synthesis by inhibiting lanosterol 14α-demethylase?",
        "options": ["Polyenes", "Azoles", "Echinocandins", "Allylamines"],
        "correct": 1
    },
    {
        "question": "Caspofungin is active against which of the following?",
        "options": ["Cryptococcus neoformans", "Candida species", "Zygomycetes", "Dermatophytes"],
        "correct": 1
    },
    {
        "question": "Which antifungal drug can cause infusion-related flushing reactions?",
        "options": ["Fluconazole", "Amphotericin B", "Caspofungin", "Terbinafine"],
        "correct": 1
    },
    {
        "question": "Terbinafine inhibits which enzyme in the ergosterol biosynthesis pathway?",
        "options": ["14α-demethylase", "Squalene epoxidase", "β-glucan synthase", "Thymidylate synthase"],
        "correct": 1
    },
    {
        "question": "Flucytosine resistance can develop rapidly if used:",
        "options": ["In high doses", "As monotherapy", "With amphotericin B", "For less than 2 weeks"],
        "correct": 1
    },
    {
        "question": "Which azole antifungal has significant CYP450 drug interactions?",
        "options": ["Fluconazole", "Ketoconazole", "Voriconazole", "Isavuconazole"],
        "correct": 2
    },
    {
        "question": "Griseofulvin is deposited in:",
        "options": ["Liver", "Kidneys", "Skin, hair, and nails", "Lungs"],
        "correct": 2
    }
]

assert len(QUESTIONS) == 15

# ==================== HELPER FUNCTIONS ====================
def get_random_questions() -> List[Dict[str, Any]]:
    questions_copy = QUESTIONS.copy()
    random.shuffle(questions_copy)
    return questions_copy

def calculate_grade(score: int, total: int):
    percentage = (score / total) * 100
    if percentage >= 90:
        grade = "A"
    elif percentage >= 80:
        grade = "B"
    elif percentage >= 70:
        grade = "C"
    elif percentage >= 60:
        grade = "D"
    else:
        grade = "F"
    passed = percentage >= PASS_PERCENTAGE
    return percentage, grade, passed

def build_question_message(question_data, current_q, total_q):
    return f"Question {current_q}/{total_q}\n\n{question_data['question']}"

def build_options_keyboard(q_index, question_data):
    keyboard = []
    for idx, option in enumerate(question_data["options"]):
        callback_data = f"answer_{q_index}_{idx}"
        keyboard.append([InlineKeyboardButton(option, callback_data=callback_data)])
    return InlineKeyboardMarkup(keyboard)

def build_restart_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Restart Exam", callback_data="restart")]])

# ==================== HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data["questions"] = get_random_questions()
    context.user_data["current_question"] = 0
    context.user_data["score"] = 0
    context.user_data["total"] = 15
    context.user_data["answered"] = [False] * 15

    welcome_msg = (
        f"Welcome {user.first_name}! 🩺\n\n"
        f"This is a Professional MCQ Exam on Antifungal Pharmacology.\n"
        f"You will answer 15 randomized questions.\n"
        f"Passing score: {PASS_PERCENTAGE}%\n\n"
        f"Press the button below to begin."
    )

    keyboard = [[InlineKeyboardButton("Start Exam", callback_data="next")]]
    await update.message.reply_text(
        welcome_msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_question(query, context):
    user_data = context.user_data
    current = user_data["current_question"]
    total = user_data["total"]

    if current >= total:
        score = user_data["score"]
        percentage, grade, passed = calculate_grade(score, total)
        status = "PASSED ✅" if passed else "FAILED ❌"
        result_msg = (
            f"🎓 Exam Completed\n\n"
            f"Score: {score}/{total}\n"
            f"Percentage: {percentage:.1f}%\n"
            f"Grade: {grade}\n"
            f"Status: {status}\n\n"
        )
        if passed:
            result_msg += "Excellent performance!"
        else:
            result_msg += "Review antifungal pharmacology and try again."

        await query.edit_message_text(result_msg, reply_markup=build_restart_keyboard())
        return

    question_data = user_data["questions"][current]
    question_text = build_question_message(question_data, current + 1, total)
    await query.edit_message_text(question_text, reply_markup=build_options_keyboard(current, question_data))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = context.user_data

    if query.data == "restart":
        context.user_data.clear()
        await start(update, context)
        return

    if query.data == "next":
        await show_question(query, context)
        return

    if query.data.startswith("answer_"):
        _, q_idx_str, opt_idx_str = query.data.split("_")
        q_index = int(q_idx_str)
        selected_idx = int(opt_idx_str)

        if user_data["answered"][q_index]:
            await query.answer("You have already answered this question!", show_alert=True)
            return

        question_data = user_data["questions"][q_index]
        correct_idx = question_data["correct"]

        if selected_idx == correct_idx:
            user_data["score"] += 1
            feedback = "✅ Correct!"
        else:
            correct_answer = question_data["options"][correct_idx]
            feedback = f"❌ Incorrect. Correct answer: {correct_answer}"

        user_data["answered"][q_index] = True
        user_data["current_question"] += 1

        await query.edit_message_text(feedback)
        await show_question(query, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

# ==================== MAIN ====================
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("No BOT_TOKEN environment variable set")

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(error_handler)

    logger.info("Bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
