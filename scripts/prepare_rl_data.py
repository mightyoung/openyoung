# RL Training Data Preparation Script
"""
Downloads and prepares RL training data from HuggingFace datasets
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def install_and_import_datasets():
    """Install datasets library if needed and import it"""
    try:
        from datasets import Dataset, load_dataset

        return load_dataset, Dataset
    except ImportError:
        print("Installing datasets library...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets", "-q"])
            from datasets import Dataset, load_dataset

            return load_dataset, Dataset
        except subprocess.CalledProcessError:
            print("Warning: Could not install datasets library. Using fallback mode.")
            return None, None


# Try to get datasets loader
load_dataset, Dataset = install_and_import_datasets()


# Default small test dataset for development
DEFAULT_TEST_PROMPTS = [
    "Write a function to calculate fibonacci numbers",
    "Explain what is recursion in programming",
    "How do I sort a list in Python?",
    "Write a function to check if a string is a palindrome",
    "Implement binary search algorithm",
    "What is the difference between list and tuple?",
    "Write a function to find the maximum element in an array",
    "Explain how quicksort works",
]


def prepare_test_data(output_dir: str = "data/rl/test"):
    """
    Prepare small test dataset for development/testing

    This creates a synthetic dataset that mimics the structure
    needed for RL training without downloading large datasets.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    data = []
    for i, prompt in enumerate(DEFAULT_TEST_PROMPTS):
        # Generate synthetic responses with varying quality
        responses = [
            f"Response A for: {prompt}",  # Low quality
            f"Here is a good solution for: {prompt}. " + "x" * 100,  # Medium quality
            f"Perfect answer for: {prompt}. "
            + "Detailed explanation with examples." * 20,  # High quality
        ]

        # Simulate rewards (chosen=2, rejected=0)
        data.append(
            {
                "prompt": prompt,
                "chosen": responses[2],
                "rejected": responses[0],
                "reward_chosen": 1.0,
                "reward_rejected": 0.0,
            }
        )

    # Save as JSONL
    output_file = output_path / "train.jsonl"
    with open(output_file, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")

    print(f"Test data saved to: {output_file}")
    return str(output_file)


def download_oasst1(output_dir: str = "data/rl/oasst1", sample_size: int = 1000):
    """
    Download OpenAssistant dataset from HuggingFace

    This dataset contains 74K human-generated assistant conversations.
    """
    global load_dataset
    if load_dataset is None:
        print("Error: datasets library not available. Please install with: pip install datasets")
        print("Falling back to test data...")
        return prepare_test_data(output_dir)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading OpenAssistant dataset (sample: {sample_size})...")

    try:
        # Load full dataset
        ds = load_dataset("OpenAssistant/oasst1", split="train")

        # Convert to RL-friendly format
        data = []
        for item in ds.select(range(min(sample_size, len(ds)))):
            # Extract conversation pairs
            if "messages" in item:
                messages = item["messages"]
                if len(messages) >= 2:
                    # Get prompt (user message) and response (assistant message)
                    prompt = None
                    chosen = None

                    for msg in messages:
                        if msg["role"] == "user":
                            prompt = msg["content"]
                        elif msg["role"] == "assistant" and prompt and not chosen:
                            chosen = msg["content"]
                            data.append(
                                {
                                    "prompt": prompt,
                                    "chosen": chosen,
                                    "rejected": "I cannot help with that.",  # Synthetic negative
                                    "reward_chosen": 1.0,
                                    "reward_rejected": 0.0,
                                }
                            )
                            break

        # Save as JSONL
        output_file = output_path / "oasst1_train.jsonl"
        with open(output_file, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

        print(f"OpenAssistant data saved to: {output_file}")
        print(f"Total samples: {len(data)}")
        return str(output_file)

    except Exception as e:
        print(f"Error downloading dataset: {e}")
        print("Falling back to test data...")
        return prepare_test_data(output_dir)


def download_hh_rlhf(output_dir: str = "data/rl/hh_rlhf", sample_size: int = 1000):
    """
    Download HH-RLHF dataset from HuggingFace

    Contains helpful and harmless preference data.
    """
    global load_dataset
    if load_dataset is None:
        print("Error: datasets library not available. Please install with: pip install datasets")
        return None

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading HH-RLHF dataset (sample: {sample_size})...")

    try:
        ds = load_dataset("Anthropic/hh-rlhf", split="train")

        data = []
        for item in ds.select(range(min(sample_size, len(ds)))):
            if "chosen" in item and "rejected" in item:
                # Extract prompt from the conversation
                chosen = item["chosen"]
                rejected = item["rejected"]

                # Try to extract the prompt
                if "\n\n" in chosen:
                    parts = chosen.split("\n\n", 1)
                    prompt = parts[0]
                    chosen = parts[1] if len(parts) > 1 else chosen
                else:
                    prompt = chosen[:100]  # Fallback

                data.append(
                    {
                        "prompt": prompt[:500],  # Truncate long prompts
                        "chosen": chosen[:2000],
                        "rejected": rejected[:2000],
                        "reward_chosen": 1.0,
                        "reward_rejected": 0.0,
                    }
                )

        output_file = output_path / "hh_rlhf_train.jsonl"
        with open(output_file, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

        print(f"HH-RLHF data saved to: {output_file}")
        print(f"Total samples: {len(data)}")
        return str(output_file)

    except Exception as e:
        print(f"Error downloading HH-RLHF: {e}")
        return None


def prepare_synthetic_data(output_dir: str = "data/rl/synthetic"):
    """
    Create synthetic training data for testing

    This is useful when no external datasets are available.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Task categories for diverse training
    task_templates = [
        ("coding", "Write a {function} in Python"),
        ("explanation", "Explain what is {concept}"),
        ("comparison", "What is the difference between {a} and {b}?"),
        ("debugging", "Fix this code: {code}"),
        ("optimization", "Optimize this {algorithm}"),
    ]

    coding_tasks = [
        "fibonacci",
        "binary search",
        "quicksort",
        "merge sort",
        "bubble sort",
        "linked list",
        "binary tree",
        "hash table",
    ]

    concepts = [
        "recursion",
        "iteration",
        "polymorphism",
        "encapsulation",
        "inheritance",
        "abstraction",
        "closure",
        "decorator",
    ]

    data = []

    # Generate coding tasks
    for i, task in enumerate(coding_tasks):
        prompt = f"Write a function to calculate {task}"
        data.append(
            {
                "prompt": prompt,
                "chosen": f"def {task.replace(' ', '_')}(n):\n    # Implementation here\n    pass",
                "rejected": "I don't know how to do that.",
                "reward_chosen": 1.0,
                "reward_rejected": 0.0,
            }
        )

    # Generate explanation tasks
    for i, concept in enumerate(concepts):
        prompt = f"Explain what is {concept}"
        data.append(
            {
                "prompt": prompt,
                "chosen": f"{concept} is an important programming concept that...",
                "rejected": "Skip.",
                "reward_chosen": 1.0,
                "reward_rejected": 0.0,
            }
        )

    # Save as JSONL
    output_file = output_path / "synthetic_train.jsonl"
    with open(output_file, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")

    print(f"Synthetic data saved to: {output_file}")
    print(f"Total samples: {len(data)}")
    return str(output_file)


def main():
    parser = argparse.ArgumentParser(description="Prepare RL training data")
    parser.add_argument("--output-dir", default="data/rl", help="Output directory")
    parser.add_argument(
        "--dataset",
        choices=["test", "oasst1", "hh_rlhf", "synthetic", "all"],
        default="test",
        help="Dataset to download",
    )
    parser.add_argument("--sample-size", type=int, default=1000, help="Sample size")

    args = parser.parse_args()

    if args.dataset == "test":
        prepare_test_data(args.output_dir + "/test")
    elif args.dataset == "oasst1":
        download_oasst1(args.output_dir + "/oasst1", args.sample_size)
    elif args.dataset == "hh_rlhf":
        download_hh_rlhf(args.output_dir + "/hh_rlhf", args.sample_size)
    elif args.dataset == "synthetic":
        prepare_synthetic_data(args.output_dir + "/synthetic")
    elif args.dataset == "all":
        # Download all datasets
        prepare_test_data(args.output_dir + "/test")
        prepare_synthetic_data(args.output_dir + "/synthetic")
        download_oasst1(args.output_dir + "/oasst1", args.sample_size)
        download_hh_rlhf(args.output_dir + "/hh_rlhf", args.sample_size)

    print("\nData preparation complete!")
    print(f"Data saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
