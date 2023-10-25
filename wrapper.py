""" tm.py
Topic Modelling
"""

from pathlib import Path
from typing import Union, Optional, Any
import pandas as pd

from atap_corpus.corpus import Corpus
import logging

logger = logging.getLogger(__name__)


class TopSBM(Serialisable):
    """ TopSBM is a topic modelling approach based on Stochastic Block Models.
    This approach is non-parametric, so number of topic (typically used a param in LDA) is not required.

    It models the document and term as a bipartite graph.
    Based on the formulation of P( partition | graph), the partition is inferred via MCMC.

    reference: https://topsbm.github.io/
    """

    def __init__(self, corpus: Corpus, meta_title: Optional[str] = None):
        """
        Create a TopSBM object based on corpus.
        :param corpus: the corpus you want to run TopSBM on.
        :param meta_title: optional meta used as titles for the documents.
        """
        # note: meta_title is made compulsory here for simplicity. It can be optional for topsbm.
        self._model = sbmtm()
        self._corpus = corpus
        if meta_title is not None:
            meta = self._corpus.meta.get_or_raise_err(meta_title)
            self._meta_title = meta.series.tolist()
        else:
            self._meta_title = None

        # object state - do not change these.
        self._results: Optional[dict[str, Any]] = None
        self._dtm_id: Optional[str] = None

    def build(self, dtm_id: Optional[str] = None, **fit_kwargs):
        """ Build graph based on dtm and fit TopSBM.

        :param dtm_id - the DTM you want to run TopSBM on. (default: tokens)
        """
        if self.is_built:
            raise ReinitException(
                f"Already built with {self._dtm_id}. "
                f"Created another {self.__class__.__name__} to fit another corpus or dtm."
            )

        if dtm_id is None or dtm_id == self._corpus._dtm_registry.tokens_dtm_id:
            dtm_id = self._corpus._dtm_registry.tokens_dtm_id
            list_texts = self._corpus.dtm.to_lists_of_terms()
        else:
            list_texts = self._corpus._dtm_registry.get_or_raise_err(dtm_id).to_lists_of_terms()

        logger.debug("Make graph from document-term-matrix.")
        # todo (perf): possibly construct graph directly from dtm matrix - pending investigation.
        self._model.make_graph(list_texts=list_texts,
                               documents=self._meta_title,
                               counts=True,  # save frequencies as edge weights
                               n_min=None, )  # keep terms with minimum frequencies of 1

        """
        # note (see above): partial investigation - it seems we can't add 'titles' as a graph property
        # self._model.make_graph_from_BoW_df(df=self._corpus.dtm.to_dataframe().T,
        #                                    counts=True,
        #                                    n_min=None)
        """

        logger.debug("Fitting the model: Find blocks based on the graph.")
        self._model.fit(**fit_kwargs)
        logger.debug("Done.")
        self._results = self._model.get_groups(l=0)
        self._dtm_id = dtm_id

    @property
    def is_built(self) -> bool:
        return self._results is not None

    @property
    def dtm_id(self) -> str:
        return self._dtm_id

    def terms_of(self, topic: int) -> tuple[str, float]:
        """ Return the terms associated with the topic(s) in descending order."""
        return self.topic_terms.loc[topic, :].sort_values(ascending=False).items()

    @property
    def num_topics(self) -> int:
        return self._results['Bw']

    @property
    def topics(self) -> list[int]:
        return self.doc_topics.columns

    @property
    def doc_topics(self) -> pd.DataFrame:
        """ The probability Document-Topic matrix."""
        doc_topic_matrix = self._results['p_tw_d'].T
        assert doc_topic_matrix.shape[0] == len(self._corpus), "Mismatched number of documents."
        assert doc_topic_matrix.shape[1] == self.num_topics, "Mismatched number of topics."
        return pd.DataFrame(doc_topic_matrix, index=self._corpus._df.index)

    @property
    def topic_terms(self) -> pd.DataFrame:
        """ The probability Topic-Term matrix.
        In TopSBM, a 'term' may only exist in one topic (i.e. topic-word block).

        The full sum of this matrix equals to size of the vocabulary.
        """
        topic_terms_matrix = self._results['p_tw_w']
        assert topic_terms_matrix.shape[0] == self.num_topics, "Mismatched number of topics."
        assert topic_terms_matrix.shape[1] == len(self._corpus), "Mismatched number of documents."
        terms = self._model.words
        topic_terms_matrix = pd.DataFrame(topic_terms_matrix, columns=terms, index=self._corpus.index)
        return topic_terms_matrix.div(topic_terms_matrix.sum(axis=1), axis=0)

    def add_results_to_corpus(self):
        """ Append results back into the corpus.
        1. document-topics matrix as a custom dtm.
        2. topic distribution per document. But they'd need to know what 'terms' constitutes the topics.

        This operation does not repeat if already added.
        """
        custom_dtm_id = self._add_doc_topic_dtm()
        logger.debug(f"Added {custom_dtm_id} dtm to corpus.")
        topic_meta_ids = self._add_topics_as_metas()
        logger.debug(f"Added {', '.join(topic_meta_ids)} metas to corpus.")

        # todo: no indirect topic-word information is kept.
        #  (Currently, user should keep this object themselves)
        return {
            'custom_dtm_id': custom_dtm_id,
            'meta_ids': topic_meta_ids
        }

    def _add_doc_topic_dtm(self) -> str:
        """ Adds the doc-topic matrix as a custom DTM to corpus.

        This operation does not repeat if already added.
        """
        from scipy.sparse import csr_matrix
        from juxtorpus.corpus.dtm import DTM
        from juxtorpus.utils.utils_formats import format_dtm_id
        import numpy as np
        dtm_id = format_dtm_id(self.__class__, "doctopic", f"from_dtm:{self._dtm_id}")
        if self._corpus._dtm_registry.get(dtm_id) is not None: return dtm_id

        doc_topics: pd.DataFrame = self.doc_topics
        topics: list[int] = doc_topics.columns

        matrix: csr_matrix = csr_matrix(doc_topics.values)

        dtm = DTM.from_matrix(matrix, np.array(topics))

        assert dtm.is_compatible(self._corpus), "Doc-Topic DTM is not compatible with corpus."

        self._corpus._dtm_registry.set_custom_dtm(dtm, dtm_id, self._corpus._df.index)
        return dtm_id

    def _add_topics_as_metas(self) -> list[str]:
        """ Adds all topics as SeriesMeta to the corpus.

        This operation does not repeat if already added.
        """
        from juxtorpus.corpus.meta import SeriesMeta
        from juxtorpus.utils.utils_formats import format_meta_id
        doc_topics: pd.DataFrame = self.doc_topics
        topics = doc_topics.columns
        meta_ids = []
        for topic in topics:
            meta_id = format_meta_id(self.__class__, "topic", topic)
            if self._corpus.meta.get(meta_id, None) is None:
                meta = SeriesMeta(id_=meta_id, series=doc_topics.loc[:, topic].copy())
                self._corpus.add_meta(meta)
            meta_ids.append(meta_id)
        return meta_ids

    @classmethod
    def deserialise(cls, path: Union[str, Path]) -> 'Serialisable':
        raise NotImplemented()

    def serialise(self, path: Union[str, Path]):
        """ Serialise the topic-word matrix."""
        raise NotImplemented()

    def __repr__(self) -> str:
        return f"<TopSBM on corpus:{self._corpus.name} from_dtm:{self._dtm_id} is_built:{self.is_built}>"
