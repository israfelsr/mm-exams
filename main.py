import argparse
import json
import pandas as pd
import numpy as np
from datasets import load_dataset
import os
import random
from typing import List, Dict
from predict_answers import run_answer_prediction

from model_utils import initialize_model, query_model, SUPPORTED_MODELS


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--num_samples",
        type=str,
        default="5",
        help="number of samples to test",
    )
    parser.add_argument(
        "--setting",
        type=int,
        default="zero-shot",
        help="[few-shot, zero-shot]",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed",
    )
    parser.add_argument(
        "--selected_langs",
        type=str,
        default=None,
        help="list of strings of languages",
    )
    parser.add_argument(
        "api_key", type=str, default=None, help="explicitly give an api key"
    )
    parser.add_argument(
        "--dataset", type=str, required=True, help="dataset name or path"
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help=f"Specify the model to use (must be one from the following: {', '.join(SUPPORTED_MODELS)})",
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default=None,
        help="Path to the model checkpoint or name",
    )
    args = parser.parse_args()
    return args


def test_lang(args, lang: str): # Manu: already done by run_answer_prediction
    # TODO: needs refactor to fit model_predict calls
    setting = args.setting

    output_folder = f"outputs/{setting}/mode_{args.model}/{lang}"
    os.makdirs(output_folder, exist_ok=True)

    if setting == "few-shot":
        fewshot_samples = generate_fewshot_samples(lang)
    else:
        fewshot_samples = {}

    # load dataset
    dataset = load_dataset(args.dataset)
    dataset = dataset.filter(lambda sample: sample["language"] == lang)

    if args.num_samples != "all":
        max_test_samples = int(args.num_samples)
        dataset = dataset.select(range(max_test_samples))

    # generate prompts
    all_prompts = [
        generate_prompt(lang, args.setting, args.model, question, fewshot_samples)
        for question in dataset
    ]

    # initialize and query
    if args.model in ["qwen", "llava"]:
        if args.model == "qwen":
            model, tokenizer = initialize_model("qwen", args.model_path)
            predictions = query_model("qwen", model, tokenizer, all_prompts)
        elif args.model == "llava":
            model, tokenizer, image_processor = initialize_model(
                "llava", args.model_path
            )
    elif args.model == "chatgpt":
        model, tokenizer, image_processor = None, None, None
    else:
        raise ValueError(f"Unsuported model: {args.model}")

    # Save Results
    save_results(output_folder, dataset, predictions, all_prompts)
    print(f"Evaluation completed for {lang}. Results saved to {output_folder}")

# Manu:
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# When is this used?
def generate_one_example(question, lang):
    # TODO: add other languages and methods - check images as answers
    answer_word = {"english": "Answer:"}
    prompt = (
        question["question"]
        + "\n"
        + "\n".join(question["options"])
        + f"\n{answer_word}"
    )
    return prompt


def generate_fewshot_samples(lang):
    return {}

# Manu:
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Ya tenemos esto, en parse_{model}_input
def generate_prompt(
    model: str,
    lang: str,
    setting: str,
    question,
    fewshot_samples=None,
):
    # TODO: add all the languages. 
    #       Manu: qué onda con la hint?? Me genera dudas
    if lang == "english":
        hint = f"The following is a multiple choice question about {question['category_original_lang']}."
    else:
        raise NotImplementedError(f"Language {lang} is not supported.")

    # TODO: add models, languages and few-shot. 
    if setting == "zero-shot":
        if lang == "english":
            hint += "\nPlease only give the correct option, without any other details or explanations."
        else:
            raise NotImplemented

    prompt = "{}\n<img>{}</img>Context: {}\nQuestion: {}\nOptions: {}\nAnswer:"
    # model-specific formatting
    if model == "qwen":
        image = f"<img>{question['image']}</img>"
        question = question["question"]
        options = "\n".join(question["options"])
        prompt = prompt.format(hint, image, question, options)

    return prompt


def save_results(
    output_folder: str,
    results: Dict
):
    output_path = os.path.join(output_folder, "results.json")
    df = pd.read_json(results)
    df.to_csv(output_path, index=False)


def main():
    #TODO: pending finish
    # Manu: levantar el dataset desde args y correr run_evaluation con las config de args.

    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)

    # select test parameters 
    #       Manu: Para mí hay que hacer distinto esto: cargar directo el dataset entero y hacer 
    #       la evaluación sobre tooodas las preguntas. Después filtramos por lenguaje en eval.py .
    # all_langs = ["english"]
    # selected_langs = eval(args.selected_langs) if args.selected_langs else all_langs

    # # read api key
    # api_key = args.api_key

    # for lang in selected_langs:
    #     test_lang(args, lang)

    # Load dataset.
    dataset = load_dataset(args.dataset)

    # Run evaluation.
    results = run_answer_prediction(args.model, dataset, args.api_key)

    # Save csv results in results folder.
    output_folder = 'results'
    save_results(output_folder, results)
    print(f"Evaluation completed. Results saved to {output_folder}")


