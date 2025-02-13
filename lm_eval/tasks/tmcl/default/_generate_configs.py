"""
Take in a YAML, and output all "other" splits with this YAML
"""

import argparse
import os

import pandas as pd
import yaml
from tqdm import tqdm


categories = {
    "examination_for_judicial_personnel": [
        "bar_judge_examination", 
        "judicial_grade_4", 
        "judicial_grade_5"
    ],
    "basic_features_from_judgments": [
        "punishment_category", 
        "term_imprisonment", 
        "fine", 
        "convicted", 
        "confiscation", 
        "crime_name"
    ],
    "conceptual_features_from_judgments": [
        "public_safety", 
        "public_authority", 
        "mastermind", 
        "evidence_debate", 
        "lineal_relative", 
        "weapon", 
        "cruel_mean", 
        "plan"
    ]
}

task_list = [
    # "basic article",
    "bar judge examination",
    "judicial grade 4",
    "judicial grade 5",
    "public authority",
    "weapon",
    "punishment category",
    "term imprisonment",
    "fine",
    "convicted",
    "lineal relative",
    "plan",
    "evidence debate",
    "cruel mean",
    "public safety",
    "mastermind",
    "confiscation", 
    "crime_name"
]

subject2name = {}
subject2num_choice = {}
subject2category = {}
SUBJECTS = {}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_yaml_path", default="_default_template_yaml")
    parser.add_argument("--save_prefix_path", default="tmcl")
    parser.add_argument("--cot_prompt_path", default=None)
    parser.add_argument("--task_prefix", default="")
    parser.add_argument("--group_prefix", default="")
    parser.add_argument("--subject_file", default="../subject.tsv")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    from pathlib import Path

    # Initialization
    SUBJECT_FILE = Path(__file__).parent / Path(args.subject_file)

    df = pd.read_csv(SUBJECT_FILE, delimiter="\t")

    for _, row in df.iterrows():
        for _c in categories:
            if row["subject"] in SUBJECTS:
                raise ValueError(f"Duplicate tasks. {row['subject']} already exists.")
            if row["category"] in categories[_c]:  # append new item into SUBJECTS
                SUBJECTS[row["subject"]] = _c
                subject2name[row["subject"]] = row["name"]
                subject2num_choice[row["subject"]] = row["# Choices"]
                break
    # End of SUBJECTS initialization

    # get filename of base_yaml so we can `"include": ` it in our "other" YAMLs.
    base_yaml_name = os.path.split(args.base_yaml_path)[-1]
    with open(args.base_yaml_path) as f:
        base_yaml = yaml.full_load(f)

    if args.cot_prompt_path is not None:
        import json

        with open(args.cot_prompt_path) as f:
            cot_file = json.load(f)

    ALL_CATEGORIES = []
    for subject, category in tqdm(SUBJECTS.items()):
        if category not in ALL_CATEGORIES:
            ALL_CATEGORIES.append(category)

        if args.cot_prompt_path is not None:
            description = cot_file[subject]
        else:
            name_of_subject = subject2name[subject].replace("＿", " ")
            description = f"以下為{name_of_subject}的單選題，請提供正確答案的選項。\n\n"
            # description = f"The following are multiple choice questions (with answers) about {' '.join(subject.split('_'))}.\n\n"

        num_choies = subject2num_choice[subject]
        # basic_doc_to_text = "{{question.strip()}}\nA. {{choices[0]}}\nB. {{choices[1]}}\nC. {{choices[2]}}\nD. {{choices[3]}}"
        basic_doc_to_choice = ["A", "B", "C"]
        if num_choies == 4:
            basic_doc_to_choice.append("D")
        if num_choies == 5:
            # basic_doc_to_text += "\nE. {{choices[4]}}"
            basic_doc_to_choice.append("E")
        if num_choies == 6:
            # basic_doc_to_text += "\nE. {{choices[4]}}\nF. {{choices[5]}}"
            basic_doc_to_choice += ["E", "F"]
        # basic_doc_to_text += "\nAnswer:"
        # basic_doc_to_text = "{{question.strip()}}\nA. {{choices[0]}}\nB. {{choices[1]}}\nC. {{choices[2]}}\nD. {{choices[3]}}{% if choices[4] %}\nE. {{choices[4]}}{% endif %}{% if choices[5] %}\nF. {{choices[5]}}{% endif %}\nAnswer:"
        # generate_until_text = "請輸出最佳答案的選項字母。"
        basic_doc_to_text = "{{question.strip()}}\nA. {{choices[0]}}\nB. {{choices[1]}}\nC. {{choices[2]}}{% if choices is defined and choices|length > 3 %}\nD. {{choices[3]}}{% endif %}\n{{data}}\nAnswer:"
        
        yaml_dict = {
            "include": base_yaml_name,
            "group": f"tmcl_{args.task_prefix}_{category}"
            if args.task_prefix != ""
            else f"tmcl_{category}",
            "group_alias": category.replace("_", " "),
            "task": f"tmcl_{args.task_prefix}_{subject}"
            if args.task_prefix != ""
            else f"tmcl_{subject}",
            "task_alias": subject.replace("_", " "),
            "dataset_name": subject,
            "description": description,
            # doc_to_text: "{{question.strip()}}\nA. {{choices[0]}}\nB. {{choices[1]}}\nC. {{choices[2]}}\nD. {{choices[3]}}\nAnswer:"
            "doc_to_text": basic_doc_to_text,
            # doc_to_choice: ["A", "B", "C", "D"]
            "doc_to_choice": basic_doc_to_choice,
        }

        file_save_path = args.save_prefix_path + f"_{subject}.yaml"
        # eval_logger.info(f"Saving yaml for subset {subject} to {file_save_path}")
        with open(file_save_path, "w") as yaml_file:
            yaml.dump(
                yaml_dict,
                yaml_file,
                # width=float("inf"),
                allow_unicode=True,
                default_style='"',
            )

    if args.task_prefix != "":
        mmlu_subcategories = [
            f"tmcl_{args.task_prefix}_{category}" for category in ALL_CATEGORIES
        ]
    else:
        mmlu_subcategories = [f"tmcl_{category}" for category in ALL_CATEGORIES]

    if args.group_prefix != "":
        file_save_path = args.group_prefix + ".yaml"
    else:
        file_save_path = args.save_prefix_path + ".yaml"

    # eval_logger.info(f"Saving benchmark config to {file_save_path}")
    with open(file_save_path, "w") as yaml_file:
        yaml.dump(
            {
                "group": f"tmcl_{args.task_prefix}"
                if args.task_prefix != ""
                else "tmcl",
                "task": mmlu_subcategories,
            },
            yaml_file,
            indent=4,
            default_flow_style=False,
        )
