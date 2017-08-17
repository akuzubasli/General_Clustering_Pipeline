"""
@author: The KnowEnG dev team
"""
import os
import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score
import knpackage.toolbox as kn
import knpackage.distributed_computing_utils as dstutil

def run_hclust(run_parameters):
    """ wrapper: call sequence to perform hierchical clustering and save the results.

    Args:
        run_parameters: parameter set dictionary.
    """
    number_of_clusters = run_parameters['number_of_clusters']
    spreadsheet_name_full_path = run_parameters['spreadsheet_name_full_path']

    spreadsheet_df = kn.get_spreadsheet_df(spreadsheet_name_full_path)
    spreadsheet_mat = spreadsheet_df.as_matrix()

    h_mat = kn.perform_hclust(spreadsheet_mat, run_parameters)

    sample_names = spreadsheet_df.columns
    save_consensus_clustering(linkage_matrix, sample_names, labels, run_parameters)
    save_final_samples_clustering(sample_names, labels, run_parameters)
    save_spreadsheet_and_variance_heatmap(spreadsheet_df, labels, run_parameters)


def run_kmeans(run_parameters):
    """ wrapper: call sequence to perform kmeans clustering and save the results.

    Args:
        run_parameters: parameter set dictionary.
    """
    processing_method = run_parameters['processing_method']
    number_of_clusters = run_parameters['number_of_clusters']
    spreadsheet_name_full_path = run_parameters['spreadsheet_name_full_path']

    spreadsheet_df = kn.get_spreadsheet_df(spreadsheet_name_full_path)
    spreadsheet_mat = spreadsheet_df.as_matrix()
    spreadsheet_mat = kn.get_quantile_norm_matrix(spreadsheet_mat)
    number_of_samples = spreadsheet_mat.shape[1]

    sample_names = spreadsheet_df.columns
    save_consensus_clustering(consensus_matrix, sample_names, labels, run_parameters)
    save_final_samples_clustering(sample_names, labels, run_parameters)
    save_spreadsheet_and_variance_heatmap(spreadsheet_df, labels, run_parameters)

def save_spreadsheet_and_variance_heatmap(spreadsheet_df, labels, run_parameters, network_mat=None):
    """ save the full genes by samples spreadsheet as processed or smoothed if network is provided.
        Also save variance in separate file.
    Args:
        spreadsheet_df: the dataframe as processed
        run_parameters: with keys for "results_directory", "method", (optional - "top_number_of_genes")
        network_mat:    (if appropriate) normalized network adjacency matrix used in processing

    Output:
        genes_by_samples_heatmp_{method}_{timestamp}_viz.tsv
        genes_averages_by_cluster_{method}_{timestamp}_viz.tsv
        top_genes_by_cluster_{method}_{timestamp}_download.tsv
    """
    if network_mat is not None:
        sample_smooth, nun = kn.smooth_matrix_with_rwr(spreadsheet_df.as_matrix(), network_mat, run_parameters)
        clusters_df = pd.DataFrame(sample_smooth, index=spreadsheet_df.index.values, columns=spreadsheet_df.columns.values)
    else:
        clusters_df = spreadsheet_df

    clusters_df.to_csv(get_output_file_name(run_parameters, 'genes_by_samples_heatmap', 'viz'), sep='\t')

    cluster_ave_df = pd.DataFrame({i: spreadsheet_df.iloc[:, labels == i].mean(axis=1) for i in np.unique(labels)})
    col_labels = []
    for cluster_number in np.unique(labels):
        col_labels.append('Cluster_%d'%(cluster_number))
    cluster_ave_df.columns = col_labels
    cluster_ave_df.to_csv(get_output_file_name(run_parameters, 'genes_averages_by_cluster', 'viz'), sep='\t')

    clusters_variance_df = pd.DataFrame(clusters_df.var(axis=1), columns=['variance'])
    clusters_variance_df.to_csv(get_output_file_name(run_parameters, 'genes_variance', 'viz'), sep='\t')

    top_number_of_genes_df = pd.DataFrame(data=np.zeros((cluster_ave_df.shape)), columns=cluster_ave_df.columns,
                                          index=cluster_ave_df.index.values)

    top_number_of_genes = run_parameters['top_number_of_genes']
    for sample in top_number_of_genes_df.columns.values:
        top_index = np.argsort(cluster_ave_df[sample].values)[::-1]
        top_number_of_genes_df[sample].iloc[top_index[0:top_number_of_genes]] = 1
    top_number_of_genes_df.to_csv(get_output_file_name(run_parameters, 'top_genes_by_cluster', 'download'), sep='\t')


def save_final_samples_clustering(sample_names, labels, run_parameters):
    """ wtite .tsv file that assings a cluster number label to the sample_names.

    Args:
        sample_names: (unique) data identifiers.
        labels: cluster number assignments.
        run_parameters: write path (run_parameters["results_directory"]).

    Output:
        samples_labeled_by_cluster_{method}_{timestamp}_viz.tsv
        phenotypes_labeled_by_cluster_{method}_{timestamp}_viz.tsv
    """
    cluster_labels_df = kn.create_df_with_sample_labels(sample_names, labels)
    cluster_mapping_full_path = get_output_file_name(run_parameters, 'samples_label_by_cluster', 'viz')
    cluster_labels_df.to_csv(cluster_mapping_full_path, sep='\t', header=None)

    if 'phenotype_name_full_path' in run_parameters.keys():
        run_parameters['cluster_mapping_full_path'] = cluster_mapping_full_path
        cluster_eval.clustering_evaluation(run_parameters)

def get_output_file_name(run_parameters, prefix_string, suffix_string='', type_suffix='tsv'):
    """ get the full directory / filename for writing
    Args:
        run_parameters: dictionary with keys: "results_directory", "method" and "correlation_measure"
        prefix_string:  the first letters of the ouput file name
        suffix_string:  the last letters of the output file name before '.tsv'

    Returns:
        output_file_name:   full file and directory name suitable for file writing
    """
    output_file_name = os.path.join(run_parameters["results_directory"], prefix_string + '_' + run_parameters['method'])
    output_file_name = kn.create_timestamped_filename(output_file_name) + '_' + suffix_string + '.' + type_suffix

    return output_file_name