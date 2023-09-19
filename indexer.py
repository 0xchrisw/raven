import io
import os
from traceback import print_exc

import concurrent.futures

import yaml
from yaml.constructor import Constructor

from config import Config
from workflow import Workflow
from composite_action import CompositeAction


# A hack to deny PyYAML to convert "on" tags into Python boolean values.
def add_bool(self, node):
    return self.construct_scalar(node)


Constructor.add_constructor("tag:yaml.org,2002:bool", add_bool)


def index_downloaded_workflows_and_actions() -> None:
    index_downloaded_actions()
    index_downloaded_workflows()


def index_downloaded_workflows() -> None:
    # with concurrent.futures.ProcessPoolExecutor(
    #     max_workers=Config.num_workers
    # ) as executor:
    #     futures = []
    #     for fname in os.listdir(Config.workflow_data_path):
    #         # fpath = os.path.join(Config.workflow_data_path, fname)
    #         fpath = fname
    #         futures.append(executor.submit(index_workflow_file, fpath))

    #     num_results = len(futures)
    #     for k, _ in enumerate(concurrent.futures.as_completed(futures)):
    #         print(f"[*] Indexing workflows. {k+1}/{num_results}", end="\r")
    fnames = os.listdir(Config.workflow_data_path)
    for fname in fnames:
        fpath = os.path.join(Config.workflow_data_path, fname)
        index_workflow_file(fpath)
        print(
            f"[*] Indexing workflows. {fnames.index(fname) + 1}/{len(fnames)}", end="\r"
        )


def index_downloaded_actions() -> None:
    # with concurrent.futures.ProcessPoolExecutor(
    #     max_workers=Config.num_workers
    # ) as executor:
    #     futures = []
    #     for fname in os.listdir(Config.action_data_path):
    #         fpath = os.path.join(Config.action_data_path, fname)
    #         futures.append(executor.submit(index_action_file, fpath))

    #     num_results = len(futures)
    #     for k, _ in enumerate(concurrent.futures.as_completed(futures)):
    #         print(f"[*] Indexing actions. {k+1}/{num_results}", end="\r")
    fnames = os.listdir(Config.action_data_path)
    for fname in fnames:
        fpath = os.path.join(Config.action_data_path, fname)
        index_action_file(fpath)
        print(
            f"[*] Indexing actions. {fnames.index(fname) + 1}/{len(fnames)}", end="\r"
        )


def index_action_file(fpath: str) -> None:
    try:
        if Config.action_index_cache.exists_in_cache(fpath):
            return

        with open(fpath, "r") as f:
            content = f.read()

        # PyYAML has issues with tabs.
        content = content.replace("\t", "  ")

        with io.StringIO() as f:
            f.write(content)
            f.seek(0)
            try:
                obj = yaml.load(f, yaml.loader.Loader)
            except yaml.scanner.ScannerError as e:
                print(f"[-] Failed loading: {fpath}. Exception: {e}. Skipping")
                return

        # Could happen if the YAML is empty.
        if not obj:
            return

        if isinstance(obj, str):
            # Treat it as a symlink
            # TODO
            print(f"[-] Symlink detected: {content}. Skipping...")
            return

        obj["path"] = fpath

        Config.graph.push_object(CompositeAction.from_dict(obj))
        Config.action_index_cache.insert_to_cache(fpath)
    except Exception as e:
        print(f"[-] Error while indexing {fpath}. {e}")
        print_exc()


def index_workflow_file(fpath: str) -> None:
    try:
        if Config.workflow_index_cache.exists_in_cache(fpath):
            return

        with open(fpath, "r") as f:
            content = f.read()

        # PyYAML has issues with tabs.
        content = content.replace("\t", "  ")

        with io.StringIO() as f:
            f.write(content)
            f.seek(0)
            try:
                obj = yaml.load(f, yaml.loader.Loader)
            except yaml.scanner.ScannerError as e:
                print(f"[-] Failed loading: {fpath}. Exception: {e}. Skipping")
                return

        # Could happen if the YAML is empty.
        if not obj:
            return

        if isinstance(obj, str):
            # Treat it as a symlink
            # TODO
            print(f"[-] Symlink detected: {content}. Skipping...")
            return

        obj["path"] = fpath
        Config.graph.push_object(Workflow.from_dict(obj))
        Config.workflow_index_cache.insert_to_cache(fpath)
    except Exception as e:
        print(f"[-] Error while indexing {fpath}. {e}")
        print_exc()