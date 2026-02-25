from openai import OpenAI
import os

client = OpenAI()



def enviar_prompt(prompt):
    response = client.responses.create(
        model="gpt-4.1-nano",  # Puedes cambiar el modelo si lo necesitas
        input=prompt
    )
    
    return response.output_text


if __name__ == "__main__":
    prompt_usuario = "Explícame qué es Kubernetes en 1 línea."
    resultado = enviar_prompt(prompt_usuario)
    print("Respuesta del modelo:\n")
    print(resultado)