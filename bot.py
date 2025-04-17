import logging
import requests
import json
import time
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, \
    ConversationHandler
import tool_8kbet

# Cấu hình logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token từ BotFather - Thay YOUR_TOKEN_HERE bằng token của bạn
TOKEN = "7693496238:AAFU1ctY0aMbR8_6u-dhlmT8sE52JzqAFPo"

# Cấu hình API SePay - Thay thế bằng thông tin API của bạn
SEPAY_API_URL = "https://api.sepay.vn/api"
SEPAY_API_KEY = "YOUR_SEPAY_API_KEY"
SEPAY_SECRET_KEY = "YOUR_SEPAY_SECRET_KEY"
MERCHANT_ID = "YOUR_MERCHANT_ID"

# Trạng thái hội thoại cho các luồng nhập liệu
AMOUNT, CONFIRM = range(2)
# Thêm trạng thái cho kiểm tra tài khoản 8KBET
WAITING_8KBET_ACCOUNTS = 3


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gửi tin nhắn chào mừng khi nhận lệnh /start."""
    user = update.effective_user
    welcome_message = f"✨ Chào mừng bạn trở lại! ✨\n\n"
    welcome_message += "🎮 Chọn Site muốn nhập\n"
    welcome_message += "ℹ️ Xem thông tin chi tiết\n"
    welcome_message += "💰 Nạp tiền\n"
    welcome_message += "Liên hệ hỗ trợ khi cần\n\n"
    welcome_message += "🚀 Chúc bạn có trải nghiệm tuyệt vời!"

    # Tạo inline keyboard
    keyboard = [
        [InlineKeyboardButton("🎮 Chọn Site muốn nhập", callback_data='game')],
        [InlineKeyboardButton("❓ Check lạm dụng", callback_data='lamdung')],
        [InlineKeyboardButton("ℹ️ Thông Tin", callback_data='info')],
        [InlineKeyboardButton("💰 Nạp Tiền", callback_data='deposit')],
        [InlineKeyboardButton("📦 Các nick đã nhập", callback_data='orders')],
        [InlineKeyboardButton("📞 CSKH", callback_data='support')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý khi người dùng nhấn vào nút."""
    query = update.callback_query
    await query.answer()  # Đánh dấu là đã xử lý callback

    # Phản hồi dựa trên nút được nhấn
    if query.data == 'game':
        await game_menu(query)
    elif query.data == 'lamdung':
        await check_menu(query)
    elif query.data == 'info':
        await info_menu(query)
    elif query.data == 'deposit':
        await deposit_menu(query)
    elif query.data == 'orders':
        await orders_menu(query)
    elif query.data == 'support':
        await support_menu(query)
    elif query.data == 'check_fb88':
        await check_f8bee(query)
    elif query.data == 'check_j88':
        await check_j88(query)
    elif query.data == 'check_8kbet':
        await check_8kbet(query)
    elif query.data == 'deposit_sepay':
        await handle_sepay_deposit(query, context)
    elif query.data == 'deposit_history':
        await show_deposit_history(query)
    elif query.data == 'payment_complete':
        await handle_payment_complete(query, context)
    elif query.data == 'back_to_main':
        # Quay lại menu chính
        keyboard = [
            [InlineKeyboardButton("🎮 Chọn Site muốn nhập", callback_data='game')],
            [InlineKeyboardButton("❓ Chọn Site muốn check lạm dụng", callback_data='lamdung')],
            [InlineKeyboardButton("ℹ️ Thông Tin", callback_data='info')],
            [InlineKeyboardButton("💰 Nạp Tiền", callback_data='deposit')],
            [InlineKeyboardButton("📦 Các nick đã nhập", callback_data='orders')],
            [InlineKeyboardButton("📞 CSKH", callback_data='support')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="✨ Chào mừng bạn trở lại! ✨\n\nHãy chọn một chức năng:",
            reply_markup=reply_markup
        )

async def check_menu(query):
    """Hiển thị menu game."""
    games = [
        [InlineKeyboardButton("✅ F8bet", callback_data='check_fb88')],
        [InlineKeyboardButton("✅ J88", callback_data='check_j88')],
        [InlineKeyboardButton("✅ 8KBET", callback_data='check_8kbet')],
        [InlineKeyboardButton("⬅️ Quay lại", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(games)
    await query.edit_message_text(
        text="🎮 Chọn site bạn muốn check:",
        reply_markup=reply_markup
    )


async def check_8kbet(query):
    """Hiển thị menu kiểm tra tài khoản 8KBET."""
    keyboard = [
        [InlineKeyboardButton("Kiểm tra tài khoản", callback_data='input_8kbet_accounts')],
        [InlineKeyboardButton("⬅️ Quay lại", callback_data='check_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="🎮 8KBET - Chọn chức năng:",
        reply_markup=reply_markup
    )


# Thêm hàm xử lý nhập tài khoản 8KBET
async def input_8kbet_accounts(update, context):
    """Xử lý nhập danh sách tài khoản 8KBET."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        text="Vui lòng nhập danh sách tài khoản 8KBET, mỗi tài khoản cách nhau bởi dấu cách.\n"
             "Ví dụ: account1 account2 account3"
    )

    # Đặt trạng thái tiếp theo để xử lý tin nhắn văn bản
    return WAITING_8KBET_ACCOUNTS


# Thêm hàm xử lý khi người dùng gửi danh sách tài khoản
async def process_8kbet_accounts(update, context):
    """Xử lý danh sách tài khoản và hiển thị kết quả."""
    accounts_input = update.message.text.strip()

    # Gửi thông báo đang xử lý
    processing_message = await update.message.reply_text("⏳ Đang kiểm tra tài khoản, vui lòng đợi...")

    # Sử dụng hàm từ tool_8kbet để kiểm tra tài khoản
    results = tool_8kbet.check_multiple_accounts(accounts_input)

    # Tạo văn bản kết quả
    result_text = "🔍 Kết quả kiểm tra tài khoản 8KBET:\n\n"
    for result in results:
        result_text += f"• {result}\n"

    # Tạo nút quay lại
    keyboard = [[InlineKeyboardButton("⬅️ Quay lại", callback_data='check_8kbet')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Gửi kết quả và xóa tin nhắn đang xử lý
    await processing_message.delete()
    await update.message.reply_text(result_text, reply_markup=reply_markup)

    # Kết thúc hội thoại
    return ConversationHandler.END
async def game_menu(query):
    """Hiển thị menu game."""
    games = [
        [InlineKeyboardButton("🎲 F8bet", callback_data='f8bet')],
        [InlineKeyboardButton("🎲 New88", callback_data='new88')],
        [InlineKeyboardButton("🎲 J88", callback_data='j88')],
        [InlineKeyboardButton("🎲 8KBET", callback_data='8kbet')],
        [InlineKeyboardButton("⬅️ Quay lại", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(games)
    await query.edit_message_text(
        text="🎮 Chọn game bạn muốn chơi:",
        reply_markup=reply_markup
    )


async def info_menu(query):
    """Hiển thị menu thông tin."""
    info_options = [
        [InlineKeyboardButton("📝 Hướng dẫn sử dụng", callback_data='info_guide')],
        [InlineKeyboardButton("💰 Bảng giá dịch vụ", callback_data='info_price')],
        [InlineKeyboardButton("❓ Câu hỏi thường gặp", callback_data='info_faq')],
        [InlineKeyboardButton("⬅️ Quay lại", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(info_options)
    await query.edit_message_text(
        text="ℹ️ Xem thông tin chi tiết:",
        reply_markup=reply_markup
    )


async def orders_menu(query):
    """Hiển thị thông tin đơn hàng."""
    # Đây là nơi bạn sẽ hiển thị thông tin đơn hàng thực tế từ cơ sở dữ liệu
    orders_info = "📦 Thông tin đơn hàng của bạn:\n\n"
    orders_info += "- Đơn #12345: Đang vận chuyển\n"
    orders_info += "- Đơn #12346: Đã xác nhận\n"
    orders_info += "- Đơn #12347: Đang chuẩn bị hàng"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Quay lại", callback_data='back_to_main')]
    ])

    await query.edit_message_text(
        text=orders_info,
        reply_markup=reply_markup
    )


async def support_menu(query):
    """Hiển thị thông tin hỗ trợ khách hàng."""
    support_info = "📞 Thông tin liên hệ CSKH:\n\n"


    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Chat với CSKH", url="https://t.me/tietkiemchob")],
        [InlineKeyboardButton("⬅️ Quay lại", callback_data='back_to_main')]
    ])

    await query.edit_message_text(
        text=support_info,
        reply_markup=reply_markup
    )


async def deposit_menu(query):
    """Hiển thị menu nạp tiền với SePay."""
    deposit_options = [
        [InlineKeyboardButton("💳 Nạp tiền", callback_data='deposit_sepay')],
        [InlineKeyboardButton("📊 Lịch sử giao dịch", callback_data='deposit_history')],
        [InlineKeyboardButton("⬅️ Quay lại", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(deposit_options)
    await query.edit_message_text(
        text="💰 Chọn phương thức nạp tiền:",
        reply_markup=reply_markup
    )


async def handle_sepay_deposit(query, context):
    """Bắt đầu quy trình nạp tiền qua SePay."""
    # Hiển thị thông tin và hướng dẫn về SePay
    sepay_info = "💳 **Nạp tiền**\n\n"
    sepay_info += "Vui lòng nhập số tiền bạn muốn nạp (VND):\n"
    sepay_info += "Ví dụ: 100000, 500000, 1000000\n\n"
    sepay_info += "⚠️ Lưu ý: Số tiền tối thiểu là 10,000 VND"

    # Lưu trữ user_id và chat_id để sau này sử dụng
    context.user_data['user_id'] = query.from_user.id
    context.user_data['chat_id'] = query.message.chat_id

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Quay lại", callback_data='deposit')]
    ])

    await query.edit_message_text(
        text=sepay_info,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    # Chuyển sang trạng thái chờ người dùng nhập số tiền
    context.user_data['expect_amount'] = True
    return AMOUNT


async def show_deposit_history(query):
    """Hiển thị lịch sử giao dịch nạp tiền."""
    # Đây là nơi bạn sẽ lấy dữ liệu thực tế từ cơ sở dữ liệu
    history = "📊 **Lịch sử giao dịch nạp tiền**\n\n"
    history += "1. **15/04/2025** - 500,000 VND - Thành công\n"
    history += "2. **10/04/2025** - 200,000 VND - Thành công\n"
    history += "3. **05/04/2025** - 1,000,000 VND - Thành công\n\n"
    history += "Số dư hiện tại: **1,700,000 VND**"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Nạp thêm", callback_data='deposit')],
        [InlineKeyboardButton("⬅️ Quay lại menu chính", callback_data='back_to_main')]
    ])

    await query.edit_message_text(
        text=history,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def process_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xử lý số tiền người dùng nhập và tạo yêu cầu thanh toán SePay."""
    # Kiểm tra xem có phải đang chờ nhập số tiền không
    if not context.user_data.get('expect_amount', False):
        return ConversationHandler.END

    # Lấy số tiền từ tin nhắn người dùng
    text = update.message.text
    try:
        amount = int(text.replace(',', '').strip())
        if amount < 10000:
            await update.message.reply_text(
                "❌ Số tiền tối thiểu là 10,000 VND. Vui lòng nhập lại:"
            )
            return AMOUNT
    except ValueError:
        await update.message.reply_text(
            "❌ Vui lòng nhập một số hợp lệ (không chứa chữ cái hoặc ký tự đặc biệt):"
        )
        return AMOUNT

    # Lưu số tiền vào user_data
    context.user_data['amount'] = amount

    # Tạo yêu cầu thanh toán từ SePay API
    try:
        payment_data = create_sepay_payment(update.effective_user.id, amount)

        payment_url = payment_data.get('payment_url')
        transaction_id = payment_data.get('transaction_id')

        # Lưu transaction_id để theo dõi
        context.user_data['transaction_id'] = transaction_id

        # Tạo inline keyboard với URL thanh toán
        keyboard = [
            [InlineKeyboardButton("🔗 Thanh toán ngay", url=payment_url)],
            [InlineKeyboardButton("✅ Đã thanh toán", callback_data='payment_complete')],
            [InlineKeyboardButton("❌ Hủy", callback_data='deposit')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        confirmation_text = f"💰 **Yêu cầu nạp tiền đã được tạo**\n\n"
        confirmation_text += f"**Số tiền:** {amount:,} VND\n"
        confirmation_text += f"**Mã giao dịch:** {transaction_id}\n\n"
        confirmation_text += "Nhấn vào nút bên dưới để tiến hành thanh toán qua SePay.\n"
        confirmation_text += "Sau khi thanh toán xong, vui lòng nhấn 'Đã thanh toán'."

        await update.message.reply_text(
            text=confirmation_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        # Reset trạng thái chờ nhập số tiền
        context.user_data['expect_amount'] = False
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error creating SePay payment: {e}")
        await update.message.reply_text(
            "❌ Có lỗi xảy ra khi tạo giao dịch. Vui lòng thử lại sau hoặc liên hệ CSKH."
        )
        # Reset trạng thái chờ nhập số tiền
        context.user_data['expect_amount'] = False
        return ConversationHandler.END


def create_sepay_payment(user_id, amount):
    """Tạo yêu cầu thanh toán với SePay API và trả về thông tin thanh toán."""
    # Đây là nơi bạn sẽ gọi API thực tế của SePay
    try:
        # Tạo dữ liệu cho request
        payload = {
            "merchant_id": MERCHANT_ID,
            "api_key": SEPAY_API_KEY,
            "amount": amount,
            "order_id": f"ORDER-{user_id}-{int(time.time())}",
            "order_info": f"Nạp tiền vào tài khoản {user_id}",
            "return_url": "https://t.me/your_bot_username",  # Thay thế bằng username của bot bạn
            "notify_url": "https://your-server.com/sepay-callback"  # URL webhook để nhận thông báo từ SePay
        }

        # Thêm chữ ký (nếu cần)
        # payload["signature"] = create_signature(payload, SEPAY_SECRET_KEY)

        # Gửi request đến SePay API
        response = requests.post(f"{SEPAY_API_URL}/create-payment", json=payload)
        data = response.json()

        if data.get("status") == "success":
            return {
                "payment_url": data.get("payment_url"),
                "transaction_id": data.get("transaction_id")
            }
        else:
            raise Exception(f"SePay API error: {data.get('message')}")

    except Exception as e:
        logger.error(f"Error in create_sepay_payment: {e}")
        raise


async def handle_payment_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý khi người dùng nhấn nút Đã thanh toán."""
    query = update.callback_query
    await query.answer()

    transaction_id = context.user_data.get('transaction_id')

    if not transaction_id:
        await query.edit_message_text(
            "❌ Không tìm thấy thông tin giao dịch. Vui lòng thử lại hoặc liên hệ CSKH."
        )
        return

    # Kiểm tra trạng thái giao dịch với SePay API
    try:
        transaction_status = check_transaction_status(transaction_id)

        if transaction_status == "success":
            # Xử lý giao dịch thành công
            await query.edit_message_text(
                "✅ **Giao dịch thành công!**\n\n"
                f"Mã giao dịch: {transaction_id}\n"
                f"Số tiền: {context.user_data.get('amount', 0):,} VND\n\n"
                "Tài khoản của bạn đã được cộng tiền.\n"
                "Cảm ơn bạn đã sử dụng dịch vụ!",
                parse_mode='Markdown'
            )

            # Cập nhật số dư của người dùng trong cơ sở dữ liệu của bạn ở đây

        elif transaction_status == "pending":
            await query.edit_message_text(
                "⏳ **Giao dịch đang xử lý**\n\n"
                f"Mã giao dịch: {transaction_id}\n"
                "Vui lòng đợi trong giây lát hoặc kiểm tra lại sau.\n\n"
                "Nếu bạn đã thanh toán nhưng chưa nhận được tiền, vui lòng liên hệ CSKH.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Kiểm tra lại", callback_data='payment_complete')],
                    [InlineKeyboardButton("📞 Liên hệ CSKH", callback_data='support')]
                ]),
                parse_mode='Markdown'
            )

        else:  # failed or other status
            await query.edit_message_text(
                "❌ **Giao dịch thất bại hoặc bị hủy**\n\n"
                f"Mã giao dịch: {transaction_id}\n\n"
                "Vui lòng thử lại hoặc liên hệ CSKH để được hỗ trợ.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Thử lại", callback_data='deposit')],
                    [InlineKeyboardButton("📞 Liên hệ CSKH", callback_data='support')]
                ]),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error checking transaction status: {e}")
        await query.edit_message_text(
            "❌ Có lỗi xảy ra khi kiểm tra giao dịch. Vui lòng thử lại sau hoặc liên hệ CSKH.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 Liên hệ CSKH", callback_data='support')]
            ])
        )


def check_transaction_status(transaction_id):
    """Kiểm tra trạng thái giao dịch với SePay API."""
    try:
        # Tạo dữ liệu cho request
        payload = {
            "merchant_id": MERCHANT_ID,
            "api_key": SEPAY_API_KEY,
            "transaction_id": transaction_id
        }

        # Thêm chữ ký (nếu cần)
        # payload["signature"] = create_signature(payload, SEPAY_SECRET_KEY)

        # Gửi request đến SePay API
        response = requests.post(f"{SEPAY_API_URL}/check-transaction", json=payload)
        data = response.json()

        if data.get("status") == "success":
            return data.get("transaction_status", "unknown")
        else:
            logger.error(f"SePay API error: {data.get('message')}")
            return "error"

    except Exception as e:
        logger.error(f"Error in check_transaction_status: {e}")
        return "error"


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hủy và kết thúc cuộc trò chuyện."""
    context.user_data.clear()
    await update.message.reply_text("Đã hủy thao tác.")
    return ConversationHandler.END


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý tin nhắn thông thường."""
    # Kiểm tra xem có đang trong quá trình nhập số tiền không
    if context.user_data.get('expect_amount', False):
        await process_amount(update, context)
    else:
        # Phản hồi với menu chính cho mọi tin nhắn khác
        await start(update, context)


def setup_webhook(app, url, token):
    """Thiết lập webhook thay vì polling (sử dụng khi triển khai trên server)."""
    webhook_url = f"{url}/webhook/{token}"
    app.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to {webhook_url}")


def main() -> None:
    """Khởi chạy bot."""
    # Tạo ứng dụng
    application = Application.builder().token(TOKEN).build()

    # Thêm conversation handler cho việc nhập số tiền
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_sepay_deposit, pattern='^deposit_sepay$')],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Thêm các handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Kiểm tra môi trường và chọn cách chạy phù hợp
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    if WEBHOOK_URL:
        # Sử dụng webhook (cho môi trường production)
        PORT = int(os.environ.get("PORT", 8443))
        setup_webhook(application, WEBHOOK_URL, TOKEN)
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook/{TOKEN}"
        )
    else:
        # Sử dụng polling (cho môi trường phát triển)
        application.run_polling()


def main() -> None:
    """Khởi chạy bot."""
    # Tạo ứng dụng
    application = Application.builder().token(TOKEN).build()

    # Thêm conversation handler cho việc nhập số tiền
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_sepay_deposit, pattern='^deposit_sepay$')],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Thêm conversation handler cho kiểm tra tài khoản 8KBET
    account_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(input_8kbet_accounts, pattern='^input_8kbet_accounts$')],
        states={
            WAITING_8KBET_ACCOUNTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_8kbet_accounts)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Thêm các handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(account_conv_handler)  # Thêm handler cho 8KBET
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Kiểm tra môi trường và chọn cách chạy phù hợp
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    if WEBHOOK_URL:
        # Sử dụng webhook (cho môi trường production)
        PORT = int(os.environ.get("PORT", 8443))
        setup_webhook(application, WEBHOOK_URL, TOKEN)
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook/{TOKEN}"
        )
    else:
        # Sử dụng polling (cho môi trường phát triển)
        application.run_polling()


if __name__ == '__main__':
    main()