# Overview

The PRO dataset is provided in a single large file, `Grobid_Shadow_Bulk_1Ms_20210113`, with one line per article, each line being an XML document produced by [GROBID](https://grobid.readthedocs.io/en/latest/). The approx. 85M articles have around 10B sentences. Ideally, we might load all of these sentences into a database so that we could ask for, e.g., "all sentences that come from articles about genetics." However, in practice it doesn't seem possible to create such an index, so instead we have to operate in phases, as follows:

1. Preparatory
    1. We break the PRO dataset into 85 files, each with 1M articles (one article per line)
    2. We create a Postgre database table `shadow` with title, language, journal, and key (i.e., hash id) for each article.
1. Create training dataset
    1. Use SQL query on `shadow` to identify keys for articles of interest, creating a file containing those keys.
    2. Scan through the 85 files, extractings sentences only for those documents identified in (i)

This process may appear somewhat inefficient (and it is not fast), but we haven not found a better approach. (An attempt to create one file per article crashed the Theta file system!)

In summary: to create a new training set, follow the steps described in **Extracting sentences for a particular subset of documents** below.

## Things to do

1. Work out why many articles do not have a journal name (or, indeed, a title). A quick look suggests that this information is missing in raw data.
    1. As evidence of difficulty:
        1. `select count(*) from shadow where jour=''` --> 51,620,295
        2. `select count(*) from shadow where titl=''` --> 16,358,957
    1. Possible solution: use Crossref API to look things up. However, lookup rate is only around 6/sec (see `get_doi_data.py`).
        1. Crossref has supplied a list of 100M DOI files, these are currently downloading.
        2. Then extract relevant metadata (article title and journal name?) and load into Postgres.
1. Expand the Postgres index to include abstracts:
    1. Modifid `analyze_shadow_json.py` to extract first 200 words of text.
    2. Then build full text index.
1. Update the `shadow_file_index` table to provide location of each document in the "85 files." (That table is currently out of date.) This may help finding a single article based on its key. (If I recall correctly, I tried this as an alternative to scanning all files, but it was slower, at least for large subsets.)

# The Postgres database

## The `shadow` table

The `shadow` table is created from the source PRO data, as described later, by extracting selected metadata from the supplied XML. This allows for identification of articles via searches on language, year, title, author, etc.

| Name  | Type | Description | Index? | 
| ------------- | ------------- | ---- | ---- | 
| SID  | bigserial  | Automatically generated sequence id (ignore) | Auto | 
| DOI  | varchar(200)  | DOI | Yes | 
| Titl | text | Article title (sometimes missing) |Full text |
| Year |  char(4)   | Publication year (sometimes missing) | Yes |
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
| Year |  1920|
| Lang |  en | 
| Jour |  Law Review and American Law Register | 
| Key  |  e2c2b47076a66e235707bafcbade8c5bc0f8e488|
| PMID  |                |



# Creating the `shadow` table, in detail

The PRO dataset is provided in a single large file, `Grobid_Shadow_Bulk_1Ms_20210113`, with one line per article, each line being an XML document produced by [GROBID](https://grobid.readthedocs.io/en/latest/). We process these data to create a Postgre database table `shadow` with title, language, journal for each article. 

1. Split into 1M-line files
    ```
    % mkdir Grobid_Shadow_Bulk_1Ms_20210113
    % cd Grobid_Shadow_Bulk_1Ms_20210113
    % split -l 1000000 -d --additional-suffix='.json' ../Shadow_20210113/grobid_shadow_bulk.20210113.json file_
    ```
1. Extract metadata into form suitable for loading into Postgres, creating 9 `insert_shadow_synopsis_20210113_0*.sql`  files. The program `analyze_shadow_json.py` extracts metadata from the supplied `shadow_file_grobid.2020-01-16.json`. 
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
    
## Extracting sentences for a particular subset of documents, in detail
We use an example to show how we extract sentences for a particular subset of PRO articles, in this case all articles with `language='en'`.

1. In Postgres, create a file containing the keys for the articles of interest.
    ```
    \copy (select key from shadow where lang='en') to '/projects/SuperBERT/foster/Ians-Data/english_key.csv' csv
    ```
1. Extract sentences from the documents with the keys in `english_key.csv`, creating in a directory `BB` a set of sentence files (`sentence_00.txt`, etc.) and log files (`log_00.err`, etc.), one for each of the 85 files of 1M articles each created in the preparatory step. The Python program `extract_xml_with_index.py` does this; the script `RUN_EXTRACTS.sh` applies it to each of the 85 files:
    ```
    % source RUN_EXTRACTS.sh
    ```

Each `log_XX.err` file has a line per article, with a Y (article found, sentences extracted), N (article skipped as not in supplied keys file), or E (JSON parsing error), plus a key. We can count the results based on the files, as follows:

```
% source COUNT.sh
    Counts: English: 75562967 Other: 7510189 JSON-failed: 1862384 (2.3%?)
```
    
See also the numbers in `shadow`: `select count(distinct key) from shadow where lang='en';` --> 74987356. Not sure why they don't quite match.
