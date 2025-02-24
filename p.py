import time
import streamlit as st
import plotly.graph_objects as go

def execute_command(command):
    # Implementasi fungsi execute_command
    pass

def server_monitoring():
    st.header("📊 Server Monitoring")
    placeholder = st.empty()

    while 'ssh' in st.session_state and st.session_state.ssh.get_transport().is_active():
        # Ambil data penggunaan resources
        cpu_usage = execute_command("""
            awk '/cpu / {
                total = $2 + $3 + $4 + $5 + $6 + $7 + $8 + $9 + $10;
                idle = $5;
                printf "%.1f", 100 - (idle * 100 / total)
            }' /proc/stat
        """)
        
        mem_usage = execute_command("""
            awk '
                /MemTotal/ {total=$2}
                /MemAvailable/ {available=$2}
                END {printf "%.2f", ((total - available) / total) * 100}
            ' /proc/meminfo
        """)
        
        disk_usage = execute_command("df -h / | awk 'NR==2{print $3 \"/\" $2}'")

        # Handle jika data tidak valid
        if not all([cpu_usage, mem_usage, disk_usage]):
            st.error("Failed to get monitoring data")
            break

        try:
            cpu_usage = float(cpu_usage)
            mem_usage = float(mem_usage)
        except ValueError:
            st.error("Invalid monitoring data format")
            break

        # Tampilkan visualisasi
        with placeholder.container():
            col1, col2, col3 = st.columns(3)
            
            with col1:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=cpu_usage,
                    title={'text': "CPU Usage (%)"},
                    gauge={'axis': {'range': [0, 100]}}
                ))
                st.plotly_chart(fig, use_container_width=True, key=f"cpu_usage_chart_{time.time()}")
            
            with col2:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=mem_usage,
                    title={'text': "Memory Usage (%)"},
                    gauge={'axis': {'range': [0, 100]}}
                ))
                st.plotly_chart(fig, use_container_width=True, key=f"mem_usage_chart_{time.time()}")
            
            with col3:
                st.text(f"Disk Usage: {disk_usage}")

        time.sleep(2)

    st.error("Connection lost!")