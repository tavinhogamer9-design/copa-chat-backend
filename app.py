import os

from flask import Flask, request, jsonify
from flask_cors import CORS

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# CONFIGURAÇÃO
# ============================================================

load_dotenv()


API_KEY = os.getenv("GROQ_API_KEY")


if not API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY não encontrada no arquivo .env"
    )


client = Groq(
    api_key=API_KEY
)


app = Flask(__name__)

CORS(app)


# ============================================================
# MODELO
# ============================================================

MODEL = "openai/gpt-oss-120b"


# ============================================================
# PROMPT PRINCIPAL
# ============================================================

SYSTEM_PROMPT = """
Você é o CopaBot, um chatbot especializado EXCLUSIVAMENTE
em Copa do Mundo de futebol.

Seu conhecimento e suas respostas devem permanecer sempre
relacionados à Copa do Mundo.

Você pode falar sobre:

- História das Copas do Mundo
- Todas as edições da Copa
- Seleções participantes
- Jogadores
- Técnicos
- Finais
- Semifinais
- Quartas de final
- Fase de grupos
- Eliminatórias relacionadas à Copa
- Artilheiros
- Recordes
- Títulos
- Campanhas das seleções
- Jogos históricos
- Gols históricos
- Estádios das Copas
- Países-sede
- Mascotes
- Troféus
- Curiosidades
- Estatísticas
- Convocações relacionadas às Copas
- Resultados históricos
- Comparações entre seleções ou jogadores quando relacionadas
  à Copa do Mundo

REGRA FUNDAMENTAL:

Você NÃO deve responder perguntas que não estejam relacionadas
à Copa do Mundo.

Se o usuário perguntar sobre qualquer outro assunto, responda
EXATAMENTE:

"Não conheço esse assunto. Meu conhecimento é focado
exclusivamente na Copa do Mundo. ⚽🏆"

Não tente responder parcialmente uma pergunta fora do tema.

Exemplos de assuntos fora do tema:

- programação
- política
- matemática
- carros
- filmes
- jogos eletrônicos
- notícias sem relação com Copa do Mundo
- tecnologia
- programação Python
- programação web
- vida pessoal
- saúde
- finanças
- receitas
- outros esportes que não estejam diretamente relacionados
  à Copa do Mundo

IMPORTANTE:

Se uma pergunta misturar Copa do Mundo com outro assunto,
responda somente à parte relacionada à Copa do Mundo.

Se a pergunta estiver claramente relacionada à Copa do Mundo,
responda normalmente.

Responda em português do Brasil.

Se não souber uma informação específica, diga claramente
que não possui informação suficiente. Nunca invente fatos.

Se houver datas ou estatísticas históricas, procure ser
preciso e contextualize a informação.

Mantenha respostas claras, naturais e fáceis de entender.

Você é um especialista em história da Copa do Mundo.
"""


# ============================================================
# FILTRO BÁSICO DE ASSUNTO
# ============================================================

WORLD_CUP_KEYWORDS = [

    "copa",
    "copas",
    "mundo",
    "mundial",

    "fifa",

    "seleção brasileira",
    "seleção",
    "seleções",

    "brasil",
    "argentina",
    "alemanha",
    "frança",
    "itália",
    "espanha",
    "inglaterra",
    "uruguai",
    "holanda",
    "portugal",

    "jogador",
    "jogadores",
    "artilheiro",
    "artilheiros",

    "gol",
    "gols",

    "final",
    "semifinal",
    "quartas",
    "oitavas",
    "fase de grupos",

    "campeão",
    "campeões",
    "título",
    "títulos",

    "troféu",
    "taça",

    "estádio",
    "estádios",

    "mascote",

    "1970",
    "1974",
    "1978",
    "1982",
    "1986",
    "1990",
    "1994",
    "1998",
    "2002",
    "2006",
    "2010",
    "2014",
    "2018",
    "2022",
    "2026",

    "1930",
    "1934",
    "1938",
    "1950",
    "1954",
    "1958",
    "1962",
    "1966",

]


def is_world_cup_topic(message: str) -> bool:

    message = message.lower().strip()

    for keyword in WORLD_CUP_KEYWORDS:

        if keyword in message:
            return True

    return False


# ============================================================
# RESPOSTA PARA ASSUNTO FORA DA COPA
# ============================================================

OUT_OF_TOPIC_RESPONSE = (
    "Não conheço esse assunto. "
    "Meu conhecimento é focado exclusivamente "
    "na Copa do Mundo. ⚽🏆"
)


# ============================================================
# ROTA PRINCIPAL
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "Dados inválidos."
            }), 400


        user_message = data.get(
            "message",
            ""
        ).strip()


        if not user_message:

            return jsonify({
                "error": "Mensagem vazia."
            }), 400


        # ----------------------------------------------------
        # PRIMEIRO FILTRO
        # ----------------------------------------------------

        if not is_world_cup_topic(user_message):

            return jsonify({
                "response": OUT_OF_TOPIC_RESPONSE
            })


        # ----------------------------------------------------
        # HISTÓRICO
        # ----------------------------------------------------

        history = data.get(
            "history",
            []
        )


        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]


        # Limitamos o histórico para evitar
        # requisições desnecessariamente grandes.

        if isinstance(history, list):

            history = history[-10:]


            for item in history:

                if not isinstance(item, dict):
                    continue

                role = item.get("role")

                content = item.get("content")


                if role not in [
                    "user",
                    "assistant"
                ]:
                    continue


                if not isinstance(content, str):
                    continue


                messages.append({
                    "role": role,
                    "content": content
                })


        # ----------------------------------------------------
        # MENSAGEM ATUAL
        # ----------------------------------------------------

        messages.append({
            "role": "user",
            "content": user_message
        })


        # ----------------------------------------------------
        # GROQ
        # ----------------------------------------------------

        completion = client.chat.completions.create(

            model=MODEL,

            messages=messages,

            temperature=0.3,

            max_tokens=700

        )


        response = completion.choices[0].message.content


        if not response:

            response = (
                "Não consegui encontrar uma resposta "
                "sobre a Copa do Mundo."
            )


        return jsonify({
            "response": response
        })


    except Exception as error:

        print(
            f"Erro no servidor: {error}"
        )


        return jsonify({
            "error": "Erro interno no servidor."
        }), 500


# ============================================================
# TESTE
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "online",
        "message": "CopaBot está funcionando! ⚽🏆"
    })


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )