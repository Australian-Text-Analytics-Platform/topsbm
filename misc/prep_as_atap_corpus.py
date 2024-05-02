"""prep_as_atap_corpus.py

This is the dataset preparation script to make the 3 datasets wiki, arxiv and constitutions compatible with atap corpus.
The source of the dataset comes from Eduardo.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Self, Iterator
import re

import pandas as pd

DATA_DIR: Path = Path(f"{os.path.dirname(__file__)}/.dataTopSBM")
assert DATA_DIR.is_dir(), f"{DATA_DIR.absolute()} directory does not exist."


class WikiPath(Enum):
    document: str = DATA_DIR.joinpath("wikipedia-texts.txt")
    title: str = DATA_DIR.joinpath("wikipedia-titles.txt")
    meta_nodes: str = DATA_DIR.joinpath("wikipedia-metadataNodes.txt")
    meta_edges: str = DATA_DIR.joinpath(
        "wikipedia-metadataEdgelist.txt"
    )  # this will be unused for workshop 08.May.24


class ArxivPath(Enum):
    document: str = DATA_DIR.joinpath("arxiv-texts.txt")
    title: str = DATA_DIR.joinpath("arxiv-titles.txt")
    meta_nodes: str = DATA_DIR.joinpath("arxiv-metadataNodes.txt")
    meta_edges: str = DATA_DIR.joinpath("arxiv-metadataEdgelist.txt")


class ConstitutionsPath(Enum):
    document: str = DATA_DIR.joinpath("constitutions-texts.txt")
    title: str = DATA_DIR.joinpath("constitutions-titles.txt")


class Dataset(str, Enum):
    wiki: Enum = WikiPath
    arxiv: Enum = ArxivPath
    constitution: Enum = ConstitutionsPath

    def __iter__(self) -> Iterator[Self]:
        return iter([Dataset(d) for d in self])


# Expected output:
# wiki-corpus.csv (document, doc_id)
# wiki-meta.csv (doc_id, title,  subcategory, category)


def parse(dataset: Dataset):
    match dataset:
        case Dataset.wiki:
            print(
                f"Parsed {dataset} into {Path(parse_wiki(out='wiki.csv')).absolute()}"
            )
        case Dataset.arxiv:
            print(
                f"Parsed {dataset} into {Path(parse_arxiv(out='arxiv.csv')).absolute()}"
            )
        case Dataset.constitution:
            print(
                f"Parsed {dataset} into {Path(parse_constitutions(out='constitutions.csv')).absolute()}"
            )
        case _:
            raise NotImplementedError("Not a valid dataset.")


def parse_wiki(out: str) -> str:
    assert out.endswith(".csv"), "Output path must end with .csv"
    df: pd.DataFrame = pd.read_table(
        WikiPath.document.value,
        header=None,
        names=["document"],
        index_col=False,
    )
    df["title"] = pd.read_table(WikiPath.title.value, header=None)
    df = pd.merge(df, pd.read_csv(WikiPath.meta_nodes.value, sep="\t"), on="title")
    assert (
        "category" in df.columns
    ), f"Missing 'category' column from {WikiPath.meta_nodes.value}."
    assert (
        "subcategory" in df.columns
    ), f"Missing 'subcategory' column from {WikiPath.meta_nodes.value}."

    df["category"] = df["category"].apply(lambda c: c.replace("Category:", "").strip())
    df["subcategory"] = df["subcategory"].apply(
        lambda c: c.replace("Category:", "").strip()
    )
    df.to_csv(out, index=False)
    return out


def parse_arxiv(out: str) -> str:
    assert out.endswith(".csv"), "Output path must end with .csv"
    df: pd.DataFrame = pd.read_table(
        ArxivPath.document.value,
        header=None,
        names=["document"],
        index_col=False,
    )
    df["title"] = pd.read_table(ArxivPath.title.value, header=None)
    df["category"] = pd.read_table(ArxivPath.meta_nodes.value, header=None).loc[:, 1]
    df["category"] = df["category"].apply(lambda c: c.replace("'", "").strip())
    df.to_csv(out, index=False)
    return out


def parse_constitutions(out: str):
    assert out.endswith(".csv"), "Output path must end with .csv"
    df: pd.DataFrame = pd.read_table(
        ConstitutionsPath.document.value,
        header=None,
        names=["document"],
        index_col=False,
    )
    df["title"] = pd.read_table(ConstitutionsPath.title.value, header=None)
    df.to_csv(out, index=False)
    return out


if __name__ == "__main__":
    for d in Dataset:
        parse(d)
