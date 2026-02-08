import yaml

PROFILE_A_COUNT = 150
PROFILE_B_COUNT = 20
PROFILE_C_COUNT = 10

def generate_pods():
    pods = []
    
    for i in range(1, PROFILE_A_COUNT + 1):
        pod = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': f'test-pod-a-{i}',
                'labels': {'profile': 'light'}
            },
            'spec': {
                'containers': [{
                    'name': 'main',
                    'image': 'busybox:latest',
                    'command': ['sh', '-c', 'sleep 3600'],
                    'resources': {
                        'requests': {
                            'cpu': '0.5',
                            'memory': '500Mi'
                        }
                    }
                }],
                'restartPolicy': 'Never'
            }
        }
        pods.append(pod)
    
    for i in range(1, PROFILE_B_COUNT + 1):
        pod = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': f'test-pod-b-{i}',
                'labels': {'profile': 'medium'}
            },
            'spec': {
                'containers': [{
                    'name': 'main',
                    'image': 'busybox:latest',
                    'command': ['sh', '-c', 'sleep 3600'],
                    'resources': {
                        'requests': {
                            'cpu': '1',
                            'memory': '1Gi'
                        }
                    }
                }],
                'restartPolicy': 'Never'
            }
        }
        pods.append(pod)
    
    for i in range(1, PROFILE_C_COUNT + 1):
        pod = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': f'test-pod-c-{i}',
                'labels': {'profile': 'heavy'}
            },
            'spec': {
                'containers': [{
                    'name': 'main',
                    'image': 'busybox:latest',
                    'command': ['sh', '-c', 'sleep 3600'],
                    'resources': {
                        'requests': {
                            'cpu': '2',
                            'memory': '2Gi'
                        }
                    }
                }],
                'restartPolicy': 'Never'
            }
        }
        pods.append(pod)
    
    return pods

def main():
    all_pods = generate_pods()
    
    doc = []
    for pod in all_pods:
        doc.append(yaml.dump(pod, default_flow_style=False))
    
    with open('test-workloads.yaml', 'w') as f:
        f.write('---\n'.join(doc))
    
    print(f"Generated YAML file with {len(all_pods)} pods")
    print("Pod distribution:")
    print(f"  Profile A (light): {PROFILE_A_COUNT} pods")
    print(f"  Profile B (medium): {PROFILE_B_COUNT} pods")
    print(f"  Profile C (heavy): {PROFILE_C_COUNT} pods")

if __name__ == '__main__':
    main()