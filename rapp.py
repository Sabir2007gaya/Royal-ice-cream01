import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import bcrypt

# DB Setup (use your secrets)
@st.cache_resource
def get_db():
    client = MongoClient(st.secrets["mongodb"]["uri"])
    db = client[st.secrets["mongodb"]["database"]]
    return db
db = get_db()

HELPLINE = "+91-9204441036"

def main():
    st.markdown("""
    <style>
        .stButton > button {background-color: #2266AA; color:white; font-weight:600;}
        .stTitle {color: #A60056;}
        .product-card {margin: 10px 0; padding: 12px; border: 1px solid #ececec; border-radius: 7px; box-shadow:2px 2px 18px #f3f3f3;}
    </style>
    """, unsafe_allow_html=True)
    st.title("Welcome to Royal Ice Cream")
    st.image("https://5.imimg.com/data5/SELLER/Default/2022/4/GA/IB/YJ/62705623/amul-ice-cream-tenkasi.jpg",
          caption="Royal Ice Cream", use_column_width=True)
    st.write(f"📞 Helpline: {HELPLINE}")
    page = st.selectbox("Choose an option:", ["User", "Admin", "Terms & Conditions"], key="page_selector")
    if page == "Terms & Conditions":
        terms_and_conditions()
    elif page == "Admin":
        admin_login()
    elif page == "User":
        user_login()

def terms_and_conditions():
    st.header("Terms and Conditions")
    st.write("Add your detailed terms & conditions here.")
    if st.button("Back", key="terms_back"):
        st.session_state.page = None

def send_otp(username, mode):
    st.info(f"OTP sent to {username} ({mode}) [simulation].")

def admin_login():
    st.header("Admin Login")
    mode = st.radio("Login via:", ["User Name", "Email"], key="admin_login_mode")
    username = st.text_input("User Name (Admin)", key="admin_login_username")
    password = st.text_input("Password", type="password", key="admin_login_password")
    if st.button("Login", key="admin_login_btn"):
        st.session_state["admin_logged_in"] = True
    if st.session_state.get("admin_logged_in"):
        admin_dashboard()

def admin_dashboard():
    st.header("Admin Dashboard")
    st.subheader("Register New User")
    first_name = st.text_input("First Name (Admin)", key="admin_add_first")
    last_name = st.text_input("Last Name (Admin)", key="admin_add_last")
    age = st.number_input("Age (Admin)", min_value=1, max_value=120, key="admin_add_age")
    username = st.text_input("User Name (Admin)", key="admin_add_username")
    user_password = st.text_input("Set Password", type="password", key="admin_set_pw")
    if st.button("Create User", key="admin_user_create_btn"):
        pw_hash = bcrypt.hashpw(user_password.encode(), bcrypt.gensalt())
        db.users.insert_one({
            "first_name": first_name,
            "last_name": last_name,
            "age": age,
            "username": username,
            "password": pw_hash,
            "created_by": "admin"
        })
        st.success("User created!")
    # Product management
    st.subheader("Manage Products")
    prod_name = st.text_input("Product Name", key="prod_add_name")
    price = st.number_input("Price (₹)", min_value=1, key="prod_add_price")
    qty = st.number_input("Total Qty", min_value=1, key="prod_add_qty")
    if st.button("Add Product", key="prod_add_btn"):
        db.products.insert_one({
            "name": prod_name,
            "price": price,
            "total_qty": qty,
            "remaining_qty": qty,
            "daily_sale": 0,
            "likes": 0,
            "added_on": datetime.now()
        })
        st.success("Product added!")
    remove_prod = st.text_input("Product name to remove", key="prod_remove_name")
    if st.button("Remove Product", key="prod_remove_btn"):
        db.products.delete_one({"name": remove_prod})
        st.warning("Product removed!")
    # Analytics
    st.subheader("Product Analytics")
    products = list(db.products.find())
    if products:
        fav_sell = max(products, key=lambda x: x.get("daily_sale", 0))
        fav_like = max(products, key=lambda x: x.get("likes", 0))
        st.markdown(
            f"**Most Sold:** {fav_sell['name']} ({fav_sell['daily_sale']} sold) :star:<br>" +
            f"**Most Liked:** {fav_like['name']} ({fav_like['likes']} likes) :heart:",
            unsafe_allow_html=True)
        for i, p in enumerate(products):
            st.markdown(
                f"<div class='product-card'><span style='font-size:18px;'>{p['name']}</span> | "
                f"Price: <span style='color:red;'>₹{p['price']}</span> | Remaining: {p['remaining_qty']} | Daily Sale: {p['daily_sale']}</div>",
                unsafe_allow_html=True)
            if p["daily_sale"] == 0:
                st.info(f"📉 Suggest Discount on {p['name']}", icon="🔔")
    else:
        st.info("No products found.")

def user_login():
    st.header("User Registration/Login")
    mode = st.radio("Login/Register via:", ["User Name", "Email"], key="user_login_mode")
    username = st.text_input("User Name (User)", key="user_login_username")
    password = st.text_input("Password", type="password", key="user_login_pw")
    if st.button("Send OTP", key="user_login_otp_btn"):
        send_otp(username, mode)
        # Check if user exists
        user = db.users.find_one({"username": username})
        if not user:
            st.session_state["user_register_mode"] = True
            st.session_state["user_username_for_reg"] = username
        else:
            if bcrypt.checkpw(password.encode(), user["password"]):
                st.success("Logged in successfully!")
                st.session_state["user_logged_in"] = True
                st.session_state["user_username"] = username
            else:
                st.error("Wrong password!")
    if st.session_state.get("user_register_mode"):
        register_user(st.session_state["user_username_for_reg"])
    if st.session_state.get("user_logged_in"):
        user_dashboard(st.session_state["user_username"])

def register_user(username):
    st.subheader("Register")
    first_name = st.text_input("First Name", key="user_register_first")
    last_name = st.text_input("Last Name", key="user_register_last")
    age = st.number_input("Age", min_value=1, max_value=120, key="user_register_age")
    location = st.text_input("Location", key="user_register_loc")
    password = st.text_input("Set Password", type="password", key="user_register_pw")
    if st.button("Register", key="user_register_btn"):
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        db.users.insert_one({
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "age": age,
            "location": location,
            "password": pw_hash
        })
        st.success("Registered!")
        st.session_state["user_logged_in"] = True
        st.session_state["user_username"] = username
        st.session_state["user_register_mode"] = False

def user_dashboard(username):
    st.subheader("Your Details")
    user = db.users.find_one({"username": username})
    st.write(user)
    st.subheader("Products")
    products = list(db.products.find())
    cart = st.session_state.get("cart", [])
    wish = st.session_state.get("wish", [])
    for idx, p in enumerate(products):
        st.markdown(f"""
        <div class="product-card">
          <span style="font-size:18px;font-weight:600">{p['name']}</span> <br>
          <span style="color:#ea2020">₹{p['price']}</span>
          <span> | Remaining: <b>{p['remaining_qty']}</b></span>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Add {p['name']} to Cart", key=f"cart_add_{idx}_userdashboard"):
            cart.append(p["name"])
            st.session_state.cart = cart
            st.success(f"{p['name']} added to Cart!")
        if st.button(f"Add {p['name']} to Wishlist", key=f"wish_add_{idx}_userdashboard"):
            wish.append(p["name"])
            st.session_state.wish = wish
            st.success(f"{p['name']} added to Wishlist!")
        rating = st.slider(f"Rate {p['name']}", 1, 5, 3, key=f"rate_{idx}_userdashboard")
        feedback = st.text_input(f"Feedback for {p['name']}", key=f"fb_{idx}_userdashboard")
        if st.button(f"Submit Feedback for {p['name']}", key=f"fb_submit_{idx}_userdashboard"):
            db.feedback.insert_one({
                "user": username,
                "product": p["name"],
                "rating": rating,
                "text": feedback,
                "date": datetime.now()
            })
            db.products.update_one({"name": p["name"]}, {"$inc": {"likes": 1}})
            st.success("Feedback submitted.")
        if p["daily_sale"] == 0:
            st.info(f"Discount available on {p['name']}!")
    st.subheader("Cart")
    st.write(st.session_state.get("cart", []))
    st.subheader("Wishlist")
    st.write(st.session_state.get("wish", []))
    if st.button("Place Order", key="order_place_btn"):
        order_id = db.orders.insert_one({
            "user": username,
            "cart": st.session_state.get("cart", []),
            "timestamp": datetime.now(),
            "payment": "Pending"
        }).inserted_id
        st.success("Order placed successfully!")
        total = sum([db.products.find_one({'name': i})['price'] for i in st.session_state.get("cart", [])])
        st.write("---")
        st.write(f"Invoice ID: {order_id}")
        st.markdown(f"Total Amount: <span style='font-size:22px;color:green;'>₹{total}</span>", unsafe_allow_html=True)
        st.write("Payment method: (Online/Offline)")
        st.write("Thanks for choosing Royal Ice Cream and visit again!")

if __name__ == "__main__":
    main()
