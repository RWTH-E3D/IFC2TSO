![RWTH Aachen University, E3D](assets/E3D_Logo.png)

# IFC2TSO

The IFC2TSO process includes algorithmic processing, complexity reduction and transfer of information from IFC models to TSO. The process has a modular design so that the individual process steps can also be used independently. A schematic representation of the process and the modular process steps IFC2GRAPH, GRAPH and GRAPH2TSO are shown below.


![IFC2TSO](assets/IFC2TSO.png?raw=true "Process of algorithmic processing, complexity reduction and information transfer from IFC to TSO.")

### IFC2GRAPH
![IFC2GRAPH](assets/IFC2GRAPH.png?raw=true "Schematic representation of a selection of sub-processes and their dependencies in the IFC2GRAPH process step.")

### GRAPH
![GRAPH](assets/GRAPH.png?raw=true "Schematic representation of a selection of sub-processes and their dependencies in the GRAPH process step.")

### GRAPH2TSO
![GRAPH2TSO](assets/GRAPH2TSO.png?raw=true "Schematic representation of a selection of sub-processes and their dependencies in the GRAPH2TSO process step.")


## Implementation
The Python 3.7.12 programming language was used to implement the IFC2TSO process. In addition to the basic functionality included, the standard libraries logging, argparse, json, os, uuid, math, datetime, shutil and zipfile were used to extend the functions. In addition, the libraries ifcopenshell 0.6.0 for parsing the IFC models, lxml 4.6.1 for the conception of the XML-based BCF files, NetworkX 2.5 for the handling of the graphs, Rtree 0.9.7 for the conception and query of the R-trees, NumPy 1.19.1 for the calculation of the absolute three-dimensional positions, trimesh 3.10.2 for the analysis of the spatial dependencies and rdflib 6.1.1 for the conception and serialization of the knowledge representation were used.

An Anaconda Environment of the programming environment is given under **env**. Anaconda can be downloaded and installed from the [Anaconda Homepage](https://www.anaconda.com/products/distribution). A corresponding [manual](https://docs.anaconda.com/anaconda/install/) is also provided. The installation of the environment can be done with the help of the **environment.yml** file using the presented command.

```
conda env create -f environment.yml
```
## Usage

The implementation of the IFC2TSO process is implemented as a command line interface application. Here, the user has to specify the paths of the IFC models as input. In addition, optional parameters can be used to customize the functionality of the process step. The call of the process is shown below and the optional parameters are explained in the table.

```
python src/main.py [-l] [-i] [-bcf_p] [-bcf_pm] [-rds {RDS}] [-ce {L}] [-data] [-bcf_sh] [-r {R}] [-add_edges {JSON}] [-add_sh {JSON}] [-cr] [-bcf_fd] [-add_ic {JSON}] [-add_fc {JSON}] [-add_spatial {IFC}] [-ifcowl] [-use_ns {NS}] [-h] IFC-Modelle
```
|      parameter |description           		 |
|----------------|--------------------------------------|
|-l|Storage of the process progress log as TXT file at the path of the IFC model.       |        
|-i          |Storage of the analysis results of the contained information on technical systems as a TXT file at the path of the IFC model.            |        
|-bcf_p          |Storage of the analysis results at the path of the models.|
|-bcf_pm         |Storage of the results of enrichment to elements with open ports and possible topological neighbors as compressed BCF files at the path of the models.|
|-rds {RDS}          |Analyze the IFC model against the specified attribute identifier and assign the values as standardized property elem_rds to the nodes of the graph.|
|-ce {L}         |Automated extension of the graph with directed edges, based on the results of the processes in the area of enrichment with the maximum allowed distance of L in mm.|
|-data         |Extending the information at the nodes of the graph with an identifier value array containing all inverse attributes of the corresponding element in the IFC model.|
|-bcf_sh  |Storage of the results of the system hierarchy enrichment as a BCF file at the path of the IFC models.|
|-r {R} |Reduction of the imported graph by weakly connected graphs with a size ≤ R.|
|-add_edges {JSON} |Enrich the merged graph with edges contained in the JSON file at the given path.|
|-add_sh {JSON}  |Enrichment of the system hierarchy contained in the JSON file at the given path.|
|-cr |Reduction of the topological complexity of the graph.|
|-bcf_fd  |Storage of the results of the flow direction analysis as a BCF file on the path of the IFC models.|
|-add_ic {JSON} |Enrichment of inner connections contained in the JSON file at the given path.|
|-add_fc {JSON} |Enrichment with functional concepts, such as flow of matter, energy and data, and sources & sinks, contained in the JSON file at the given path.|
|-add_spatial {IFC} |Enrichment of spatial concepts contained in the IFC model at the given path and their dependencies to systems.|
|-ifcowl |Enrichment of the A-Box with classifications of components based on IFCowl.|
|-use_ns |Use of the specified namespace to uniquely identify the instances.|
|-h         |Presentation of explanations on how to call the IFC2GRAPH process step and on necessary as well as optional parameters.|

## Structure of the repository

Under **src** all scripts and necessary files for the functionality of the process are stored. **env** contains the anaconda environment for running the implementation. Under **modules** the source files of the modular process steps IFC2GRAPH, GRAPH and GRAPH2TSO and their corresponding environments are given to implement them independently.

## Citation

The following publication has to be cited for the use of the code.
```
@InProceedings{}
```

## Licence

The program code is licensed via the [MIT license](LICENSE).

## Author

[Nicolas Pauen](https://www.e3d.rwth-aachen.de/cms/E3D/Der-Lehrstuhl/Team/Wissenschaftliche-Beschaeftigte/~tlpi/Nicolas-Pauen/)
