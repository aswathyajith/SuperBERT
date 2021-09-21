# Steps used to preprocess PRO dataset

1) Start with `Grobid_Shadow_Bulk_1Ms_20210113`

2) Split into 1M-line files

```
% mkdir Grobid_Shadow_Bulk_1Ms_20210113
% cd Grobid_Shadow_Bulk_1Ms_20210113
% split -l 1000000 -d --additional-suffix='.json' ../Shadow_20210113/grobid_shadow_bulk.20210113.json file_
```

3) Extract metadata into form suitable for loading into Postgres, creating 9 `insert_shadow_synopsis_20210113_0*.sql`  files

```
% python analyze_shadow_json.py
```

4) Load metadata into Postgres `shadow` table, and create indices. (Needs Postgres running: conventionally, on thetalogin1.)

```
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

5) Create a file containing the keys for just english language documents

In postgres:
```
\copy (select key from shadow where lang='en') to '/projects/SuperBERT/foster/Ians-Data/english_key.csv' csv
```
