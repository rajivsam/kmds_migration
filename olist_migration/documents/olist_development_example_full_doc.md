## Overview

The process of preparing the olist dataset is very similar to that of the SBA except that this is going to be a clustering task. KMDS provides a template to document ML projects for different tasks. The basic mechanics of setting up the repository, initializing the workspace is the same. When you bootstrap the dataset information, you will be providing a differentset of answers. Accordingly, the configuration file, generated from your boot strap answers will be different.

## Dataset Preparation

You, as the data scientist know that this is a clustering task and you need to know how to prepare your dataset. In this example, the data is viewed as a homogeneous graph and the dataset bootstrapping is done accordingly. You can see [this notebook](notebooks/raw_datafile_creation.ipynb) for details. Identifying that this can be abstracted as a graph problem is a skill or context a human brings to problem solving.

## Featurization

This particular dataset is the __wide and short__ category. The dataset has more columns than rows, each column is essentially the same measurement - here it is the weekly revenue for the sale of a product, but easily you can see how this can be electiricity demand for period, gene expression value for a gene in gene expression dataset and so on. Recognizing this dataset is wide and short, the redundancy of column meta-data is something only a human can recognize. Again, this is the human's skill to recognize context. For this type of dataset, feature advice on a column by column basis makes no sense. Feature selection makses sense and this is what the feature advisor will tell you, see [this notebook](notebooks/featurization_advisor_olist.ipynb)

## Model Development

Model development can done by providing the agent a set of documents that are available in the [agent documents](../agent_documents) directory. The modeling instructions are provided by the human expert. The modeling code is available in [this notebook](../notebooks/modeling_spectral_clustering.ipynb) . This code is developed by the copilot coding agent/orchestrator. You can export the serialized model for deployment to a location of your choice. You can view the modeling advice [here](notebooks/modeling_clustering_advisor.ipynb).

The rest of the process of generating the knowledge graph is the same. It should be evident from both the examples that KMDS takes a human expert for judgement and instruction and AI assistant for coding view.
