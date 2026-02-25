from openai import OpenAI
import os

# Es recomendable guardar tu API Key como variable de entorno
# export OPENAI_API_KEY="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"  (Linux/Mac)
# setx OPENAI_API_KEY "tu_api_key_aqui"    (Windows)

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