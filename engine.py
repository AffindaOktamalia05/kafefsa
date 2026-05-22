import re

class ChatbotEngine:
    def __init__(self):
        # =============================================
        # LANGKAH 1: Inisialisasi Atribut Objek
        # Database Menu dengan Info Tambahan untuk UI
        # =============================================
        self.menu_data = {
            "kopi":     {"price": 15000, "emoji": "☕", "desc": "Kopi hitam klasik"},
            "latte":    {"price": 20000, "emoji": "🥛", "desc": "Espresso dengan susu steamed"},
            "teh":      {"price": 10000, "emoji": "🍵", "desc": "Teh melati hangat"},
            "espresso": {"price": 18000, "emoji": "⚡", "desc": "Shot kopi murni pekat"}
        }

        # Regex Patterns
        self.re_number = r"\b(\d+)\b"

        # Membuat pola regex dinamis dari keys menu
        menu_keys = "|".join(self.menu_data.keys())
        self.re_menu = rf"\b({menu_keys})\b"

        # Pemisah kalimat (koma, titik, 'dan', '&')
        self.re_split = r"[,.]|\bdan\b|\b&\b"

        # Regex untuk pembatalan/pengurangan
        self.re_cancel_all = r"\b(batalkan semua|hapus semua|reset keranjang|kosongkan)\b"
        self.re_reduce     = r"\b(batalkan|kurangi|tidak jadi|hapus|cancel)\b"

        # State FSA & keranjang belanja
        self.state   = "START"
        self.cart    = {}   # {"kopi": {"qty": 2, "price": 15000, "emoji": "☕"}}
        self.pending = []   # order yang menunggu konfirmasi

    # =============================================
    # LANGKAH 2: Method _parse_single_segment
    # Helper untuk memproses SATU potongan kalimat
    # Contoh input: "2 teh"
    # =============================================
    def _parse_single_segment(self, text):
        """Helper untuk memproses satu potongan kalimat (misal: '2 teh')"""
        text = text.lower().strip()

        # 1. Cari Item
        item_match = re.search(self.re_menu, text)
        if not item_match:
            return None

        item_key = item_match.group(1)

        # 2. Cari Jumlah (Default 1)
        qty_match = re.search(self.re_number, text)
        qty = int(qty_match.group(1)) if qty_match else 1

        return {
            "item":  item_key,
            "qty":   qty,
            "price": self.menu_data[item_key]["price"],
            "emoji": self.menu_data[item_key]["emoji"]
        }

    # =============================================
    # LANGKAH 3: Method parse_orders
    # Memecah kalimat majemuk menjadi list orders
    # Contoh: "pesan teh 2, espresso 2"
    # =============================================
    def parse_orders(self, full_text):
        """
        Memecah kalimat majemuk: "pesan teh 2, espresso 2"
        Menjadi list orders.
        """
        segments     = re.split(self.re_split, full_text)
        found_orders = []

        for segment in segments:
            if segment.strip():
                order = self._parse_single_segment(segment)
                if order:
                    found_orders.append(order)

        return found_orders

    # =============================================
    # LANGKAH 4: Method detect_intent
    # Mendeteksi maksud pengguna dari teks input
    # Inilah kondisi percabangan awal FSA chatbot
    # =============================================
    def detect_intent(self, text):
        text = text.lower()

        if re.search(r"\b(reset|ulang|batal semua)\b", text):
            return "RESET"
        if re.search(self.re_cancel_all, text):
            return "CANCEL_ALL"
        if re.search(self.re_reduce, text):
            return "REDUCE_ITEM"
        if re.search(r"(menu|daftar|apa saja|jual apa|list)", text):
            return "ASK_MENU"
        if re.search(r"\b(selesai|bayar|checkout|cukup)\b", text):
            return "CHECKOUT"
        if re.search(r"\b(ya|yes|oke|betul|siap|baik)\b", text):
            return "YES"
        if re.search(r"\b(tidak|enggak|batal|no|salah)\b", text):
            return "NO"

        return "UNKNOWN"

    # =============================================
    # LANGKAH 5: Method print_menu
    # Menampilkan daftar menu yang tersedia
    # =============================================
    def print_menu(self):
        print(self.menu_data)

    # =============================================
    # LANGKAH 6: Method get_cart_summary
    # Menghasilkan ringkasan isi keranjang belanja
    # =============================================
    def get_cart_summary(self):
        if not self.cart:
            return "Keranjang kamu masih kosong."

        lines = ["Isi keranjang kamu:"]
        total = 0
        for item, detail in self.cart.items():
            subtotal = detail["qty"] * detail["price"]
            total   += subtotal
            lines.append(
                f"  {detail['emoji']} {item.capitalize()} x{detail['qty']} "
                f"= Rp{subtotal:,}"
            )
        lines.append(f"Total: Rp{total:,}")
        return "\n".join(lines)

    # =============================================
    # LANGKAH 7: Method process_input (FSA utama)
    # Mesin utama yang mengelola transisi state
    # =============================================
    def process_input(self, user_input):
        intent = self.detect_intent(user_input)
        orders = self.parse_orders(user_input)

        # --- State: START ---
        if self.state == "START":
            if intent == "ASK_MENU":
                self.state = "BROWSING"
                menu_list = "\n".join(
                    [f"  {v['emoji']} {k.capitalize()} - Rp{v['price']:,} ({v['desc']})"
                     for k, v in self.menu_data.items()]
                )
                return f"Halo! Selamat datang. Berikut menu kami:\n{menu_list}\n\nMau pesan apa?"

            if orders:
                self.pending = orders
                self.state   = "CONFIRM_ORDER"
                preview = ", ".join(
                    [f"{o['emoji']} {o['item'].capitalize()} x{o['qty']}" for o in orders]
                )
                return f"Kamu mau pesan: {preview}. Betul ya? (ya/tidak)"

            return ("Halo! Selamat datang di Kafe FSA. "
                    "Ketik 'menu' untuk lihat daftar minuman, atau langsung pesan ya!")

        # --- State: BROWSING ---
        if self.state == "BROWSING":
            if orders:
                self.pending = orders
                self.state   = "CONFIRM_ORDER"
                preview = ", ".join(
                    [f"{o['emoji']} {o['item'].capitalize()} x{o['qty']}" for o in orders]
                )
                return f"Oke, kamu mau pesan: {preview}. Betul ya? (ya/tidak)"

            return "Silakan sebutkan minuman yang ingin dipesan."

        # --- State: CONFIRM_ORDER ---
        if self.state == "CONFIRM_ORDER":
            if intent == "YES":
                for o in self.pending:
                    key = o["item"]
                    if key in self.cart:
                        self.cart[key]["qty"] += o["qty"]
                    else:
                        self.cart[key] = {
                            "qty":   o["qty"],
                            "price": o["price"],
                            "emoji": o["emoji"]
                        }
                self.pending = []
                self.state   = "ORDERING"
                return (f"Pesanan ditambahkan!\n{self.get_cart_summary()}\n\n"
                        "Mau tambah pesanan lain? Atau ketik 'bayar' untuk checkout.")

            if intent == "NO":
                self.pending = []
                self.state   = "BROWSING"
                return "Oke, pesanan dibatalkan. Mau pesan yang lain?"

        # --- State: ORDERING ---
        if self.state == "ORDERING":
            if intent == "CHECKOUT":
                summary    = self.get_cart_summary()
                self.cart  = {}
                self.state = "START"
                return (f"Terima kasih sudah memesan!\n{summary}\n\n"
                        "Pembayaran berhasil. Sampai jumpa lagi!")

            if intent == "CANCEL_ALL":
                self.cart  = {}
                self.state = "START"
                return "Semua pesanan dibatalkan. Keranjang kosong."

            if intent == "RESET":
                self.cart  = {}
                self.state = "START"
                return "Keranjang direset. Mulai dari awal ya!"

            if orders:
                self.pending = orders
                self.state   = "CONFIRM_ORDER"
                preview = ", ".join(
                    [f"{o['emoji']} {o['item'].capitalize()} x{o['qty']}" for o in orders]
                )
                return f"Tambah pesanan: {preview}. Betul ya? (ya/tidak)"

            return (f"{self.get_cart_summary()}\n\n"
                    "Ketik nama minuman untuk tambah pesanan, atau 'bayar' untuk checkout.")

        return "Maaf, aku tidak mengerti. Coba ulangi ya."


# =============================================
# MAIN: Jalankan chatbot di terminal
# =============================================
if __name__ == "__main__":
    print("=" * 50)
    print("   CHATBOT KAFE FSA - Teori Bahasa & Otomata")
    print("=" * 50)
    print("Ketik 'quit' atau 'exit' untuk keluar.\n")

    bot = ChatbotEngine()
    # Sambutan awal
    print(f"Bot: {bot.process_input('halo')}\n")

    while True:
        user_input = input("Kamu: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["quit", "exit"]:
            print("Bot: Sampai jumpa! Terima kasih.")
            break

        response = bot.process_input(user_input)
        print(f"Bot: {response}\n")