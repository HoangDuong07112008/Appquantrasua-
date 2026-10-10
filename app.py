import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

# =========================================================
# 1. CẤU HÌNH ỨNG DỤNG
# =========================================================
st.set_page_config(
    page_title="Milk Tea POS - Quản lý bán hàng",
    page_icon="🧋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Bảng giá mẫu (VNĐ)
DRINKS = {
    "Trà sữa truyền thống": 30000,
    "Trà sữa trân châu đường đen": 35000,
    "Trà sữa matcha": 35000,
    "Trà sữa khoai môn": 35000,
    "Trà sữa socola": 35000,
    "Trà sữa ô long": 32000,
    "Trà sữa thái xanh": 30000,
    "Trà sữa thái đỏ": 30000,
    "Trà đào cam sả": 30000,
    "Trà vải": 30000,
    "Trà chanh": 20000,
    "Trà dâu": 28000,
    "Matcha latte": 35000,
    "Sữa tươi trân châu đường đen": 35000,
    "Cà phê sữa": 25000,
    "Nước ép cam": 30000,
}

SIZES = {
    "S": 0,
    "M": 5000,
    "L": 10000,
}

TOPPINGS = {
    "Trân châu đen": 5000,
    "Trân châu trắng": 5000,
    "Trân châu hoàng kim": 7000,
    "Pudding trứng": 7000,
    "Thạch trái cây": 5000,
    "Thạch phô mai": 7000,
    "Flan": 7000,
    "Kem cheese": 10000,
    "Không topping": 0,
}

# =========================================================
# 2. KHỞI TẠO SESSION STATE
# =========================================================
if "cart" not in st.session_state:
    st.session_state.cart = []
if "invoice" not in st.session_state:
    st.session_state.invoice = None
if "order_counter" not in st.session_state:
    st.session_state.order_counter = 1
if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""
if "payment_method" not in st.session_state:
    st.session_state.payment_method = "Tiền mặt"
if "discount" not in st.session_state:
    st.session_state.discount = 0
if "service_fee" not in st.session_state:
    st.session_state.service_fee = 0

# =========================================================
# 3. HÀM HỖ TRỢ
# =========================================================
def money(value):
    """Định dạng số tiền theo VNĐ."""
    return f"{int(value):,}".replace(",", ".") + " đ"

def reset_order():
    """Xóa đơn hiện tại để tạo đơn mới."""
    st.session_state.cart = []
    st.session_state.invoice = None
    st.session_state.customer_name = ""
    st.session_state.payment_method = "Tiền mặt"
    st.session_state.discount = 0
    st.session_state.service_fee = 0

def calculate_item_price(item):
    """Tính giá một ly, bao gồm size và topping."""
    return item["base_price"] + item["size_price"] + item["topping_price"]

def calculate_totals(cart, discount_percent, service_percent):
    subtotal = sum(calculate_item_price(item) * item["quantity"] for item in cart)
    discount_amount = int(subtotal * discount_percent / 100)
    after_discount = subtotal - discount_amount
    service_amount = int(after_discount * service_percent / 100)
    total = after_discount + service_amount
    return subtotal, discount_amount, service_amount, total

def create_invoice_text(invoice):
    """Tạo nội dung hóa đơn dạng văn bản."""
    lines = [
        "=" * 42,
        "          HOA DON QUAN TRA SUA",
        "=" * 42,
        f"Ma hoa don: {invoice['order_id']}",
        f"Thoi gian:  {invoice['datetime']}",
        f"Khach hang: {invoice['customer']}",
        f"Thanh toan: {invoice['payment']}",
        "-" * 42,
        "CHI TIET DON HANG",
        "-" * 42,
    ]
    for index, item in enumerate(invoice["items"], start=1):
        lines.append(f"{index}. {item['drink']} - Size {item['size']}")
        lines.append(f"   Duong: {item['sugar']} | Da: {item['ice']}")
        lines.append(f"   Topping: {', '.join(item['toppings'])}")
        lines.append(f"   SL: {item['quantity']} x {money(calculate_item_price(item))}")
        lines.append(f"   Thanh tien: {money(calculate_item_price(item) * item['quantity'])}")
    
    lines.extend([
        "-" * 42,
        f"Tam tinh:    {money(invoice['subtotal'])}",
        f"Giam gia:   -{money(invoice['discount_amount'])} ({invoice['discount_percent']}%)",
        f"Phi dich vu: {money(invoice['service_amount'])} ({invoice['service_percent']}%)",
        "=" * 42,
        f"TONG THANH TOAN: {money(invoice['total'])}",
        "=" * 42,
        "Camon quy khach! Hen gap lai!",
    ])
    return "\n".join(lines)

def invoice_to_csv(invoice):
    """Xuất chi tiết hóa đơn thành CSV."""
    rows = []
    for item in invoice["items"]:
        rows.append({
            "Ma hoa don": invoice["order_id"],
            "Thoi gian": invoice["datetime"],
            "Khach hang": invoice["customer"],
            "Ten mon": item["drink"],
            "Size": item["size"],
            "Topping": ", ".join(item["toppings"]),
            "Duong": item["sugar"],
            "Da": item["ice"],
            "Don gia": calculate_item_price(item),
            "So luong": item["quantity"],
            "Thanh tien": calculate_item_price(item) * item["quantity"],
            "Phuong thuc thanh toan": invoice["payment"],
            "Tong hoa don": invoice["total"],
        })
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8-sig")

# =========================================================
# 4. GIAO DIỆN CHÍNH
# =========================================================
st.markdown(
    """
    <div style="background: linear-gradient(120deg, #542788, #9b59b6); padding: 25px; border-radius: 18px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin: 0; color: white;">🧋 MILK TEA POS</h1>
        <p style="font-size: 16px; margin-bottom: 0;">Hệ thống gọi món, tính tiền và xuất hóa đơn trà sữa</p>
    </div>
    """, 
    unsafe_allow_html=True
)

with st.sidebar:
    st.title("⚙️ Quản lý bán hàng")
    st.caption("Milk Tea POS")
    st.markdown("---")
    st.markdown("### 📋 Chức năng")
    st.write("🧋 Thêm món và topping")
    st.write("🛒 Quản lý giỏ hàng")
    st.write("💵 Tính tiền tự động")
    st.write("🧾 Xuất hóa đơn")
    st.markdown("---")
    st.caption("Giá bán được thiết lập theo menu mẫu.")

# =========================================================
# 5. THÔNG TIN KHÁCH HÀNG
# =========================================================
st.subheader("👤 Thông tin khách hàng")
customer_col1, customer_col2 = st.columns(2)
with customer_col1:
    st.text_input(
        "Tên khách hàng", 
        key="customer_name", 
        placeholder="Nhập tên khách hàng..."
    )
with customer_col2:
    st.selectbox(
        "Phương thức thanh toán", 
        ["Tiền mặt", "Chuyển khoản", "Thẻ ngân hàng", "Ví điện tử"], 
        key="payment_method"
    )
st.divider()

# =========================================================
# 6. THÊM MÓN VÀO ĐƠN HÀNG
# =========================================================
st.subheader("🥤 Chọn đồ uống")
with st.container(border=True):
    with st.form("add_drink_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            drink = st.selectbox("Loại đồ uống", list(DRINKS.keys()))
            size = st.selectbox(
                "Kích thước", 
                list(SIZES.keys()), 
                index=1, 
                format_func=lambda x: f"Size {x} (+{money(SIZES[x])})" if SIZES[x] > 0 else f"Size {x} (giá gốc)"
            )
            sugar = st.select_slider("Mức độ đường", options=["0%", "30%", "50%", "70%", "100%"], value="50%")
            
        with col2:
            toppings_selected = st.multiselect(
                "Chọn topping", 
                options=[x for x in TOPPINGS if x != "Không topping"], 
                placeholder="Chọn một hoặc nhiều topping..."
            )
            ice = st.select_slider("Mức độ đá", options=["Không đá", "Ít đá", "Bình thường", "Nhiều đá"], value="Bình thường")
            quantity = st.number_input("Số lượng ly", min_value=1, max_value=100, value=1, step=1)
            
        topping_price = sum(TOPPINGS[t] for t in toppings_selected)
        toppings_display = toppings_selected if toppings_selected else ["Không topping"]
        size_price = SIZES[size]
        unit_price = DRINKS[drink] + size_price + topping_price
        
        st.info(f"**Giá một ly:** {money(unit_price)} | **Thành tiền:** {money(unit_price * quantity)}")
        
        add_button = st.form_submit_button("➕ THÊM MÓN VÀO HÓA ĐƠN", type="primary", use_container_width=True)
        
        if add_button:
            item = {
                "id": str(uuid.uuid4()),
                "drink": drink,
                "base_price": DRINKS[drink],
                "size": size,
                "size_price": size_price,
                "toppings": toppings_display,
                "topping_price": topping_price,
                "sugar": sugar,
                "ice": ice,
                "quantity": int(quantity),
            }
            st.session_state.cart.append(item)
            st.session_state.invoice = None
            st.toast(f"Đã thêm thành công {quantity} ly {drink}!", icon="✅")
            st.rerun()

st.divider()

# =========================================================
# 7. GIỎ HÀNG
# =========================================================
st.subheader("🛒 Giỏ hàng")
if not st.session_state.cart:
    st.info("Chưa có món nào. Hãy chọn đồ uống và nhấn 'Thêm món vào hóa đơn'.")
else:
    for index, item in enumerate(st.session_state.cart):
        with st.container(border=True):
            left, middle, right = st.columns([3, 2, 1])
            with left:
                st.markdown(f"**{index + 1}. {item['drink']}**")
                st.caption(f"Size {item['size']} | Đường {item['sugar']} | Đá {item['ice']}")
                st.caption("Topping: " + ", ".join(item["toppings"]))
                st.write(f"Đơn giá: {money(calculate_item_price(item))}")
            with middle:
                # Hàm callback để cập nhật ngay lập tức khi đổi số lượng
