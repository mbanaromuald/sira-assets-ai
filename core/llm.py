import os

def available():
    k = os.getenv("GROQ_API_KEY", "")
    return bool(k) and not k.endswith("here")

def chat(system, user, temperature=0.1, max_tokens=700):
    from groq import Groq
    r = Groq(api_key=os.environ["GROQ_API_KEY"]).chat.completions.create(
        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"), temperature=temperature, max_tokens=max_tokens,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    return r.choices[0].message.content.strip()
