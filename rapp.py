import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import bcrypt

# Database setup
@st.cache_resource
def get_db():
    client = MongoClient(st.secrets["mongodb"]["uri"])
    db = client[st.secrets["mongodb"]["database"]]
    return db
db = get_db()
HELPLINE = "+91-9204441036"

def main_navbar():
    col1, col2 = st.columns([5,1])
    with col1:
        if st.button("👤 My Profile"):
            st.session_state.page = "profile"
    with col2:
        if st.button("🚪 Logout"):
            for k in st.session_state.keys():
                del st.session_state[k]
            st.experimental_rerun()

def main():
    st.markdown("""<style>
    .stButton > button {background-color: #6C63FF; color:white; font-weight:600;}
    .stTitle {color: #1B2430;}
    </style>""", unsafe_allow_html=True)
    st.title("Welcome to Royal Ice Cream")
    main_navbar()
    st.image("https://5.imimg.com/data5/SELLER/Default/2022/4/GA/IB/YJ/62705623/amul-ice-cream-tenkasi.jpg",caption="Royal Ice Cream",use_column_width=True)
    st.write(f"📞 Helpline: {HELPLINE}")
    option = st.selectbox("Choose an option:", ["User", "Admin", "Terms & Conditions"])
    if option == "Terms & Conditions":
        terms_and_conditions()
    elif option == "Admin":
        admin_login()
    elif option == "User":
        user_login()
    if st.session_state.get("page") == "profile":
        user_profile()

def terms_and_conditions():
    st.header("Terms and Conditions")
    st.write("Add your detailed terms & conditions here.")
    if st.button("Back"):
        st.session_state.page = None

def send_otp(contact, mode):
    st.info(f"OTP sent to {contact} ({mode}) [simulation].")

# Admin login/registration
def admin_login():
    main_navbar()
    st.header("Admin Login")
    mode = st.radio("Login via:", ["Mobile Number", "Email"])
    contact = st.text_input("Contact (Admin)")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # Implement password check
        st.session_state["admin_logged_in"] = True
    if st.session_state.get("admin_logged_in"):
        admin_dashboard()

def admin_dashboard():
    main_navbar()
    st.header("Admin Dashboard")
    st.subheader("Register New User")
    first_name = st.text_input("First Name (Admin)")
    last_name = st.text_input("Last Name (Admin)")
    age = st.number_input("Age", min_value=1, max_value=120)
    user_password = st.text_input("Set Password", type="password")
    if st.button("Create User"):
        pw_hash = bcrypt.hashpw(user_password.encode(), bcrypt.gensalt())
        db.users.insert_one({"first_name": first_name, "last_name": last_name, "age": age, "password": pw_hash, "created_by": "admin"})
        st.success("User created!")
    st.subheader("Manage Products")
    prod_name = st.text_input("Product Name")
    price = st.number_input("Price (₹)", min_value=1)
    qty = st.number_input("Total Qty", min_value=1)
    if st.button("Add Product"):
        db.products.insert_one({"name": prod_name,"price": price,"total_qty": qty,"remaining_qty": qty,"daily_sale": 0,"likes": 0,"added_on": datetime.now()})
        st.success("Product added!")
    # Rest like analytics, remove, same as existing

def user_login():
    main_navbar()
    st.header("User Registration/Login")
    mode = st.radio("Login/Register via:", ["Mobile Number", "Email"])
    contact = st.text_input("Contact (User)")
    password = st.text_input("Password", type="password")
    if st.button("Send OTP"):
        send_otp(contact, mode)
        # Check if user exists
        user = db.users.find_one({"contact": contact})
        if not user:
            st.session_state["user_register_mode"] = True
        else:
            # Password check (bcrypt)
            if bcrypt.checkpw(password.encode(), user["password"]):
                st.success("Logged in successfully!")
                st.session_state["user_logged_in"] = True
            else:
                st.error("Wrong password!")

    if st.session_state.get("user_register_mode"):
        register_user(contact)
    if st.session_state.get("user_logged_in"):
        user_dashboard(contact)

def register_user(contact):
    st.subheader("Register")
    first_name = st.text_input("First Name (Reg)")
    last_name = st.text_input("Last Name (Reg)")
    age = st.number_input("Age", min_value=1, max_value=120)
    location = st.text_input("Location")
    password = st.text_input("Set Password", type="password")
    if st.button("Register"):
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        db.users.insert_one({
            "contact": contact, "first_name": first_name,
            "last_name": last_name, "age": age,
            "location": location, "password": pw_hash
        })
        st.success("Registered!")
        st.session_state["user_logged_in"] = True
        st.session_state["user_register_mode"] = False

def user_dashboard(contact):
    main_navbar()
    st.subheader("Your Details")
    user = db.users.find_one({"contact": contact})
    st.write(user)
    st.subheader("Products")
    products = list(db.products.find())
    cart, wishlist = [], []
    for p in products:
        st.markdown(f"**{p['name']}** | Price: <span style='color:red;'>₹{p['price']}</span> | Remaining: **{p['remaining_qty']}**", unsafe_allow_html=True)
        if st.button(f"Add {p['name']} to Cart"):
            cart.append(p["name"])
        if st.button(f"Add {p['name']} to Wishlist"):
            wishlist.append(p["name"])
        rating = st.slider(f"Rate {p['name']}", 1, 5, 3)
        feedback = st.text_input(f"Feedback for {p['name']}")
        if st.button(f"Submit Feedback for {p['name']}"):
            db.feedback.insert_one({
                "user": contact, "product": p["name"],
                "rating": rating, "text": feedback,
                "date": datetime.now()
            })
            db.products.update_one({"name": p["name"]}, {"$inc": {"likes": 1}})
            st.success("Feedback submitted.")
        if p["daily_sale"] == 0:
            st.info(f"Discount available on {p['name']}!")
    st.subheader("Cart")
    st.write(cart)
    st.subheader("Wishlist")
    st.write(wishlist)
    if st.button("Place Order"):
        order_id = db.orders.insert_one({
            "user": contact, "cart": cart,
            "timestamp": datetime.now(), "payment": "Pending"
        }).inserted_id
        st.success("Order placed successfully!")
        st.write("---")
        st.write(f"Invoice ID: {order_id}")
        st.markdown(f"Total Amount: <span style='font-size:22px;color:green;'>₹{sum([db.products.find_one({'name': i})['price'] for i in cart])}</span>", unsafe_allow_html=True)
        st.write("Payment method: (Online/Offline)")
        st.write("Thanks for choosing Royal Ice Cream and visit again!")

def user_profile():
    st.header("My Profile")
    contact = st.session_state.get("user_contact", None)
    if contact:
        user = db.users.find_one({"contact": contact})
        st.write(user)
    else:
        st.write("No profile loaded.")
    if st.button("Back"):
        st.session_state.page = None

if __name__ == "__main__":
    main()
