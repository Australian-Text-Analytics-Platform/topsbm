""" wrapper2.py

This is a wrapper over TopSBM and is meant to extend the existing workflow with
ATAP integration.
It provides the following:
    1. Enhanced visualisations.
    2. Integrate results into an ATAP Corpus.
"""
import sys

import subprocess

from IPython.display import HTML
from pathlib import Path

import networkx as nx
import numpy as np
import tempfile
from typing import IO
from os import PathLike

from atap_corpus import Corpus
from atap_corpus.parts.dtm import DTM
from topsbm.sbmtm import sbmtm

from utils import embed_js
import srsly

__all__ = ['atap']


class ATAPWrapper(object):
    def __init__(self, model: sbmtm, corpus: Corpus, attribs: dict):
        self.model = model
        self.corpus = corpus
        self.attribs = attribs

    def serialise(self, file: PathLike[str] | IO):
        """ Serialise with added topsbm attributes."""
        attribs = dict()
        try:
            git_args = {
                'origin': ['config', '--get', 'remote.origin.url'],
                'commit': ['rev-parse', 'HEAD'],
            }
            git = dict()
            for name, args in git_args.items():
                git[name] = subprocess.check_output(['git'] + args).strip().decode('utf-8')

            git['origin'] = git['origin'].replace("git@github.com:", "https://")
            attribs['git'] = git
        except subprocess.CalledProcessError:
            print("Failed to retrieve git information to be part of the Corpus attributes. Skipped.", file=sys.stderr)
        attribs['data'] = self.attribs
        self.corpus.attribute('topsbm', attribs)
        return self.corpus.serialise(file)


def atap(model: sbmtm, corpus: Corpus, used_dtm: str) -> ATAPWrapper:
    if not isinstance(model, sbmtm):
        raise ValueError(f"Expecting sbmtm for model but got {model}.")
    if not isinstance(corpus, Corpus):
        raise ValueError(f"Expecting Corpus for corpus but got {corpus}.")
    if model.g is None:
        raise ValueError(f"Your model hasn't been fitted yet. Call .fit() on the model.")

    # note: let's just only do this for level 0 for now.
    level = 0
    topic_dtms = topic_dtms_of(model, level, corpus.get_dtm(used_dtm))
    attributes = dict(word_clusters=dict(dtms=dict()), topic_dists=dict(metas=dict()))
    for cluster_idx, topic_dtm in topic_dtms.items():
        name = f"{used_dtm}_topsbm_lv{level}_cluster{cluster_idx}"
        attributes["word_clusters"]['dtms'][cluster_idx] = name
        corpus.add_dtm(topic_dtm, name)
    topic_dists: dict[int, np.ndarray[float]] = topic_dist_of(model, level)
    for topic_idx, topic_dist in topic_dists.items():
        name = f"topsbm_lv{level}_topic{topic_idx}"
        attributes["topic_dists"]['metas'][topic_idx] = name
        corpus.add_meta(topic_dist, name=name)
    return ATAPWrapper(model, corpus, attributes)


# -- Visualisers --
JUPYTER_ALLOW_HIDDEN = False
try:
    from notebook.services.contents.filemanager import FileContentsManager

    JUPYTER_ALLOW_HIDDEN = FileContentsManager().allow_hidden
except Exception as _:
    pass

_hierarchy_viz = {
    "radial-cluster": "./viz/radial-cluster.js",
    "collapsible-tree": "./viz/collapsible-tree.js"
}


def visualise_hierarchy(model: sbmtm, kind: str) -> tuple[HTML, HTML]:
    if kind not in _hierarchy_viz.keys():
        raise ValueError(f"Must be either {', '.join(_hierarchy_viz.keys())}.")
    viz_js = _hierarchy_viz.get(kind)
    if not Path(viz_js).exists(): raise FileNotFoundError(f"Missing viz js file. {viz_js}")
    digraph_docs, digraph_word = group_membership_digraphs_of(model)

    digraph: nx.DiGraph
    tmp_data_files = []
    tmpd = tempfile.mkdtemp(dir="./." if JUPYTER_ALLOW_HIDDEN else "./")
    for digraph in [digraph_docs, digraph_word]:
        roots = [node for node, in_degree in digraph.in_degree() if in_degree == 0]
        assert len(roots) == 1, "Expecting only 1 root"
        root = roots[0]
        tmp = tempfile.mktemp(dir=tmpd, suffix='.json')
        srsly.write_json(tmp, nx.tree_data(digraph, root=root))
        tmp_data_files.append(tmp)
    return embed_js(viz_js, tmp_data_files[0]), embed_js(viz_js, tmp_data_files[1])

    # --- Data Adapters (from TopSBM to ATAP Corpus) ---


def group_membership_digraphs_of(model: sbmtm) -> tuple[nx.DiGraph, nx.DiGraph]:
    """ Produce a networkx DiGraph based on the group membership output from topSBM.
    :arg model - a fitted topsbm.sbmtm model.

    :return Doc Digraph, Word DiGraph.

    There is a membership matrix for each layer of the model.
    The matrix describes the group that each word/token belongs for the layer.

    Group memberships are retrieved via sbmtm.group_membership(l=<level>) method.
    """
    Gs: list[nx.DiGraph] = list()
    type_labels = [model.documents, model.words]

    prefix = "Level_{level}_"
    for idx, type_ in enumerate(["documents", "words"]):
        G = nx.DiGraph()
        leaf_nodes = type_labels[idx]
        G.add_nodes_from(leaf_nodes)
        for level in range(0, len(model.state.levels)):
            memberships = model.group_membership(l=level)[idx]
            assert len(leaf_nodes) == memberships.shape[1], \
                f"Mismatched number of leaf nodes in group memberships for {type_}."
            cluster_names = [prefix.format(level=level) + str(i) for i in range(memberships.shape[0])]
            G.add_nodes_from(cluster_names, kind='cluster', level=level)
            for cluster_idx in range(memberships.shape[0]):
                for label_idx in range(memberships.shape[1]):
                    weight = memberships[cluster_idx, label_idx]
                    is_member = weight > 0
                    if is_member:
                        leaf, cluster = leaf_nodes[label_idx], cluster_names[cluster_idx]
                        if level == 0:
                            G.add_edge(cluster, leaf, weight=weight)
                        else:
                            # 1. searches bottom up for all prior clusters of (layer - 1) connected to this leaf node.
                            # 2. add an edge from this cluster to all found prior clusters of (layer - 1)
                            edges = [(src, tgt) for src, tgt in G.edges() if tgt == leaf]
                            for l_tmp in range(1, level):
                                prior_clusters = [src for src, _ in edges
                                                  if src.startswith(prefix.format(level=str(l_tmp - 1)))]
                                edges = [(src, tgt) for src, tgt in G.edges() if tgt in prior_clusters]
                            prior_clusters = [prior for prior, _ in edges]
                            for prior_cluster in prior_clusters:
                                G.add_edge(cluster, prior_cluster, weight=weight)
        Gs.append(G)
    return tuple(Gs)


def topic_dtms_of(model: sbmtm, level: int, from_dtm: DTM) -> dict[int, DTM]:
    """ Produce DTMs of topics (word clusters) from the model.
    Used to add directly to Corpus via .add_dtm()
    """
    word_groups: np.ndarray = model.group_membership(l=level)[1]
    assert from_dtm.num_terms == word_groups.shape[1], \
        "Mismatched number of terms. Did you use this dtm to fit the model?"

    dtms = dict()
    for wgroup_idx in range(word_groups.shape[0]):
        dtms[wgroup_idx] = DTM.from_matrix(from_dtm.matrix.multiply(word_groups[wgroup_idx, :]), terms=from_dtm.terms)
    return dtms


def topic_dist_of(model: sbmtm, level: int) -> dict[int, np.ndarray[float]]:
    """ Produce a list of topic distributions
    Used to add directly to Corpus via .add_meta()
    """
    p_tw_d = model.get_groups(l=level)['p_tw_d']  # topic X doc
    num_topics = p_tw_d.shape[0]

    topic_dists = dict()
    for topic_idx in range(num_topics):
        topic_dists[topic_idx] = p_tw_d[topic_idx, :]
    return topic_dists
