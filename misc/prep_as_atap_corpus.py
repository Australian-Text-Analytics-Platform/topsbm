"""prep_as_atap_corpus.py

This is the dataset preparation script to make the 3 datasets wiki, arxiv and constitutions compatible with atap corpus.
The source of the dataset comes from Eduardo.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Self, Iterator

import pandas as pd


class WikiPath(Enum):
    document: str = f"{os.path.dirname(__file__)}/wikipedia-texts.txt"
    title: str = f"{os.path.dirname(__file__)}/wikipedia-titles.txt"
    meta_nodes: str = f"{os.path.dirname(__file__)}/wikipedia-metadataNodes.txt"
    meta_edges: str = f"{os.path.dirname(__file__)}/wikipedia-metadataEdgelist.txt"  # this will be unused for workshop 08.May.24


class ArxivPath(Enum):
    document: str = f"{os.path.dirname(__file__)}/arxiv-texts.txt"
    title: str = f"{os.path.dirname(__file__)}/arxiv-titles.txt"
    meta_nodes: str = f"{os.path.dirname(__file__)}/arxiv-metadataNodes.txt"
    meta_edges: str = f"{os.path.dirname(__file__)}/arxiv-metadataEdgelist.txt"  # this will be unused for workshop 08.May.24


class ConstitutionsPath(Enum):
    document: str = f"{os.path.dirname(__file__)}/constitutions-texts.txt"
    title: str = f"{os.path.dirname(__file__)}/constitutions-titles.txt"


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
    # note: nodes and edgelists only describes their relationship with no extra metadata hence skipped.
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
