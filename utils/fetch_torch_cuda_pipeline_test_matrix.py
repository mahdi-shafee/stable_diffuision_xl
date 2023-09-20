import json
import os
from collections import defaultdict

from huggingface_hub import HfApi, ModelFilter

import diffusers

ALWAYS_TEST_PIPELINE_MODULES = [
    "controlnet",
    "stable_diffusion",
    "stable_diffusion_2",
    "stable_diffusion_xl",
    "deepfloyd_if",
    "kandinsky",
    "kandinsky2_2",
    "text_to_video_synthesis",
    "wuerstchen",
]
PIPELINE_USAGE_CUTOFF = int(os.getenv("PIPELINE_USAGE_CUTOFF", 10000))

api = HfApi()
filter = ModelFilter(library="diffusers")


def filter_pipelines(usage_dict, usage_cutoff=10000):
    output = []
    for diffusers_object, usage in usage_dict.items():
        if usage < usage_cutoff:
            continue

        if "Pipeline" in diffusers_object:
            output.append(diffusers_object)

    return output


def fetch_pipeline_objects():
    models = api.list_models(filter=filter)
    downloads = defaultdict(int)

    for model in models:
        is_counted = False
        for tag in model.tags:
            if tag.startswith("diffusers:"):
                is_counted = True
                downloads[tag[len("diffusers:") :]] += model.downloads

        if not is_counted:
            downloads["other"] += model.downloads

    # Remove 0 downloads
    downloads = {k: v for k, v in downloads.items() if v > 0}
    pipeline_objects = filter_pipelines(downloads, PIPELINE_USAGE_CUTOFF)

    return pipeline_objects


def fetch_pipeline_modules_to_test():
    pipeline_objects = fetch_pipeline_objects()

    test_modules = []
    for pipeline_name in pipeline_objects:
        module = getattr(diffusers, pipeline_name)
        test_module = module.__module__.split(".")[-2].strip()
        test_modules.append(test_module)

    return test_modules


def main():
    test_modules = fetch_pipeline_modules_to_test()
    test_modules.extend(ALWAYS_TEST_PIPELINE_MODULES)

    # Get unique modules
    test_modules = list(set(test_modules))
    print(json.dumps(test_modules))


if __name__ == "__main__":
    main()