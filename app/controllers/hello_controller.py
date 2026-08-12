# app\controllers\hello_controller.py
def get_hello() -> dict[str, str]:
    return {"message": "Hello, World!"}

def get_bye() -> dict[str, str]:
    return {"message": "Goodbye, World!"}