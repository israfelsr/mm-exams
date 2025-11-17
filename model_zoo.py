import base64
import re
from io import BytesIO
from PIL import Image
import io

INSTRUCTIONS_COT = {
    "en": "The following is a multiple-choice question. Think step by step and then provide your FINAL answer between the tags <ANSWER> X </ANSWER> where X is ONLY the correct letter of your choice. Do not write additional text between the tags.",
    "es": "Lo siguiente es una pregunta de opción múltiple. Piensa paso a paso y luego proporciona tu RESPUESTA FINAL entre las etiquetas <ANSWER> X </ANSWER>, donde X es ÚNICAMENTE la letra correcta de tu elección. No escribas texto adicional entre las etiquetas.",
    "hi": "निम्नलिखित एक बहुविकल्पीय प्रश्न है। चरणबद्ध सोचें और फिर <ANSWER> X </ANSWER> टैग के बीच अपना अंतिम उत्तर प्रदान करें, जहाँ X केवल आपके चयन का सही अक्षर है। टैग के बीच अतिरिक्त कोई पाठ न लिखें।",
    "hu": "A következő egy feleletválasztós kérdés. Gondolkodj lépésről lépésre, majd add meg a VÉGSŐ válaszodat a <ANSWER> X </ANSWER> címkék között, ahol X CSAK a választott helyes betű. Ne írj további szöveget a címkék közé.",
    "hr": "Sljedeće je pitanje s višestrukim izborom. Razmislite korak po korak, a zatim dajte svoj ZAVRŠNI odgovor između oznaka <ANSWER> X </ANSWER> gdje je X SAMO ispravno slovo vašeg izbora. Nemojte pisati dodatni tekst između oznaka.",
    "uk": "Наступне — це питання з множинним вибором. Думайте крок за кроком, а потім надайте вашу ОСТАННЮ відповідь між тегами <ANSWER> X </ANSWER>, де X — ЛИШЕ правильна літера за вашим вибором. Не пишіть додаткового тексту між тегами.",
    "pt": "A seguir, temos uma questão de múltipla escolha. Pense passo a passo e depois forneça sua RESPOSTA FINAL entre as tags <ANSWER> X </ANSWER>, onde X é SOMENTE a letra correta da sua escolha. Não escreva texto adicional entre as tags.",
    "bn": "নিম্নলিখিতটি একটি বহু-বিকল্প প্রশ্ন। ধাপে ধাপে চিন্তা করুন এবং তারপর <ANSWER> X </ANSWER> ট্যাগের মধ্যে আপনার চূড়ান্ত উত্তর প্রদান করুন, যেখানে X শুধুমাত্র আপনার পছন্দের সঠিক অক্ষর। ট্যাগগুলির মধ্যে অতিরিক্ত কোনো লেখা লিখবেন না।",
    "te": "కింద ఇచ్చినది ఒక బహుళ ఎంపిక ప్రశ్న. దశల వారీగా ఆలోచించి, <ANSWER> X </ANSWER> ట్యాగ్లలో మీ తుది సమాధానాన్ని ఇవ్వండి, ఇక్కడ X మీ ఎంపికలోని సరైన అక్షరం మాత్రమే. ట్యాగ్లలో అదనపు వచనం రాయవద్దు.",
    "ne": "तलको प्रश्न बहुविकल्पीय छ। चरणबद्ध सोच्नुहोस् र त्यसपछि <ANSWER> X </ANSWER> ट्यागहरूबीच आफ्नो अन्तिम उत्तर प्रदान गर्नुहोस्, जहाँ X केवल तपाईंको रोजाइको सही अक्षर हो। ट्यागहरूबीच अतिरिक्त पाठ नलेख्नुहोस्।",
    "sr": "Sledeće je pitanje sa višestrukim izborom. Razmislite korak po korak, a zatim dajte svoj KONAČNI odgovor između oznaka <ANSWER> X </ANSWER>, gde je X SAMO tačno slovo vašeg izbora. Nemojte pisati dodatni tekst između oznaka.",
    "nl": "Het volgende is een meerkeuzevraag. Denk stap voor stap na en geef dan je UITEINDLIJKE antwoord tussen de tags <ANSWER> X </ANSWER>, waarbij X ALLEEN de juiste letter van je keuze is. Schrijf geen extra tekst tussen de tags.",
    "ar": "التالي هو سؤال اختيار من متعدد. فكر خطوة بخطوة ثم قدم إجابتك النهائية بين الوسوم <ANSWER> X </ANSWER> حيث X هي الحرف الصحيح فقط من اختيارك. لا تكتب نصًا إضافيًا بين الوسوم.",
    "ru": "Следующее — это вопрос с выбором ответа. Думайте шаг за шагом, а затем предоставьте ваш ОКОНЧАТЕЛЬНЫЙ ответ между тегами <ANSWER> X </ANSWER>, где X — ТОЛЬКО правильная буква вашего выбора. Не пишите дополнительный текст между тегами.",
    "fr": "Ce qui suit est une question à choix multiple. Réfléchissez étape par étape, puis donnez votre RÉPONSE FINALE entre les balises <ANSWER> X </ANSWER>, où X est UNIQUEMENT la lettre correcte de votre choix. N'écrivez pas de texte supplémentaire entre les balises.",
    "fa": "متن زیر یک سوال چندگزینه‌ای است. مرحله به مرحله فکر کنید و سپس پاسخ نهایی خود را بین تگ‌های <ANSWER> X </ANSWER> قرار دهید، جایی که X تنها حرف صحیح انتخاب شماست. متن اضافی بین تگ‌ها ننویسید.",
    "de": "Im Folgenden ist eine Multiple-Choice-Frage. Denken Sie Schritt für Schritt nach und geben Sie dann Ihre ENDGÜLTIGE Antwort zwischen den Tags <ANSWER> X </ANSWER> an, wobei X NUR der korrekte Buchstabe Ihrer Wahl ist. Schreiben Sie keinen zusätzlichen Text zwischen den Tags.",
    "lt": "Toliau pateikiamas klausimas su keliomis pasirinkimo galimybėmis. Mąstykite žingsnis po žingsnio ir pateikite savo GALUTINĮ atsakymą tarp žymų <ANSWER> X </ANSWER>, kur X yra TIK teisinga jūsų pasirinkta raidė. Nerašykite jokio papildomo teksto tarp žymų.",
}

keywords = {
    "en": {"question": "Question", "options": "Options", "answer": "Answer"},
    "es": {"question": "Pregunta", "options": "Opciones", "answer": "Respuesta"},
    "hi": {"question": "प्रश्न", "options": "विकल्प", "answer": "उत्तर"},
    "hu": {"question": "Kérdés", "options": "Lehetőségek", "answer": "Válasz"},
    "hr": {"question": "Pitanje", "options": "Opcije", "answer": "Odgovor"},
    "uk": {"question": "Питання", "options": "Варіанти", "answer": "Відповідь"},
    "pt": {"question": "Pergunta", "options": "Opções", "answer": "Resposta"},
    "bn": {"question": "প্রশ্ন", "options": "বিকল্প", "answer": "উত্তর"},
    "te": {"question": "ప్రశ్న", "options": "ఎంపికలు", "answer": "సమాధానం"},
    "ne": {"question": "प्रश्न", "options": "विकल्पहरू", "answer": "उत्तर"},
    "sr": {"question": "Pitanje", "options": "Opcije", "answer": "Odgovor"},
    "nl": {"question": "Vraag", "options": "Opties", "answer": "Antwoord"},
    "ar": {"question": "السؤال", "options": "الخيارات", "answer": "الإجابة"},
    "ru": {"question": "Вопрос", "options": "Варианты", "answer": "Ответ"},
    "fr": {"question": "Question", "options": "Options", "answer": "Réponse"},
    "fa": {"question": "سؤال", "options": "گزینه‌ها", "answer": "پاسخ"},
    "de": {"question": "Frage", "options": "Optionen", "answer": "Antwort"},
    "lt": {"question": "Klausimas", "options": "Pasirinkimai", "answer": "Atsakymas"},
}

# Only-English instructions for smaller models
SYS_MESSAGE = 'You are a helpful assistant who answers multiple-choice questions. For each question, output your final answer in JSON format with the following structure:\n\n{"choice": "The correct option (e.g., A, B, C, or D)"}\n\ONLY output this format exactly. Do not include any additional text or explanations outside the JSON structure.'
INSTRUCTION = "Output your choice in the specified JSON format."


# Molmo
def create_molmo_prompt_vllm(question, method, few_shot_samples):
    lang = question["language"]
    lang_keyword = keywords[lang]
    prompt = [SYS_MESSAGE]
    prompt.append(INSTRUCTION)
    if question["image"] is not None:
        images = [question["image"]]
    else:
        images = None
    prompt.append(
        f"\n{lang_keyword['question']}: {question['question'].replace('<image>', '')} \n{lang_keyword['options']}: \n"
    )
    for t, option in enumerate(question["options"]):
        index = f"{chr(65+t)}. "
        prompt.append(f"{index}) {option.replace('<image>', '')}\n")
    prompt.append(f"\nANSWER:")
    prompt = "".join(prompt)

    prompt = f"<|im_start|>user <image>\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    return prompt, images


# Pangea
def create_pangea_prompt(question, method, few_shot_samples):
    lang = question["language"]
    lang_keyword = keywords[lang]
    prompt = [f"<|im_start|>system\n{SYS_MESSAGE}<|im_end|>\n<|im_start|>user\n"]
    if question["image"] is not None:
        prompt.append("<image>\n")
        images = question["image"]
    else:
        images = None

    prompt.append(f"\n{INSTRUCTION}\n")
    prompt.append(
        f"\n{lang_keyword['question']}: {question['question'].replace('<image>', '')} \n{lang_keyword['options']}: \n"
    )
    for t, option in enumerate(question["options"]):
        index = f"{chr(65+t)}. "
        prompt.append(f"{index}) {option.replace('<image>', '')}\n")
    # prompt.append(f"\n{lang_keyword['answer']}:")
    prompt.append("<|im_end|>\n<|im_start|>assistant\n")
    message = "".join(prompt)
    return message, images


# Qwen
def create_qwen_prompt_vllm(question, method, few_shot_samples):
    # Determine the placeholder for images
    lang = question["language"]
    prompt = ""
    # Add the main question and options
    prompt += (
        #f"\n{INSTRUCTION}\n"
        f"\n{keywords[lang]['question']}: {question['question']}\n"
        f"{keywords[lang]['options']}:\n"
    )
    for t, option in enumerate(question["options"]):
        prompt += f"{chr(65 + t)}. {option}\n"
    prompt += f"\nANSWER:"

    # Construct the final message
    if question["image"] is not None:
        images = [question["image"]]
        message = (
            f"<|im_start|>system\n{INSTRUCTIONS_COT[lang]}<|im_end|>\n"
            f"<|im_start|>user\n<|vision_start|><|image_pad|><|vision_end|>\n"
            f"{prompt}<|im_end|>\n"
            "<|im_start|>assistant\n"
        )
    else:
        message = (
            f"<|im_start|>system\n{INSTRUCTIONS_COT[lang]}<|im_end|>\n"
            f"{prompt}<|im_end|>\n"
            "<|im_start|>assistant\n"
        )
        images = None

    return message, images


# Aya-Vision
def create_aya_prompt(question, method, few_shot_samples):
    lang = question["language"]
    lang_keyword = keywords[lang]
    prompt = []
    content = []
    # zero shot
    if question["image"] is not None:
        with open(question["image"], "rb") as img_file:
            img = Image.open(img_file).resize((512, 512))
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")

            base64_image_url = f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": base64_image_url},
            },
        )
    prompt.append(f"\n{INSTRUCTION}\n")
    prompt.append(f"\n{keywords[lang]['question']}: {question['question']}\n")
    prompt.append(f"{keywords[lang]['options']}:\n")
    for t, option in enumerate(question["options"]):
        index = f"{chr(65+t)}. "
        prompt.append(f"{index}) {option}\n")
    # prompt.append(f"\n{lang_keyword['answer']}:")
    prompt = "".join(prompt)
    content.append({"type": "text", "text": prompt})
    message = [
        {"role": "system", "content": SYS_MESSAGE},
        {"role": "user", "content": content},
    ]
    return message, None


# Claude
def create_claude_prompt(question, method, few_shot_samples):
    """
    Outputs: conversation dictionary supported by OpenAI.
    """
    question_text = question["question"]
    question_image = question["image"]
    options_list = question["options"]
    lang = question["language"]
    system_message = {"role": "system", "content": INSTRUCTIONS_COT[lang]}

    def encode_image(image_path):
        try:
            with open(image_path, "rb") as image_file:
                binary_data = image_file.read()
                base_64_encoded_data = base64.b64encode(binary_data)
                base64_string = base_64_encoded_data.decode("utf-8")
                return base64_string
        except Exception as e:
            raise TypeError(f"Image {image_path} could not be encoded. {e}")

    if question_image:
        base64_image = encode_image(question_image)
        question = [
            {"type": "text", "text": question_text},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "low",
                },
            },
        ]
    else:
        question = [{"type": "text", "text": question_text}]

    # Parse options. Handle options with images carefully by inclusion in the conversation.
    parsed_options = [{"type": "text", "text": "Options:\n"}]
    only_text_option = {"type": "text", "text": "{text}"}
    only_image_option = {
        "type": "image_url",
        "image_url": {"url": "data:image/jpeg;base64,{base64_image}", "detail": "low"},
    }

    for i, option in enumerate(options_list):
        option_indicator = f"{chr(65+i)}. "
        if option.lower().endswith(".png"):
            # Generating the dict format of the conversation if the option is an image
            new_image_option = only_image_option.copy()
            new_text_option = only_text_option.copy()
            formated_text = new_text_option["text"].format(text=option_indicator + "\n")
            new_text_option["text"] = formated_text

            parsed_options.append(new_text_option)
            parsed_options.append(
                new_image_option["image_url"]["url"].format(
                    base64_image=encode_image(option)
                )
            )

        else:
            # Generating the dict format of the conversation if the option is not an image
            new_text_option = only_text_option.copy()
            formated_text = new_text_option["text"].format(
                text=option_indicator + option + "\n"
            )
            new_text_option["text"] = formated_text
            parsed_options.append(new_text_option)

    user_text = question + parsed_options
    user_message = {"role": "user", "content": user_text}
    messages = [system_message, user_message]

    return messages, None


# Openai
def create_openai_prompt(question, method, few_shot_samples):
    """
    Outputs: conversation dictionary supported by Anthropic.
    """
    question_text = question["question"]
    question_image = question["image"]
    options_list = question["options"]
    lang = question["language"]
    system_message = {"role": "system", "content": INSTRUCTIONS_COT[lang]}

    def resize_and_encode_image(image_path):
        try:
            with Image.open(image_path) as img:
                # Resize the image to 512x512 using an appropriate resampling filter
                resized_img = img.resize((512, 512), Image.LANCZOS)

                # Save the resized image to a bytes buffer in PNG format
                buffer = BytesIO()
                resized_img.save(buffer, format="PNG")
                buffer.seek(0)

                # Encode the image in base64
                base64_encoded = base64.b64encode(buffer.read()).decode("utf-8")
                return base64_encoded
        except Exception as e:
            raise TypeError(f"Image {image_path} could not be processed. {e}")

    if question_image:
        base64_image = resize_and_encode_image(question_image)
        question = [
            {"type": "text", "text": question_text},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64_image,
                },
            },
        ]
    else:
        question = [{"type": "text", "text": question_text}]

    # Parse options. Handle options with images carefully by inclusion in the conversation.
    parsed_options = [{"type": "text", "text": "Options:\n"}]
    only_text_option = {"type": "text", "text": "{text}"}

    for i, option in enumerate(options_list):
        option_indicator = f"{chr(65+i)}. "
        if option.lower().endswith(".png"):
            # Generating the dict format of the conversation if the option is an image
            new_image_option = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": resize_and_encode_image(option),
                },
            }
            new_text_option = only_text_option.copy()
            formated_text = new_text_option["text"].format(text=option_indicator + "\n")
            new_text_option["text"] = formated_text

            parsed_options.append(new_text_option)
            parsed_options.append(new_image_option)

        else:
            # Generating the dict format of the conversation if the option is not an image
            new_text_option = only_text_option.copy()
            formated_text = new_text_option["text"].format(
                text=option_indicator + option + "\n"
            )
            new_text_option["text"] = formated_text
            parsed_options.append(new_text_option)

    user_text = question + parsed_options
    user_message = {"role": "user", "content": user_text}
    messages = [system_message, user_message]

    return messages, None  # image paths not expected for openai client.


def format_answer(answer: str):
    """
    Searchs for the answer between tags <Answer>.

    Returns: A zero-indexed integer corresponding to the answer.
    """
    pattern = r"<ANSWER>\s*([A-Za-z])\s*</ANSWER>"
    match = re.search(pattern, answer, re.IGNORECASE)

    if match:
        # Extract and convert answer letter
        letter = match.group(1).upper()
        election = ord(letter) - ord("A")

        # Extract reasoning by removing answer tag section
        start, end = match.span()
        reasoning = answer.strip()
        # Clean multiple whitespace
        reasoning = re.sub(r"\s+", " ", reasoning)
    elif len(answer) == 1:
        reasoning = answer
        if "A" <= answer <= "Z":
            # Convert letter to zero-indexed number
            election = ord(answer) - ord("A")
        elif "1" <= answer <= "9":
            # Convert digit to zero-indexed number
            election = int(answer) - 1
        else:
            election = answer
    else:
        # Error handling cases
        election = "No valid answer tag found"
        if re.search(r"<ANSWER>.*?</ANSWER>", answer):
            election = "Answer tag exists but contains invalid format"
        reasoning = answer.strip()

    return reasoning, election


def fetch_cot_instruction(lang: str) -> str:
    """
    Retrieves the CoT Instruction for the given lang.
    """
    if lang in INSTRUCTIONS_COT.keys():
        return INSTRUCTIONS_COT[lang]
    else:
        raise ValueError(f"{lang} language code not in INSTRUCTIONS_COT")


def fetch_few_shot_examples(lang):
    # TODO: write function. Should output a list of dicts in the conversation format expected.
    # I reckon we should do as parse_client_input with these. Add few-shot image examples regarding the format the input model expects.
    raise NotImplementedError(
        "The function to fetch few_shot examples is not yet implemented, but should return the few shot examples regarding that language."
    )
