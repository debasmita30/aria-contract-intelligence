import json

class DecisionGraph:
    def __init__(self):
        self.nodes = []

    def add(self, step, status):
        self.nodes.append({"step": step, "status": status})

    def save(self):
        with open("app/logs/decision_graph.json", "w") as f:
            json.dump(self.nodes, f, indent=2)