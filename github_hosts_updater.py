# github_hosts_updater.py
import socket
import subprocess
import platform

GITHUB_DOMAINS = [
    "github.com",
    "raw.githubusercontent.com",
    "githubusercontent.com"
]

def resolve_ip(domain):
    try:
        return socket.gethostbyname(domain)
    except Exception as e:
        print(f"获取 {domain} IP 失败: {e}")
        return None

def update_hosts(domain_ip_map):
    hosts_path = "C:\\Windows\\System32\\drivers\\etc\\hosts" if platform.system() == "Windows" else "/etc/hosts"
    try:
        with open(hosts_path, "r+", encoding="utf-8") as f:
            content = f.read()
            f.seek(0)
            for domain, ip in domain_ip_map.items():
                content = "\n".join([line for line in content.splitlines() if domain not in line])
                content += f"\n{ip} {domain} # github加速\n"
            f.write(content)
            f.truncate()
        print("✅ hosts 更新完成")
    except Exception as e:
        print(f"❌ 写入 hosts 失败: {e}")

def update_github_hosts():
    domain_ip_map = {}
    for domain in GITHUB_DOMAINS:
        ip = resolve_ip(domain)
        if ip:
            domain_ip_map[domain] = ip
    if domain_ip_map:
        update_hosts(domain_ip_map)

