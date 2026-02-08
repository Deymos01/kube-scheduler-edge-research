import subprocess
import json
import csv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Ошибка при выполнении команды: {cmd}\n{result.stderr}")
        return ""
    return result.stdout.strip()

def parse_cpu(cpu_str):
    if not cpu_str: return 0.0
    if isinstance(cpu_str, (int, float)): return float(cpu_str)
    
    cpu_str = str(cpu_str).lower()
    if cpu_str.endswith('m'):
        return float(cpu_str[:-1]) / 1000
    return float(cpu_str)

def parse_memory(mem_str):
    if not mem_str: return 0.0
    mem_str = str(mem_str).upper()
    
    units = {
        'KI': 1024,
        'MI': 1024**2,
        'GI': 1024**3,
        'TI': 1024**4,
        'K': 1000,
        'M': 1000**2,
        'G': 1000**3,
        'T': 1000**4
    }
    
    for unit, multiplier in units.items():
        if mem_str.endswith(unit):
            number = float(mem_str[:-len(unit)])
            return (number * multiplier) / (1024**3)

    try:
        return float(mem_str) / (1024**3)
    except ValueError:
        return 0.0

def get_node_info():
    cmd = 'kubectl get nodes -o json'
    nodes_json = run_command(cmd)
    if not nodes_json: return {}
    
    nodes_data = json.loads(nodes_json)
    node_info = {}
    
    for node in nodes_data['items']:
        name = node['metadata']['name']
        labels = node['metadata'].get('labels', {})
        hardware_type = labels.get('hardware-type', 'unknown')
        
        allocatable = node['status']['allocatable']
        cpu_cores = parse_cpu(allocatable.get('cpu', '0'))
        memory_gb = parse_memory(allocatable.get('memory', '0'))
        
        node_info[name] = {
            'hardware_type': hardware_type,
            'allocatable_cpu': cpu_cores,
            'allocatable_memory_gb': memory_gb,
            'pods': [],
            'total_cpu_allocated': 0.0,
            'total_memory_allocated_gb': 0.0
        }
    return node_info

def get_pod_distribution(node_info):
    cmd = 'kubectl get pods -A -o json'
    pods_json = run_command(cmd)
    if not pods_json: return [], node_info
    
    pods_data = json.loads(pods_json)
    pod_distribution = []
    
    for pod in pods_data['items']:
        pod_name = pod['metadata']['name']
        node_name = pod['spec'].get('nodeName')
        
        if not node_name or not pod_name.startswith('test-pod-'):
            continue
            
        cpu_req = 0.0
        mem_req = 0.0
        
        for container in pod['spec'].get('containers', []):
            requests = container.get('resources', {}).get('requests', {})
            cpu_req += parse_cpu(requests.get('cpu', '0'))
            mem_req += parse_memory(requests.get('memory', '0'))

        if 'test-pod-a-' in pod_name: profile = 'A (light)'
        elif 'test-pod-b-' in pod_name: profile = 'B (medium)'
        elif 'test-pod-c-' in pod_name: profile = 'C (heavy)'
        else: profile = 'unknown'
        
        pod_data = {
            'pod_name': pod_name,
            'node_name': node_name,
            'profile': profile,
            'cpu_request': round(cpu_req, 3),
            'memory_request_gb': round(mem_req, 3)
        }
        
        if node_name in node_info:
            node_info[node_name]['pods'].append(pod_data)
            node_info[node_name]['total_cpu_allocated'] += cpu_req
            node_info[node_name]['total_memory_allocated_gb'] += mem_req
            
        pod_distribution.append(pod_data)
        
    return pod_distribution, node_info

def calculate_metrics(node_info):
    for name, info in node_info.items():
        if info['allocatable_cpu'] > 0:
            info['cpu_usage_percent'] = round((info['total_cpu_allocated'] / info['allocatable_cpu']) * 100, 2)
        else:
            info['cpu_usage_percent'] = 0
            
        if info['allocatable_memory_gb'] > 0:
            info['memory_usage_percent'] = round((info['total_memory_allocated_gb'] / info['allocatable_memory_gb']) * 100, 2)
        else:
            info['memory_usage_percent'] = 0
            
        info['free_cpu'] = round(info['allocatable_cpu'] - info['total_cpu_allocated'], 3)
        info['free_memory_gb'] = round(info['allocatable_memory_gb'] - info['total_memory_allocated_gb'], 3)
        
    return node_info

def save_to_csv(node_info, pod_distribution):
    with open('node_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['node_name', 'hardware_type', 'alloc_cpu', 'alloc_mem_gb', 
                         'used_cpu', 'used_mem_gb', 'cpu_util_%', 'mem_util_%', 'num_pods'])
        for name, info in node_info.items():
            writer.writerow([
                name, info['hardware_type'], info['allocatable_cpu'], 
                round(info['allocatable_memory_gb'], 2),
                round(info['total_cpu_allocated'], 2), 
                round(info['total_memory_allocated_gb'], 2),
                info['cpu_usage_percent'], info['memory_usage_percent'], len(info['pods'])
            ])

    with open('pod_distribution.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['pod_name', 'node_name', 'hardware_type', 'profile', 'cpu_request', 'memory_request_gb'])
        writer.writeheader()
        for pod in pod_distribution:
            pod['hardware_type'] = node_info.get(pod['node_name'], {}).get('hardware_type', 'unknown')
            writer.writerow(pod)


def generate_plots():
    try:
        df_nodes = pd.read_csv('node_data.csv')
        df_pods = pd.read_csv('pod_distribution.csv')
        
        sns.set_theme(style="whitegrid")
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        sns.barplot(x='hardware_type', y='cpu_util_%', data=df_nodes, ax=axes[0], palette='viridis', errorbar=None)
        axes[0].set_title('Средняя загрузка CPU по типам оборудования (%)')
        axes[0].set_ylim(0, 100)

        all_hw_types = df_nodes['hardware_type'].unique()
        all_profiles = df_pods['profile'].unique()
        
        counts = df_pods.groupby(['hardware_type', 'profile']).size()
        
        full_index = pd.MultiIndex.from_product([all_hw_types, all_profiles], names=['hardware_type', 'profile'])
        
        pod_counts = counts.reindex(full_index, fill_value=0).reset_index(name='count')
        
        sns.barplot(x='hardware_type', y='count', hue='profile', data=pod_counts, ax=axes[1], palette='magma')
        axes[1].set_title('Распределение профилей по типам узлов')
        axes[1].legend(title='Profile', loc='upper center')
        plt.tight_layout()
        plt.savefig('experiment_results.png')
        
    except Exception as e:
        print(f"Ошибка при генерации графиков: {e}")

def main():
    node_info = get_node_info()
    pod_dist, node_info = get_pod_distribution(node_info)
    node_info = calculate_metrics(node_info)
    save_to_csv(node_info, pod_dist)
    generate_plots()

if __name__ == '__main__':
    main()