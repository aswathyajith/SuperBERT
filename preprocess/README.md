# The Postgres database

## Tables

The following are tables of some interest:


| Name  | Description | 
| ------------- | ------------- | 
| shadow  | The main table, with contents described below | 
| shadow_file_index | Maps from keys in shadow to file number + line number |


## Shadow table

The table `shadow` has columns as follows:

| Name  | Type | Description | Index? | 
| ------------- | ------------- | ---- | ---- | 
| SID  | bigserial  | Automatically generated sequence id (ignore) | Auto | 
| DOI  | varchar(200)  | DOI | Yes | 
| Titl | text | Article title |Full text |
| Year |  char(4)   | | Yes |
| Lang |  varchar(50)  | Language, e.g., en for english | Yes |
| Jour |  text  | Journal title | Full text | 
| Key  |  char(40)  | Hash | Yes |
| PMID  | varchar(40)  | PubMed ID (when available)| Yes |

A full text index is created e.g. via `CREATE INDEX titl_idx ON shadow USING gin(to_tsvector('pg_catalog.english', titl));`

E.g.,:

| Name  | Value |
| ------------- | ------------- | 
| SID  | 25808589 |
| DOI  | 10.2307/3694202 |
| Titl | Nature of the Services of a Flagman at a Crossing under the Federal Employers Liability Act |
| Year |  1920| | 
| Lang |  en | 
| Jour |  Law Review and American Law Register | 
| Key  |  e2c2b47076a66e235707bafcbade8c5bc0f8e488| | 
| PMID  |                |



# Steps used to preprocess PRO dataset

The PRO dataset is provided in a single large file, `Grobid_Shadow_Bulk_1Ms_20210113`, with one line per article, each line being an XML document produced by [GROBID](https://grobid.readthedocs.io/en/latest/). We process these data to create a Postgre database table `shadow` with title, language, journal for each article. 

Start with `Grobid_Shadow_Bulk_1Ms_20210113`

1. Split into 1M-line files
    ```
    % mkdir Grobid_Shadow_Bulk_1Ms_20210113
    % cd Grobid_Shadow_Bulk_1Ms_20210113
    % split -l 1000000 -d --additional-suffix='.json' ../Shadow_20210113/grobid_shadow_bulk.20210113.json file_
    ```
1. Extract metadata into form suitable for loading into Postgres, creating 9 `insert_shadow_synopsis_20210113_0*.sql`  files
    ```
    % python analyze_shadow_json.py
    ```
1. Load metadata into Postgres `shadow` table, and create indices. (Needs Postgres running: conventionally, on thetalogin1.)
    ```
    % export PGHOST=/tmp
    % psql -p 12345 -d postgres -f create_shadow_table.sql
    % source LOAD_SHADOW.sh
    % psql -p 12345 -d postgres -f index_shadow_table.sql
    ```
    Some queries:
    ```
    select count(*) from shadow --> 83030736
    select count(distinct key) from shadow --> 82330125  ==>  700611 duplicates
    select  lang, count(*) as count  from shadow group by lang  order by  count desc
             en    | 75643546
             de    |  3125088
             fr    |  1224352
             ??    |   923286
             ru    |   724103
             es    |   387565
             it    |   268020
             pt    |   187018
             nl    |   120453
    ```
1. Create a file containing the keys for just english language documents.
    In postgres:
    ```
    \copy (select key from shadow where lang='en') to '/projects/SuperBERT/foster/Ians-Data/english_key.csv' csv
    ```
1. Extract sentences from the documents with keys extracted in step #5.
    ```
    % source RUN_*.sh
    ```
1. Count results based on log_XX.err files:
    ```
    % source COUNT.sh
    ```
    Counts: English: 75562967 Other: 7510189 JSON-failed: 1862384 (2.3%?)
    `select count(distinct key) from shadow where lang='en';` --> 74987356
