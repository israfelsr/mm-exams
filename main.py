import argparse
import numpy as np
from datasets import load_from_disk
import os
import random
import json
from tqdm import tqdm

from model_utils import (
    initialize_model,
    query_model,
    generate_prompt,
    fetch_cot_instruction,
    SUPPORTED_MODELS,
    TEMPERATURE,
    MAX_TOKENS,
)

IMAGE_ROOT = "/leonardo_work/EUHPC_D12_071/projects/mm-exams/"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--num_samples",
        type=int,
        default=None,
        help="number of samples to test",
    )
    parser.add_argument(
        "--method",
        type=str,
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
        nargs="+",
        default=["all"],
        help="list of strings of language codes",
    )
    parser.add_argument(
        "--api_key", type=str, default=None, help="explicitly give an api key"
    )
    parser.add_argument(
        "--dataset", type=str, required=True, help="dataset name or path"
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help=f"specify the model to use (must be one from the following: {', '.join(SUPPORTED_MODELS)})",
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default=None,
        help="Path to the model checkpoint or name",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Pass the file of aswers from where to resume",
    )
    args = parser.parse_args()
    return args


def map_image_path(example):
    if example["image"] is not None:
        example["image"] = IMAGE_ROOT + example["image"]
    return example


def load_and_filter_dataset(dataset_name: str, lang: str, num_samples: int, model):
    """
    Load and filter the dataset based on language and number of samples.
    """
    # Define a filtering function
    def multimodal_only(example):
        return example["image"]
    def text_only(example):
        return example["image"] is None  # Returns True when image is None

    # Apply the filter
    # TODO: ADD OTHER FILTERS
    dataset = load_from_disk(dataset_name)
    dataset = dataset.map(map_image_path)
    #dataset = dataset.filter(text_only)
    
    # Language
    # if lang != "all":
    #     dataset = dataset.filter(lambda sample: sample["language"] == lang)
    # else:
    #     print("evaluating all languages")
    # Level
    if num_samples is not None:
        dataset = dataset.select(range(num_samples))
    return dataset


def evaluate_model(args):
    """
    Run the evaluation pipeline for the specified model.
    """
    def is_multi_image(question):
        res = False
        for opt in question['options']:
            if opt.endswith('.png'): res = True
        return res

    # Set path
    if args.resume:
        output_path = args.resume
        with open(output_path, "r") as f:
            results = json.load(f)
            continue_from = len(results)
        
    else:
        output_folder = f"outputs/{args.method}/mode_{args.model}"
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, f"results.json")
        continue_from = 0
        results = []

    # Initialize model
    model, processor = initialize_model(args.model, args.model_path, args.api_key)

    temperature = TEMPERATURE
    max_tokens = MAX_TOKENS

    # Load dataset
    dataset = load_and_filter_dataset(
        args.dataset, args.selected_langs, args.num_samples, args.model
    )
    print(dataset)

    # Evaluate each question
    for t, question in tqdm(enumerate(dataset), total=len(dataset)):
        if t < continue_from:
            continue
        lang = question["language"]
        system_message = fetch_cot_instruction(lang)
        # Generate prompt. Note that only local models will need image_paths separatedly.

        if is_multi_image(question):
            reasoning, prediction = 'MULTI-IMAGE', 'MULTI-IMAGE'
        else:
            prompt, image_paths = generate_prompt(
                args.model, question, lang, system_message, args.setting
            )
            # Query model
            reasoning, prediction = query_model(
                args.model,
                model,
                processor,
                prompt,
                image_paths,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        question["prediction_by_" + args.model] = prediction
        question["reasoning_by_" + args.model] = reasoning
        # question["prompt_used"] = prompt
        result_metadata = question.copy()
        results.append(result_metadata)

        if (t + 1) % 100 == 0 or (t + 1) == len(dataset):
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)
            print(f"Ongoing {t} results saved to {output_path}")

    # Save results to file
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Evaluation completed. Results saved to {output_path}")


def main():
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    evaluate_model(args)


if __name__ == "__main__":
    main()
