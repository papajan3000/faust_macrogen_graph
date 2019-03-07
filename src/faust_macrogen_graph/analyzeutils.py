from collections import Counter
import re
import pandas as pd
from faust_macrogen_graph import graphutils, eades_fas, parserutils
from pathlib import Path
from collections import OrderedDict
import networkx as nx

#TODO: docstring
def compare_approaches(approaches, special_researchers, temppre=False):
    """
    Args:
        approaches (list): List with the approaches names as strings.
        special_resarchers (dict): Dictionary with sources (string) as keys and their publication year (int) as values. 
        temppre (bool): If True, the graph for the approaches will be computed by the combination of 
                        the temppre- and the dates-graph, if False, only the dates-graph.
    Return:
        DataFrame
    """

    approaches_graphs = {}
    approaches_fas =  {}
    
    
    filespath = Path('resources')
    date_items = parserutils.xmlparser(filespath, True, skipignore=False)
    
    for approach in approaches:
        
        
        if temppre:
            temppre_items = parserutils.xmlparser(filespath)
            temppreG = nx.DiGraph()
            for t in temppre_items:
                graphutils.add_egdes_from_node_list(temppreG, t)
                
            datesG = graphutils.graph_from_dates(date_items, approach, special_researchers)
            G = nx.compose(temppreG, datesG)
            
        else:
            G = graphutils.graph_from_dates(date_items, approach, special_researchers)
        
        approaches_graphs[approach] = G
        G_fas = eades_fas.eades_FAS(G, True)
        #adatesG = acyclic dates graph
        aG = G.copy()
        aG.remove_edges_from(G_fas)
    
        approaches_fas[approach] = G_fas
    
    graphs_approaches = {}
    columns = ["n nodes", "n edges", "n cycles", "n feedback edges"]
    
    for k, v in approaches_graphs.items():
        graphs_approaches[k] = [len(v.nodes()), len(v.edges()), len(list(nx.simple_cycles(v))), len(approaches_fas[k])]
    
    approach_df = pd.DataFrame(graphs_approaches)
    approach_df = approach_df.T
    approach_df.columns = columns
    
    return approach_df

#TODO: docstring
def gen_frequencyfas(G):
    """
    Returns:
        DataFrame
    """
    G_fas = eades_fas.eades_FAS(G, True)
    
    #frequency of the researcher as manuscript source
    fas_source_counter = Counter()
    for edge in G_fas:
        if G.has_edge(edge[0], edge[1]):
            edge_data = G.get_edge_data(edge[0], edge[1])
            key = edge_data["source"]
            if fas_source_counter[key]:
                fas_source_counter[key] += 1
            else:
                fas_source_counter[key] = 1
    
                
    fasfrequency_df = pd.DataFrame.from_dict(OrderedDict(fas_source_counter.most_common()), 
                                             orient="index").reset_index()
    fasfrequency_df = fasfrequency_df.rename(columns={"index":"source", 0: "fas_frequency"})
    fasfrequency_df.set_index("source", inplace=True)
    
    return fasfrequency_df


def dataframe_from_column(df, metacol, extractcol):
    """Extract DataFrames of specific columns of another DataFrame and generate a new DataFrame.
    
    Args:
        df (DataFrame): The DataFrame whereof the DataFrames will be extracted.
        metacol (string): Column name of df, where the DataFrames are stored.
        extractcol (string): Column name of the extracted DataFrame.
    Returns:
        Extracted DataFramefrom another DataFrame.
    """
    d = {}
    for idx, dataframe in enumerate(df[metacol]):
        source = list(df.index)
        extractdf = dict(dataframe[extractcol])
        d[source[idx]] = extractdf

    return pd.DataFrame(d)


def get_source_year(G, special_researchers):
    """Returns dictionary with the edge sources of a graph as keys and their publication year as values, extracted from a string
        or a special dictionary.
    
    Args:
        G (DiGraph): DiGraph-Object of networkx.
        special_resarchers (dict): Dictionary with sources (string) as keys and their publication year (int) as values. 
    Returns:
        Dictionary with the sources as keys and their publication year as values.
    """    
    source_year = {}
    
    for edge in G.edges():
        edge_data = G.get_edge_data(edge[0], edge[1])
        source = edge_data["source"]
        if source in source_year:
            pass
        else:
            if source in special_researchers:
                year = special_researchers[source]
            else:
                year = re.match(r".*([1-3][0-9]{3})", str(source))
                if year is not None:
                    year = year.group(1)
                else:
                    year = 1000
            
            source_year[source] = int(year)
        
    return source_year


def get_research_score(G):
    """Parse through the source-attribute of Graph edges and return a Counter with a frequency score assigned to each researcher.
    
    Args:
        G (DiGraph): DiGraph-Object of networkx.
    Returns:
        Counter with a frequency score assigned to each researcher.
    """
    research_score = Counter()
    for edge in G.edges():
        edge_data = G.get_edge_data(edge[0], edge[1])
        source = edge_data["source"]
        research_score[source] += 1
    return research_score


def get_norm_research_score(G, special_researchers, min_range=1770, max_range=2017):
    """Normalize the score of a given Counter of researchers and their score. The score is computed as following: 
            Number of the researchers work mentioned in the macrogenesis * normalized year of publication of researchers work about Faust
            e.g.: Bohnenkamp 1994 --> 94 * ((1994 - 1770) / (2017 - 1770)) = 94 * 0.9068825910931174 = 85.24696356275304
        The goal of the normalization is to generate a number between 0 and 1 as coefficent to give older researchers work less weight in the context
        of a comparison between two possible conflicting statements of researchers about a different dating of manuscripts.
        
    Args:
        G (DiGraph): DiGraph-Object of networkx.
        special_resarchers (dict): Dictionary with sources (string) as keys and their publication year (int) as values. 
        min_range (int): Lower border of the normalization function.
        max_range (int): Upper border of the normalization function.
    Returns:
        Counter with a normalized score assigned to each researcher.
    """
    research_score = dict(get_research_score(G))
    norm_research_score = {}
    

    for key, value in research_score.items():
        if key in special_researchers:
            year = special_researchers[key]
        else:
            year = re.match(r".*([1-3][0-9]{3})", str(key))
            if year is not None:
                year = year.group(1)
            else:
                year = 1000
                
        normalized_year = (int(year) - min_range) / (max_range - min_range) #range(1700, 2020), normalized to be between 0 and 1
        norm_research_score[key] = value * normalized_year
    return norm_research_score

#TODO: docstring
def minimize_source_removal(G, remaining_fas_size=0):
    """
    Return:
        DataFrame
    """
    
    fasfrequency_df = gen_frequencyfas(G)
    sourcelist = list(fasfrequency_df.index)
    df = pd.DataFrame(0, index=sourcelist, columns=sourcelist)
    
    for source in sourcelist:
        
        nG = graphutils.remove_edge_by_source(G.copy(), source)
        nG_fas = eades_fas.eades_FAS(nG, True)
        df[source][source] = 1
        
        if len(nG_fas) > remaining_fas_size:
            withoutsource = [e for i,e in enumerate(sourcelist) if e != source]
            
            for element in withoutsource:
                nG = graphutils.remove_edge_by_source(nG, element)
                nlongerG_fas = eades_fas.eades_FAS(nG, True)
                df[element][source] = 1
                
                if len(nlongerG_fas) <= remaining_fas_size:
                    break
    
    df.index.name = "source"
    return df


def special_research_generator(item_list):
    """Generates a list with researchers out of all researchers whose name doesn't include a publication year.
    
    Args:
        item_list (list): List with date-, temppre- and tempsyn_items.
    Returns:
        List with special researchers where the publication year can't be extracted from the name.
    """
    researchers = []
    for items in item_list:
        for item in items:
            research_list = item[0]
            for research in research_list:
                if research not in researchers:
                    researchers.append(research)
    
    special_researchers = []
    for r in researchers:
        match = re.match(r".*([1-3][0-9]{3})", r)
        if match == None:
            special_researchers.append(r)

    return special_researchers