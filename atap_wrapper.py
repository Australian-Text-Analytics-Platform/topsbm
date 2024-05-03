"""wrapper2.py

This is a wrapper over TopSBM and is meant to extend the existing workflow with
ATAP integration.
It provides the following:
    1. Enhanced visualisations.
    2. Integrate results into an ATAP Corpus.
"""

import os
import sys
import subprocess
import tempfile
from enum import Enum
from os import PathLike
from typing import IO, Callable, Any

from IPython.display import HTML

import networkx as nx
import numpy as np

from atap_corpus import Corpus
from atap_corpus.parts.dtm import DTM
from topsbm.sbmtm import sbmtm

from utils import embed_js, merge_leafs_per_depth, top_word_indices_for_level
import srsly

__all__ = [
    "add_results",
    "visualise",
]


def add_results(model: sbmtm, corpus: Corpus):
    if not isinstance(model, sbmtm):
        raise ValueError(f"Expecting sbmtm for model but got {model}.")
    if not isinstance(corpus, Corpus):
        raise ValueError(f"Expecting Corpus for corpus but got {corpus}.")
    if model.g is None:
        raise ValueError("Your model hasn't been fitted yet. Call .fit() on the model.")

    DOC_MEMBERSHIP_IDX: int = 0

    attribs = {"meta": list()}
    for level in range(0, len(model.state.levels)):
        doc_memberships = model.group_membership(l=level)[DOC_MEMBERSHIP_IDX]
        membership_vector = np.argmax(doc_memberships.T, axis=1)
        name = f"topsbm_lvl_{level}_cluster"
        corpus.add_meta(membership_vector, name=name)
        attribs["meta"].append(name)

    try:
        git_args = {
            "origin": ["config", "--get", "remote.origin.url"],
            "commit": ["rev-parse", "HEAD"],
        }
        git = dict()
        for name, args in git_args.items():
            git[name] = subprocess.check_output(["git"] + args).strip().decode("utf-8")

        git["origin"] = git["origin"].replace("git@github.com:", "https://")
        attribs["git"] = git
    except subprocess.CalledProcessError:
        print(
            "Failed to retrieve git information to be part of the Corpus attributes. Skipped.",
            file=sys.stderr,
        )
    corpus.attribute("topsbm", attribs)


# -- Visualisers --
JUPYTER_ALLOW_HIDDEN = False
try:
    from notebook.services.contents.filemanager import FileContentsManager

    JUPYTER_ALLOW_HIDDEN = FileContentsManager().allow_hidden
except Exception as _:
    pass

# constants
_LEVEL_META_KEY: str = "level"
_IS_ROOT_META_KEY: str = "is_root"


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

        global _IS_ROOT_META_KEY
        roots = [
            node
            for node in digraph
            if digraph.nodes[node].get(_IS_ROOT_META_KEY, False)
        ]
        assert len(roots) == 1, "Expecting only 1 root"
        root = roots[0]

        self.tree_data = nx.tree_data(digraph, root=root)

        global JUPYTER_ALLOW_HIDDEN
        if not JUPYTER_ALLOW_HIDDEN:
            os.makedirs("./tmp", exist_ok=True)
        self.tmpd = tempfile.mkdtemp(
            dir="./" if JUPYTER_ALLOW_HIDDEN else "./tmp",
            prefix="." if JUPYTER_ALLOW_HIDDEN else "",
        )
        tmp = tempfile.mktemp(dir=self.tmpd, suffix=".json")
        srsly.write_json(tmp, self.tree_data)

        self.htmls: dict[int, tuple[HTML, str, dict]] = {
            0: (embed_js(self.hierarchy.value, tmp), tmp, self.tree_data),
        }

    @property
    def min_depth(self) -> int:
        return 0

    @property
    def max_depth(self) -> int:
        global _LEVEL_META_KEY
        return self.tree_data[_LEVEL_META_KEY]

    def display(self, depth: int = 0):
        if depth > self.max_depth:
            raise ValueError(
                f"TopSBM have only inferred a maximum depth of {self.max_depth}."
            )
        if depth < self.min_depth:
            raise ValueError("TopSBM have a minimum of depth 0.")

        if depth not in self.htmls.keys():
            global _LEVEL_META_KEY
            merged_tree_data: dict = merge_leafs_per_depth(
                self.tree_data, level_key=_LEVEL_META_KEY
            )
            for merge_level, tree_data in merged_tree_data.items():
                if merge_level not in self.htmls.keys():
                    tmp = tempfile.mktemp(dir=self.tmpd, suffix=".json")
                    srsly.write_json(tmp, tree_data)
                    self.htmls[merge_level] = (
                        embed_js(self.hierarchy.value, tmp),
                        tmp,
                        tree_data,
                    )
        return self.htmls[depth][0]


def visualise(
    model: sbmtm,
    corpus: Corpus,
    kind: str | GroupMembershipKind,
    hierarchy: str | Hierarchy,
    categories: list[str] | None = None,
    top_words_for_level: int = 0,
    top_num_words: int = 5,
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
                categories=categories,
            )
        case GroupMembershipKind.WORDS:
            digraph = group_membership_digraphs_of(
                corpus,
                model,
                kind=GroupMembershipKind.WORDS,
                categories=categories,
                top_num_words=top_num_words,
                top_words_for_level=top_words_for_level,
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
    categories: list[str] | None = None,
    top_words_for_level: int = 0,
    top_num_words: int = 1,
) -> nx.DiGraph:
    """Produce a networkx DiGraph based on the group membership output from topSBM.
    :arg model - a fitted topsbm.sbmtm model.

    :return Doc Digraph, Word DiGraph.

    There is a membership matrix for each layer of the model.
    The matrix describes the group that each word/token belongs for the layer.

    Group memberships are retrieved via sbmtm.group_membership(l=<level>) method.
    """
    global _LEVEL_META_KEY
    global _IS_ROOT_META_KEY

    DOC_MEMBERSHIP_IDX, WORD_MEMBERSHIP_IDX = 0, 1

    MEMBERSHIP_IDX: int
    leaf_nodes: list[str]
    leaf_nodes_to_retain: list[str]
    match kind:
        case GroupMembershipKind.DOCUMENTS:
            MEMBERSHIP_IDX = DOC_MEMBERSHIP_IDX
            leaf_nodes = model.documents
            leaf_nodes_to_retain = leaf_nodes
            label_indices = list(range(len(leaf_nodes)))
        case GroupMembershipKind.WORDS:
            if top_words_for_level > (len(model.state.levels) - 1):
                raise ValueError(f"Maximum level is {len(model.state.levels) - 1}")
            if top_words_for_level < 0:
                raise ValueError("Minimum level is 0.")
            MEMBERSHIP_IDX = WORD_MEMBERSHIP_IDX
            leaf_nodes = model.words
            top_word_indices: list[int] = top_word_indices_for_level(
                model, top=top_num_words, level=top_words_for_level
            )
            leaf_nodes_to_retain = [model.words[idx] for idx in top_word_indices]
            label_indices = top_word_indices
        case _:
            raise NotImplementedError(
                f"{kind} is not valid. Either {', '.join([k.value for k in GroupMembershipKind])}"
            )
    if categories is not None and len(categories) != len(leaf_nodes):
        word_or_document: str = (
            "documents" if MEMBERSHIP_IDX == DOC_MEMBERSHIP_IDX else "words"
        )
        raise ValueError(
            f"Mismatched number of categories ({len(categories)}) with number of {word_or_document} ({len(leaf_nodes)})."
        )

    LEVEL_PREFIX = "Level_{level}_"
    G = nx.DiGraph()
    if categories is not None:
        G.add_nodes_from(
            [
                (leaf, {"category": categories[idx]})
                for idx, leaf in zip(label_indices, leaf_nodes_to_retain)
            ]
        )
    else:
        G.add_nodes_from(leaf_nodes_to_retain)

    # now, all the edges between the nodes
    for level in range(0, len(model.state.levels)):
        memberships = model.group_membership(l=level)[MEMBERSHIP_IDX]
        cluster_names = [
            LEVEL_PREFIX.format(level=level) + str(i)
            for i in range(memberships.shape[0])
        ]
        cluster_metadata: dict[str, Any] = {
            "kind": "cluster",
            _LEVEL_META_KEY: level,
            _IS_ROOT_META_KEY: level == (len(model.state.levels) - 1),
        }
        G.add_nodes_from(cluster_names, **cluster_metadata)
        for cluster_idx in range(memberships.shape[0]):
            for label_idx in label_indices:
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

    # prune nodes with no edges to maintain tree structure
    nodes_with_edge: set[str] = {tgt for _, tgt in G.edges}
    all_non_root_nodes: set[str] = set(
        [n_id for n_id in G.nodes if not G.nodes[n_id].get(_IS_ROOT_META_KEY, False)]
    )
    G.remove_nodes_from(list(all_non_root_nodes.difference(nodes_with_edge)))
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


def to_list_of_words(corpus: Corpus, tokeniser_fn: Callable, *matchers) -> list[str]:
    docs = corpus.docs()
    for matcher in matchers:
        docs = corpus.docs().apply(
            lambda doc: [doc[start:end] for match_id, start, end in matcher(doc)]
        )
    return docs.apply(tokeniser_fn).tolist()
