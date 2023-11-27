#!/usr/bin/python
"""
Top level script. Calls other functions that generate datasets that this script then creates in HDX.

"""
import logging
from os.path import expanduser, join

from hdx.api.configuration import Configuration
from hdx.facades.infer_arguments import facade
from hdx.utilities.downloader import Download
from hdx.utilities.path import progress_storing_folder, wheretostart_tempdir_batch
from hdx.utilities.retriever import Retrieve

from peacesecurity import PeaceSecurity

logger = logging.getLogger(__name__)

lookup = "hdx-scraper-peacesecurity"
updated_by_script = "HDX Scraper: Peace and Security"


def main(save: bool = False, use_saved: bool = False) -> None:
    """Generate datasets and create them in HDX"""
    with wheretostart_tempdir_batch(lookup) as info:
        folder = info["folder"]
        with Download() as downloader:
            retriever = Retrieve(
                downloader, folder, "saved_data", folder, save, use_saved
            )
            folder = info["folder"]
            batch = info["batch"]
            configuration = Configuration.read()
            peacesecurity = PeaceSecurity(configuration, retriever, folder)
            datasets = peacesecurity.get_data()
            logger.info(f"Number of datasets to upload: {len(datasets)}")

            for _, nextdict in progress_storing_folder(info, datasets, "name"):
                dataset_name = nextdict["name"]
                dataset, showcase = peacesecurity.generate_dataset_and_showcase(dataset_name)
                if dataset:
                    dataset.update_from_yaml()
                    dataset["notes"] = dataset["notes"].replace(
                        "\n", "  \n"
                    )  # ensure markdown has line breaks
                    dataset.create_in_hdx(
                        remove_additional_resources=True,
                        hxl_update=False,
                        updated_by_script="HDX Scraper: Peacekeeping",
                        batch=batch,
                    )
                    if showcase:
                        showcase.create_in_hdx()
                        showcase.add_dataset(dataset)


if __name__ == "__main__":
    facade(
        main,
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yaml"),
        user_agent_lookup=lookup,
        project_config_yaml=join("config", "project_configuration.yml")
    )
