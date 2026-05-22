# =============================================
# LANGKAH 1: Import library yang dibutuhkan
# =============================================
from enum import Enum, auto
from engine import ChatbotEngine as NLPEngine


# =============================================
# LANGKAH 2: Buat class State sebagai Enum
# untuk mendefinisikan state-state FSM chatbot
# =============================================
class State(Enum):
    IDLE         = auto()
    ORDERING     = auto()
    CONFIRMATION = auto()
    PAYMENT      = auto()


# =============================================
# LANGKAH 3: Buat class CoffeeFSM sebagai
# object utama chatbot, beserta __init__
# =============================================
class CoffeeFSM:
    def __init__(self):
        self.state    = State.IDLE
        self.nlp      = NLPEngine()
        self.cart     = []
        self.response = ""

    # =============================================
    # LANGKAH 4: Method get_response & calculate_total
    # =============================================
    def get_response(self):
        return self.response

    def calculate_total(self):
        return sum(item['price'] * item['qty'] for item in self.cart)

    # =============================================
    # LANGKAH 5: Method get_menu_text
    # Merangkai teks daftar menu dari menu_data
    # =============================================
    def get_menu_text(self):
        """Fungsi bantuan untuk merangkai teks daftar menu"""
        teks_menu = "**☕ Daftar Menu Logic Coffee:**\n\n"
        for key, data in self.nlp.menu_data.items():
            teks_menu += (
                f"- {data['emoji']} **{key.capitalize()}**"
                f" (Rp {data['price']:,}): *{data['desc']}*\n"
            )
        teks_menu += "\nSilakan ketik pesanan Anda (contoh: *'Pesan 2 teh, 1 espresso'*)."
        return teks_menu

    # =============================================
    # LANGKAH 6: Method reduce_cart
    # Mengurangi atau menghapus item dari keranjang
    # =============================================
    def reduce_cart(self, item_to_reduce, qty_to_remove):
        """Logika untuk mengurangi qty item atau menghapusnya jika qty <= 0"""
        found   = False
        message = ""

        # Cari item di cart
        for item in self.cart:
            if item['item'] == item_to_reduce:
                item['qty'] -= qty_to_remove
                found = True
                if item['qty'] <= 0:
                    self.cart.remove(item)
                    message = f"❌ **{item_to_reduce}** telah dihapus dari keranjang."
                else:
                    message = (
                        f"📝 **{item_to_reduce}** dikurangi {qty_to_remove}. "
                        f"Sisa: {item['qty']}."
                    )
                break

        if not found:
            message = f"Gagal: **{item_to_reduce}** tidak ditemukan di keranjang Anda."
        return message

    # =============================================
    # LANGKAH 7: Method step (FSM utama)
    # Mengelola semua transisi state & fitur chatbot
    # =============================================
    def step(self, user_input=""):
        user_input = user_input.strip()
        intent     = self.nlp.detect_intent(user_input)

        # ------------------------------------------
        # GLOBAL RESET SYSTEM (berlaku di semua state)
        # ------------------------------------------
        if intent == "RESET":
            self.__init__()
            self.response = "Sistem di-reset total. Halo! Mau pesan apa?"
            return

        # ------------------------------------------
        # STATE LOGIC: IDLE
        # ------------------------------------------
        if self.state == State.IDLE:
            self.state    = State.ORDERING
            self.response = "Halo! Mau pesan apa hari ini? Ketik 'menu' untuk melihat pilihan."

        # ------------------------------------------
        # STATE LOGIC: ORDERING
        # ------------------------------------------
        elif self.state == State.ORDERING:

            # FITUR: Tanya Menu
            if intent == "ASK_MENU":
                self.response = self.get_menu_text()

            # FITUR: Batalkan Semua
            elif intent == "CANCEL_ALL":
                self.cart     = []
                self.response = "Keranjang telah dikosongkan. Mau pesan yang lain?"

            # FITUR: Kurangi/Batalkan Item Tertentu
            elif intent == "REDUCE_ITEM":
                items_to_remove = self.nlp.parse_orders(user_input)
                if items_to_remove:
                    results = []
                    for itm in items_to_remove:
                        res = self.reduce_cart(itm['item'], itm['qty'])
                        results.append(res)
                    self.response = "\n".join(results)
                else:
                    self.response = (
                        "Item apa yang ingin dibatalkan? "
                        "Contoh: *'batalkan 1 kopi'*."
                    )

            # FITUR: Checkout Keranjang
            elif intent == "CHECKOUT":
                if not self.cart:
                    self.response = "Keranjang masih kosong."
                else:
                    self.state    = State.CONFIRMATION
                    self.response = (
                        f"Total: **Rp {self.calculate_total():,}**. "
                        f"Lanjut bayar? (Ya/Tidak)"
                    )

            # FITUR: Logika Penambahan Pesanan (default)
            else:
                new_orders = self.nlp.parse_orders(user_input)
                if new_orders:
                    for order in new_orders:
                        # Cek jika item sudah ada, tambah qty saja
                        existing = next(
                            (i for i in self.cart if i['item'] == order['item']),
                            None
                        )
                        if existing:
                            existing['qty'] += order['qty']
                        else:
                            # Ambil info harga & emoji dari menu_data
                            menu_info = self.nlp.menu_data[order['item']]
                            order.update({
                                "price": menu_info['price'],
                                "emoji": menu_info['emoji']
                            })
                            self.cart.append(order)
                    self.response = (
                        "✅ Pesanan ditambahkan. "
                        "Ada lagi? (Ketik 'bayar' untuk selesai)"
                    )
                else:
                    self.response = (
                        "Maaf, saya tidak mengerti. "
                        "Coba: *'pesan 2 kopi'* atau *'hapus 1 kopi'*."
                    )

        # ------------------------------------------
        # STATE LOGIC: CONFIRMATION
        # ------------------------------------------
        elif self.state == State.CONFIRMATION:
            intent = self.nlp.detect_intent(user_input)

            if intent == "YES":
                self.state = State.PAYMENT
                self.step()   # Auto-step ke PAYMENT

            elif intent == "NO":
                self.state    = State.ORDERING
                self.response = "Oke, silakan tambah pesanan lagi."

            else:
                self.response = "Jawab 'Ya' atau 'Tidak'."

        # ------------------------------------------
        # STATE LOGIC: PAYMENT
        # ------------------------------------------
        elif self.state == State.PAYMENT:
            total         = self.calculate_total()
            self.response = (
                f"🎉 Terima kasih! Pembayaran Rp {total:,} diterima. "
                f"Pesanan diproses."
            )
            self.state = State.IDLE


# =============================================
# MAIN: Jalankan chatbot di terminal
# =============================================
if __name__ == "__main__":
    print("=" * 55)
    print("   CHATBOT KAFE FSA - Logic Coffee")
    print("   Teori Bahasa dan Otomata")
    print("=" * 55)
    print("Ketik 'quit' atau 'exit' untuk keluar.\n")

    bot = CoffeeFSM()

    # Trigger pertama (IDLE -> ORDERING)
    bot.step()
    print(f"Bot: {bot.get_response()}\n")

    while True:
        user_input = input("Kamu: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["quit", "exit"]:
            print("Bot: Sampai jumpa! Terima kasih sudah mampir.")
            break

        bot.step(user_input)
        print(f"Bot: {bot.get_response()}\n")