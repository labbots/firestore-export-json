<h1 align="center">Firestore Export JSON</h1>

<p align="center">
<a href="https://github.com/labbots/firestore-export-json/stargazers"><img src="https://img.shields.io/github/stars/labbots/firestore-export-json.svg?color=blueviolet&style=for-the-badge" alt="Stars"></a>
<a href="https://github.com/labbots/firestore-export-json/blob/master/LICENSE"><img src="https://img.shields.io/github/license/labbots/firestore-export-json.svg?style=for-the-badge" alt="License"></a>
<a href="https://www.codacy.com/gh/labbots/firestore-export-json/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=labbots/firestore-export-json&amp;utm_campaign=Badge_Grade"><img src="https://img.shields.io/codacy/grade/7fe7c1503f574ac1a2072e611f562896?style=for-the-badge"/></a>
</p>
Convert google firestore/datastore LevelDB exports to JSON data.

## Dependencies

* Python  3.9
*  [Python Google Appengine](https://github.com/GoogleCloudPlatform/appengine-python-standard)

## Setup

### Method 1 - Direct Install

1. Clone the repository.

   ```shell
   $ git clone git@github.com:labbots/firestore-export-json.git
   $ cd firestore-export-json
   ```

2. Create a new virtual environment within the project directory.

   ```shell
   $ python -m venv venv
   ```

3. Activate the virtual environment in the project.

   ```shell
   $ source ./venv/bin/activate
   ```

4. Install framework dependencies.

   ```shell
   $ pip install -e .
   ```

### Method 2 - Make

1. Clone the repository.

   ```shell
   $ git clone git@github.com:labbots/firestore-export-json.git
   $ cd firestore-export-json
   ```

2. Run the make command

   ```
   $ make install
   ```



## Usage

1. Export firestore collections using firestore admin tools. Follow the [instructions here](https://firebase.google.com/docs/firestore/manage-data/export-import#export_data) to backup firestore.
2. The exports are stored in google cloud storage. Download the exported data directory from cloud storage.
3. Use the below command to convert the exported data to JSON. 
4. By default, running the command will use (num_cpus - 1) processes to process the data. This can greatly speed up processing. 
    To set this to something different use the `-P`/`--processes` flags e.g. `./fs_to_json.py source/ dest/ -P 1`
5. By default, this will not clear out any files from the destination directory.
    To force a clean before running use the `-C`/`--clean-dest` flag e.g. `./fs_to_json.py source/ dest/ -C`

### Method 1

`fs_to_json.py` can be used to convert the firestore/datastore export files to JSON data.

```shell
$ python fs_to_json.py path_to_source_dir path_to_destination
```

1. Provide the path to the directory where files such as `output-0` exists as source directory usually this would be `kinds_*` directory.
2. Destination directory must be specified where the json files will be created. If not provided then the json files will be created using `json` folder in source directory.

e.g.
```shell
# this will look for all files in exports/all_namespaces/kind_collection-id that start with `output-` and put the resulting json files in out/collection-id
python fs_to_json.py exports/all_namespaces/kind_collection-id out/collection-id
```

### Method 2

The project exposes console script using setuptools to provide `fs_to_json` CLI command which can be used to convert exports to JSON.

```shell
$ fs_to_json path_to_source_dir path_to_destination
```



## Inspired By

* [Venryx/firestore-leveldb-tools](https://github.com/Venryx/firestore-leveldb-tools) - LevelDB files to JSON converter written in python 2.7.
