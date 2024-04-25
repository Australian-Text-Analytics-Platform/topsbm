"""wrapper2.py

This is a wrapper over TopSBM and is meant to extend the existing workflow with
ATAP integration.
It provides the following:
    1. Enhanced visualisations.
    2. Integrate results into an ATAP Corpus.
"""

import sys
import subprocess
import tempfile
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import IO, Callable

from IPython.display import HTML

import networkx as nx
import numpy as np
from tqdm.auto import tqdm

from atap_corpus import Corpus
from atap_corpus.parts.dtm import DTM
from atap_corpus.utils import download
from topsbm.sbmtm import sbmtm

from utils import embed_js, progressive_merge
import srsly

__all__ = ["wrap"]


class ATAPWrapper(object):
    def __init__(self, model: sbmtm, corpus: Corpus, attribs: dict):
        self.model = model
        self.corpus = corpus
        self.attribs = attribs

    def serialise(self, file: PathLike[str] | IO):
        """Serialise with added topsbm attributes."""
        attribs = dict()
        try:
            git_args = {
                "origin": ["config", "--get", "remote.origin.url"],
                "commit": ["rev-parse", "HEAD"],
            }
            git = dict()
            for name, args in git_args.items():
                git[name] = (
                    subprocess.check_output(["git"] + args).strip().decode("utf-8")
                )

            git["origin"] = git["origin"].replace("git@github.com:", "https://")
            attribs["git"] = git
        except subprocess.CalledProcessError:
            print(
                "Failed to retrieve git information to be part of the Corpus attributes. Skipped.",
                file=sys.stderr,
            )
        attribs["data"] = self.attribs
        self.corpus.attribute("topsbm", attribs)
        return self.corpus.serialise(file)

    def download(self):
        return download(self.corpus)


def wrap(model: sbmtm, corpus: Corpus, used_dtm: str) -> ATAPWrapper:
    if not isinstance(model, sbmtm):
        raise ValueError(f"Expecting sbmtm for model but got {model}.")
    if not isinstance(corpus, Corpus):
        raise ValueError(f"Expecting Corpus for corpus but got {corpus}.")
    if model.g is None:
        raise ValueError("Your model hasn't been fitted yet. Call .fit() on the model.")

    # note: let's just only do this for level 0 for now.
    level = 0
    topic_dtms = topic_dtms_of(model, level, corpus.get_dtm(used_dtm))
    attributes = dict(word_clusters=dict(dtms=dict()), topic_dists=dict(metas=dict()))
    for cluster_idx, topic_dtm in topic_dtms.items():
        name = f"{used_dtm}_topsbm_lv{level}_cluster{cluster_idx}"
        attributes["word_clusters"]["dtms"][cluster_idx] = name
        corpus.add_dtm(topic_dtm, name)
    topic_dists: dict[int, np.ndarray[float]] = topic_dist_of(model, level)
    for topic_idx, topic_dist in topic_dists.items():
        name = f"topsbm_lv{level}_topic{topic_idx}"
        attributes["topic_dists"]["metas"][topic_idx] = name
        corpus.add_meta(topic_dist, name=name)
    return ATAPWrapper(model, corpus, attributes)


# -- Visualisers --
JUPYTER_ALLOW_HIDDEN = False
try:
    from notebook.services.contents.filemanager import FileContentsManager

    JUPYTER_ALLOW_HIDDEN = FileContentsManager().allow_hidden
except Exception as _:
    pass


class Hierarchy(str, Enum):
    RADIAL = "./viz/radial-cluster.js"
    TREE = "./viz/collapsible-tree.js"


class GroupMembershipKind(str, Enum):
    DOCUMENTS: str = "documents"
    WORDS: str = "words"


class Viz(object):
    def __init__(
        self,
        kind: GroupMembershipKind,
        hierarchy: Hierarchy,
        digraph: nx.DiGraph,
    ):
        self.kind = kind
        self.hierarchy = hierarchy
        self.digraph = digraph

        roots = [node for node, in_degree in digraph.in_degree() if in_degree == 0]
        assert len(roots) == 1, "Expecting only 1 root"
        root = roots[0]
        self.tree_data = nx.tree_data(digraph, root=root)

        global JUPYTER_ALLOW_HIDDEN
        self.tmpd = tempfile.mkdtemp(
            dir="./", prefix="." if JUPYTER_ALLOW_HIDDEN else "tmp"
        )
        tmp = tempfile.mktemp(dir=self.tmpd, suffix=".json")
        srsly.write_json(tmp, self.tree_data)

        self.htmls: dict[int, tuple[HTML, str]] = {
            0: (embed_js(self.hierarchy.value, tmp), tmp),
        }

    @property
    def max_depth(self):
        return self.tree_data["level"]

    def display(self, depth: int = 0):
        if depth > self.max_depth:
            raise ValueError(
                f"TopSBM have only inferred a maximum depth of {self.max_depth}."
            )
        if depth not in self.htmls.keys():
            merged_tree_data: dict = progressive_merge(self.tree_data)
            for merge_level, tree_data in merged_tree_data.items():
                if merge_level not in self.htmls.keys():
                    tmp = tempfile.mktemp(dir=self.tmpd, suffix=".json")
                    srsly.write_json(tmp, tree_data)
                    self.htmls[merge_level] = (embed_js(self.hierarchy.value, tmp), tmp)
        return self.htmls[depth][0]


def visualise(
    model: sbmtm,
    corpus: Corpus,
    kind: str | GroupMembershipKind,
    hierarchy: str | Hierarchy,
) -> Viz:
    try:
        hierarchy: Hierarchy = Hierarchy[
            hierarchy.upper() if isinstance(hierarchy, str) else hierarchy
        ]
    except ValueError:
        raise ValueError(
            f"hierarchy must be one of {', '.join([h.name.lower() for h in Hierarchy])}'"
        )
    try:
        kind: GroupMembershipKind = GroupMembershipKind[
            kind.upper() if isinstance(kind, str) else kind
        ]
    except Exception as e:
        raise ValueError(
            f"{kind} is not valid. Either {', '.join([k.value for k in GroupMembershipKind])}"
        )
    digraph: nx.DiGraph
    match kind:
        case GroupMembershipKind.DOCUMENTS:
            digraph = group_membership_digraphs_of(
                corpus,
                model,
                kind=GroupMembershipKind.DOCUMENTS,
            )
        case GroupMembershipKind.WORDS:
            digraph = group_membership_digraphs_of(
                corpus,
                model,
                kind=GroupMembershipKind.WORDS,
            )
        case _:
            raise NotImplementedError(f"{kind} is not implemented.")

    return Viz(
        kind=kind,
        hierarchy=hierarchy,
        digraph=digraph,
    )


# --- Data Adapters (from TopSBM to ATAP Corpus) ---


def group_membership_digraphs_of(
    corpus: Corpus,
    model: sbmtm,
    kind: GroupMembershipKind,
    top: int | None = None,
) -> nx.DiGraph:
    """Produce a networkx DiGraph based on the group membership output from topSBM.
    :arg model - a fitted topsbm.sbmtm model.

    :return Doc Digraph, Word DiGraph.

    There is a membership matrix for each layer of the model.
    The matrix describes the group that each word/token belongs for the layer.

    Group memberships are retrieved via sbmtm.group_membership(l=<level>) method.
    """
    DOC_MEMBERSHIP_IDX, WORD_MEMBERSHIP_IDX = 0, 1

    MEMBERSHIP_IDX: int
    leaf_nodes: list[str]
    match kind:
        case GroupMembershipKind.DOCUMENTS:
            MEMBERSHIP_IDX = DOC_MEMBERSHIP_IDX
            leaf_nodes = model.documents
            # metas: list[str] = corpus.metas
            # print(f"found metas: {', '.join(metas)}")
            # todo: Add meta data here (how to retrieve them?) - via corpus.
        case GroupMembershipKind.WORDS:
            MEMBERSHIP_IDX = WORD_MEMBERSHIP_IDX
            if top is not None:
                pass
            leaf_nodes = model.words
        case _:
            raise NotImplementedError(
                f"{kind} is not valid. Either {', '.join([k.value for k in GroupMembershipKind])}"
            )

    LEVEL_PREFIX = "Level_{level}_"
    G = nx.DiGraph()

    G.add_nodes_from(leaf_nodes)

    # now, all the edges between the nodes
    for level in range(0, len(model.state.levels)):
        memberships = model.group_membership(l=level)[MEMBERSHIP_IDX]
        cluster_names = [
            LEVEL_PREFIX.format(level=level) + str(i)
            for i in range(memberships.shape[0])
        ]
        G.add_nodes_from(cluster_names, kind="cluster", level=level)
        for cluster_idx in range(memberships.shape[0]):
            for label_idx in range(memberships.shape[1]):
                weight = memberships[cluster_idx, label_idx]
                is_member = weight > 0
                if is_member:
                    leaf, cluster = (
                        leaf_nodes[label_idx],
                        cluster_names[cluster_idx],
                    )
                    if level == 0:
                        G.add_edge(cluster, leaf, weight=weight)
                    else:
                        # 1. searches bottom up for all prior clusters of (layer - 1) connected to this leaf node.
                        # 2. add an edge from this cluster to all found prior clusters of (layer - 1)
                        edges = [(src, tgt) for src, tgt in G.edges() if tgt == leaf]
                        for l_tmp in range(1, level):
                            prior_clusters = [
                                src
                                for src, _ in edges
                                if src.startswith(
                                    LEVEL_PREFIX.format(level=str(l_tmp - 1))
                                )
                            ]
                            edges = [
                                (src, tgt)
                                for src, tgt in G.edges()
                                if tgt in prior_clusters
                            ]
                        prior_clusters = [prior for prior, _ in edges]
                        for prior_cluster in prior_clusters:
                            G.add_edge(cluster, prior_cluster, weight=weight)
    return G


def topic_dtms_of(model: sbmtm, level: int, from_dtm: DTM) -> dict[int, DTM]:
    """Produce DTMs of topics (word clusters) from the model.
    Used to add directly to Corpus via .add_dtm()
    """
    word_groups: np.ndarray = model.group_membership(l=level)[1]
    assert (
        from_dtm.num_terms == word_groups.shape[1]
    ), "Mismatched number of terms. Did you use this dtm to fit the model?"

    dtms = dict()
    for wgroup_idx in range(word_groups.shape[0]):
        dtms[wgroup_idx] = DTM.from_matrix(
            from_dtm.matrix.multiply(word_groups[wgroup_idx, :]), terms=from_dtm.terms
        )
    return dtms


def topic_dist_of(model: sbmtm, level: int) -> dict[int, np.ndarray[float]]:
    """Produce a list of topic distributions
    Used to add directly to Corpus via .add_meta()
    """
    p_tw_d = model.get_groups(l=level)["p_tw_d"]  # topic X doc
    num_topics = p_tw_d.shape[0]

    topic_dists = dict()
    for topic_idx in range(num_topics):
        topic_dists[topic_idx] = p_tw_d[topic_idx, :]
    return topic_dists


def to_list_of_terms(corpus: Corpus, tokeniser_fn: Callable) -> list[str]:
    return corpus.docs().apply(tokeniser_fn).tolist()
