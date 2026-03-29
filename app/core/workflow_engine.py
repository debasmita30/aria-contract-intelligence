import json
from agents.failure_monitor import compute_reliability, check_failure
from agents.recovery_agent import recover

LOG_FILE = "app/logs/audit_log.json"

def log_event(event):
    try:
        data = json.load(open(LOG_FILE))
    except:
        data = []

    data.append(event)
    json.dump(data, open(LOG_FILE, "w"), indent=2)

def run_workflow(contract_text):
    state = {"input": contract_text}

    # Simulated evaluation scores
    logic, factual, compliance = 0.6, 0.7, 0.65
    complexity = 1

    reliability = compute_reliability(logic, factual, compliance, complexity)

    if check_failure(reliability):
        log_event({
            "step": "compliance_check",
            "status": "failed",
            "reason": "low reliability"
        })

        recovery = recover({"failure_reason": "ambiguity"})

        log_event({
            "step": "recovery",
            "status": "success",
            "action": recovery
        })

        return {
            "status": "recovered",
            "message": recovery
        }

    else:
        log_event({
            "step": "workflow",
            "status": "success"
        })

        return {
            "status": "success",
            "message": "Workflow completed successfully"
        }