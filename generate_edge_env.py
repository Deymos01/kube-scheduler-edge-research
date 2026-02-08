NODE_GROUPS = [
    {
        "type": "powerful",
        "count": 10,
        "cpu": "8",
        "memory": "32Gi",
        "pods": "110",
        "region": "core-edge"
    },
    {
        "type": "gateway",
        "count": 30,
        "cpu": "4",
        "memory": "16Gi",
        "pods": "64",
        "region": "local-gateway"
    },
    {
        "type": "iot-a",
        "count": 20,
        "cpu": "2",
        "memory": "4Gi",
        "pods": "20",
        "region": "field-area"
    },
    {
        "type": "iot-b",
        "count": 20,
        "cpu": "2",
        "memory": "3Gi",
        "pods": "15",
        "region": "field-area"
    },
    {
        "type": "iot-c",
        "count": 20,
        "cpu": "1",
        "memory": "2Gi",
        "pods": "10",
        "region": "field-area"
    }
]

FILENAME = "kwok_edge_simulation.yaml"

def generate_node_yaml(name, specs):
    return f"""apiVersion: v1
kind: Node
metadata:
  name: {name}
  annotations:
    kwok.x-k8s.io/node: standard
  labels:
    beta.kubernetes.io/arch: amd64
    beta.kubernetes.io/os: linux
    kubernetes.io/hostname: {name}
    node-role.kubernetes.io/edge: "true"
    hardware-type: {specs['type']}
    topology.kubernetes.io/region: {specs['region']}
status:
  capacity:
    cpu: "{specs['cpu']}"
    memory: "{specs['memory']}"
    pods: "{specs['pods']}"
  allocatable:
    cpu: "{specs['cpu']}"
    memory: "{specs['memory']}"
    pods: "{specs['pods']}"
  phase: Running
---"""

def generate_kwok_stage():
    """Генерирует Stage для оживления узлов."""
    return """apiVersion: kwok.x-k8s.io/v1alpha1
kind: Stage
metadata:
  name: node-fast-simulation
spec:
  resourceRef:
    apiGroup: v1
    kind: Node
  selector:
    matchLabels:
      kwok.x-k8s.io/node: standard
  delay:
    durationMilliseconds: 1000
  next:
    statusTemplate: |
      phase: Running
      conditions:
      - type: Ready
        status: "True"
        lastHeartbeatTime: {{ .Now }}
        lastTransitionTime: {{ .Now }}
        reason: KubeletReady
        message: kubelet is posting ready status
---"""

def main():
    print(f"Generating configuration for {sum(g['count'] for g in NODE_GROUPS)} nodes...")
    
    with open(FILENAME, "w") as f_nodes:
        f_nodes.write(generate_kwok_stage() + "\n")

        for group in NODE_GROUPS:
            for i in range(group['count']):
                node_name = f"{group['type']}-{i}"
                f_nodes.write(generate_node_yaml(node_name, group) + "\n")

    print(f"Done! File saved as: {FILENAME}")

if __name__ == "__main__":
    main()