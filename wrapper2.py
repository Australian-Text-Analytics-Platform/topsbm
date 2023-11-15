""" wrapper2.py

This is a wrapper over TopSBM and is meant to extend the existing workflow with
ATAP integration.
It provides the following:
    1. Enhanced visualisations.
    2. Integrate results into an ATAP Corpus.
"""

import networkx as nx
import numpy as np

from atap_corpus.parts.dtm import DTM
from topsbm.sbmtm import sbmtm


def group_membership_digraphs_of(model: sbmtm) -> tuple[nx.DiGraph]:
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


def topic_dtms_of(model: sbmtm, level: int) -> DTM:
    """ Produce DTMs of topics (word clusters) from the model.
    Used to add directly to Corpus via .add_dtm()
    """
    word_groups: np.ndarray = model.group_membership(l=level)[1]
    return DTM.from_matrix(word_groups, terms=model.words)


def topic_dist_of(model: sbmtm, level: int) -> list[np.ndarray[float]]:
    """ Produce a list of topic distributions
    Used to add directly to Corpus via .add_meta()
    """
    p_tw_d = model.get_groups(l=level)['p_tw_d']  # topic X doc
    num_topics = p_tw_d.shape[0]
    return list([p_tw_d[idx, :] for idx in range(num_topics)])
