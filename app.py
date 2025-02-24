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
    
    # Inisialisasi data history di session state
    if 'cpu_history' not in st.session_state:
        st.session_state.cpu_history = []
    if 'mem_history' not in st.session_state:
        st.session_state.mem_history = []
    if 'disk_history' not in st.session_state:
        st.session_state.disk_history = []
    
    placeholder = st.empty()
    max_history = 20  # Jumlah maksimum data point yang disimpan

    while 'ssh' in st.session_state and st.session_state.ssh.get_transport().is_active():
        # Ambil data
        cpu = execute_command("""
            awk '/cpu / {
                total = $2 + $3 + $4 + $5 + $6 + $7 + $8 + $9 + $10;
                idle = $5;
                printf "%.1f", 100 - (idle * 100 / total)
            }' /proc/stat
        """)
        
        mem = execute_command("""
            awk '
                /MemTotal/ {total=$2}
                /MemAvailable/ {available=$2}
                END {printf "%.2f", ((total - available) / total) * 100}
            ' /proc/meminfo
        """)
        
        disk = execute_command("df -h / | awk 'NR==2{print $5}' | tr -d '%'")
        disk_total = execute_command("df -h / | awk 'NR==2{print $3 \"/\" $2}'")

        if not all([cpu, mem, disk]):
            break

        try:
            # Update history
            timestamp = time.strftime("%H:%M:%S")
            st.session_state.cpu_history.append((timestamp, float(cpu)))
            st.session_state.mem_history.append((timestamp, float(mem)))
            st.session_state.disk_history.append((timestamp, float(disk)))
            
            # Batasi history
            for metric in ['cpu_history', 'mem_history', 'disk_history']:
                if len(st.session_state[metric]) > max_history:
                    st.session_state[metric].pop(0)
        except ValueError:
            break

        # Buat line chart
        with placeholder.container():
            
            # Disk Chart
            st.markdown("**Disk Usage :**")
            st.markdown(f"<span style='font-size:40px; font-weight:bold;'>{disk_total}</span>", unsafe_allow_html=True)
            
            # CPU Chart
            fig_cpu = go.Figure()
            fig_cpu.add_trace(go.Scatter(
                x=[t[0] for t in st.session_state.cpu_history],
                y=[t[1] for t in st.session_state.cpu_history],
                mode='lines+markers',
                name='CPU Usage'
            ))
            fig_cpu.update_layout(
                title='CPU Usage History (%)',
                xaxis_title='Time',
                yaxis_title='Usage (%)',
                height=300
            )
            st.plotly_chart(fig_cpu, use_container_width=True)

            # Memory Chart
            fig_mem = go.Figure()
            fig_mem.add_trace(go.Scatter(
                x=[t[0] for t in st.session_state.mem_history],
                y=[t[1] for t in st.session_state.mem_history],
                mode='lines+markers',
                name='Memory Usage',
                line=dict(color='#FFA15A')
            ))
            fig_mem.update_layout(
                title='Memory Usage History (%)',
                xaxis_title='Time',
                yaxis_title='Usage (%)',
                height=300
            )
            st.plotly_chart(fig_mem, use_container_width=True)

            # Disk Chart

        time.sleep(2)

    st.error("Connection lost!")

# Fungsi untuk User Management
def user_management():
    st.header("👤 User Management")

    # Menampilkan daftar user
    if st.button("Show Users"):
        users = execute_command("getent passwd | awk -F: '$6 ~ /^\\/home\\// || $6 == \"/root\" {print $1 \"    \" $6}'")
        if users:
            st.text_area("User List:", users, height=200)

    # Form untuk menambahkan user
    with st.form("add_user_form"):
        new_user = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        add_user_submit = st.form_submit_button("Add User")

        if add_user_submit and new_user and new_password:
            result = execute_command(f"sudo useradd {new_user}")
            if result == "":
                execute_command(f'echo "{new_user}:{new_password}" | sudo chpasswd')
                st.success(f"User {new_user} added successfully!")
            else:
                st.error(result)

    # Form untuk menghapus user
    with st.form("delete_user_form"):
        del_user = st.text_input("Delete Username")
        del_user_submit = st.form_submit_button("Delete User")

        if del_user_submit and del_user:
            result = execute_command(f"sudo userdel {del_user}")
            if result == "":
                st.success(f"User {del_user} deleted successfully!")
            else:
                st.error(result)
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
