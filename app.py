import streamlit as st
import paramiko
import plotly.graph_objects as go
import time

# Fungsi untuk menjalankan perintah SSH
def execute_command(command):
    try:
        if 'ssh' in st.session_state and st.session_state.ssh.get_transport().is_active():
            stdin, stdout, stderr = st.session_state.ssh.exec_command(command)
            output = stdout.read().decode() + stderr.read().decode()
            return output.strip()
        else:
            return None
    except Exception as e:
        return None

# Fungsi Terminal SSH (CMD)
def ssh_terminal():
    st.header("🖥️ SSH Terminal")
    command = st.text_input("Enter command:")

    if st.button("Execute"):
        if command:
            output = execute_command(command)
            if output:
                st.text_area("Output:", output, height=200)
            else:
                st.error("No output received!")

# Fungsi untuk Server Monitoring
def server_monitoring():
    st.header("📊 Server Monitoring")
    placeholder = st.empty()

    while 'ssh' in st.session_state and st.session_state.ssh.get_transport().is_active():
        cpu_usage = execute_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'")
        mem_usage = execute_command("free -m | awk 'NR==2{printf \"%.2f\", $3*100/$2 }'")
        disk_usage = execute_command("df -h / | awk 'NR==2{print $5}' | tr -d '%'")

        if not cpu_usage or not mem_usage or not disk_usage:
            break

        cpu_usage = float(cpu_usage)
        mem_usage = float(mem_usage)
        disk_usage = float(disk_usage)

        with placeholder.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.plotly_chart(go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=cpu_usage,
                    title={'text': "CPU Usage (%)"},
                    gauge={'axis': {'range': [0, 100]}}
                )), use_container_width=True, key=f"cpu_{time.time()}")
            with col2:
                st.plotly_chart(go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=mem_usage,
                    title={'text': "Memory Usage (%)"},
                    gauge={'axis': {'range': [0, 100]}}
                )), use_container_width=True, key=f"mem_{time.time()}")
            with col3:
                st.plotly_chart(go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=disk_usage,
                    title={'text': "Disk Usage (%)"},
                    gauge={'axis': {'range': [0, 100]}}
                )), use_container_width=True, key=f"disk_{time.time()}")

        time.sleep(2)

    st.error("Connection lost!")

# Fungsi untuk User Management
def user_management():
    st.header("👤 User Management")

    if st.button("Show Users"):
        users = execute_command("cat /etc/passwd | cut -d: -f1")
        if users:
            st.text_area("User List:", users, height=200)

    new_user = st.text_input("New Username")
    if st.button("Add User"):
        if new_user:
            result = execute_command(f"sudo useradd {new_user}")
            st.success(f"User {new_user} added successfully!") if result == "" else st.error(result)

    del_user = st.text_input("Delete Username")
    if st.button("Delete User"):
        if del_user:
            result = execute_command(f"sudo userdel {del_user}")
            st.success(f"User {del_user} deleted successfully!") if result == "" else st.error(result)

# Fungsi login SSH
def ssh_login():
    st.title("🔐 SSH Login")
    host = st.text_input("Host")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=username, password=password)
            st.session_state.ssh = ssh
            st.session_state.menu = "Server Monitoring"  # Set default menu ke Monitoring
            st.session_state.logged_in = True  # Tandai login berhasil
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {str(e)}")

# Fungsi logout
def logout():
    if "ssh" in st.session_state:
        st.session_state.ssh.close()
        del st.session_state["ssh"]
    st.session_state.logged_in = False
    st.session_state.menu = "Server Monitoring"  # Reset menu ke default setelah logout
    st.rerun()

# **LOGIC UNTUK MENAMPILKAN PAGE**
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    ssh_login()  # Menampilkan login page sebelum semua menu
else:
    st.sidebar.button("Logout", on_click=logout)

    # Set menu default jika belum ada
    if "menu" not in st.session_state:
        st.session_state.menu = "Server Monitoring"

    menu = st.sidebar.radio("Navigation", ["Server Monitoring", "SSH Terminal", "User Management"], index=["Server Monitoring", "SSH Terminal", "User Management"].index(st.session_state.menu))

    # Simpan pilihan menu
    st.session_state.menu = menu

    # **Menampilkan menu yang dipilih tanpa bercampur dengan menu lain**
    if menu == "Server Monitoring":
        server_monitoring()
    elif menu == "SSH Terminal":
        ssh_terminal()
    elif menu == "User Management":
        user_management()
