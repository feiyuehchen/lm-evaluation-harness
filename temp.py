from datasets import load_dataset

# ds = load_dataset("lianghsun/tw-legal-benchmark-v1")

# print(ds)

# dataset = load_dataset("csv", data_files="data/short_question/judical_grade_1.csv")
dataset = load_dataset("feiyuehchen/TWCL")
print(dataset["train"])


# dataset = load_dataset("feiyuehchen/TWCL", 
#                        data_files={
#                           "grade_1": "judical_grade_1_train.csv",
#                           "grade_4": "judical_grade_4_train.csv"
#                        })
# print(dataset)

# ds = load_dataset("miulab/tmlu")
# print(ds)

# dataset.save_to_disk("temp")
# dataset.to_csv("temp.csv")