from pyzeebe import ZeebeWorker

def register_tasks(worker: ZeebeWorker):
    
    @worker.task(task_type="check-eligibility")
    def check_eligibility(monthly_views: int, subscribers: int):
        eligibility_status = None
        if monthly_views >= 4000 and subscribers >= 1000:
            eligibility_status = True
            print(f"Number of monthly_views: {monthly_views}, Number of subscribers: {subscribers}")
        else:
            eligibility_status = False
            print(f"not enough subscribers or monthly views")
        return {"eligibility_status": eligibility_status}

    @worker.task(task_type="verify-compliance")
    def verify_compliance(channel_category: str):
        if channel_category is None:
            compliance_status = False
            print("No category provided → not compliant")
        elif channel_category == "education":
            compliance_status = False
            print(f"Category '{channel_category}' → not compliant")
        else:
            compliance_status = True
            print(f"Category '{channel_category}' → compliant")
    
        return {"compliance_status": compliance_status}
