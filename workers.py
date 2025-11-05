from pyzeebe import ZeebeWorker

def register_tasks(worker: ZeebeWorker):
    
    @worker.task(task_type="check-name")
    def check_name(client_name: str):
        if client_name == "anna":
            print(f"right name, {client_name}")
        else:
            print(f"wrong name, {client_name}")
        # ici tu peux mettre ton code réel
        return {"name": client_name}

    @worker.task(task_type="calculate_something")
    def calculate(number: int):
        result = number * 2
        print(f"Calcul terminé : {result}")
        return {"result": result}
