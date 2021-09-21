import json, re
import csv

#filename = 'Original/shadow_file_grobid.json'
filename = 'shadow_file_grobid.2020-01-16.json'
#outfile  = 'insert_shadow_synopsis'
outfile  = 'insert_shadow_synopsis_20210113'
outfile  = 'foo'

plotfreq      =1000000
ROW_PER_GROUP =100000
GROUP_PER_FILE=100

unique1 = '&abbaABBAabba42'
unique2 = '&yuTTRTaBBbba67'

# Following works for all but ~51 for shadow
def fix_line(line):
    line2a = re.sub(r'", "', unique1, line)
    line2 = re.sub(r'"}', unique2, line2a)
    line3 = re.sub(r'\\[^\\&]', r'', line2) 
    oldline = line3
    newline = re.sub(r'\\', r'', line3)
    while oldline != newline:
        tmpline = newline
        newline = re.sub(r'\\', r'', tmpline)  # repeat
        oldline = tmpline
    newnewlineA = re.sub(unique1, r'", "', newline)
    newnewline = re.sub(unique2, r'"}', newnewlineA)
    return newnewline

def write_insert_group_start(writer):
    writer.write('INSERT INTO shadow (Key, SID, DOI, PMID, Lang, Titl, Year, Jour)\nVALUES\n')

def truncate_value_if_needed(kind, value, maxlen):
    if value==None:
        value=''
    if len(value) >= maxlen:
        print(f'Warning: {kind} truncated to {maxlen} - {value}')
    return re.sub("'",'', value[:maxlen])

def write_inserts_to_file(reader, writer):
    lines   = 0
    success = 0
    error   = 0
    nostatus= 0
    badjson = 0

    write_insert_group_start(writer)
    first = True
    for line in reader:
        lines += 1
        newline = fix_line(line)
    
        try:
            json_doc = json.loads(newline)
        except Exception as e:
            print(f'JSON error on line {lines}: ', e)
            print('Original:', line)
            print('Transformed:', newline)
            badjson += 1
            continue
        shadow = json_doc['shadow']
        key    = shadow['sha1hex']
        sid    = shadow['shadow_id']
        doi    = truncate_value_if_needed('DOI', shadow['doi'], 200)
        pmid   = truncate_value_if_needed('PMID', shadow['pmid'], 200)

        grobid = json_doc['grobid']
        try:
            status = grobid['status']
        except:
            nostatus += 1
            continue
        if status=='success':
            metadata=grobid['metadata']
            try:
                lang = truncate_value_if_needed('LANG', metadata['language_code'], 40)
            except:
                lang = '??'
            try:
                title = re.sub("'",'', metadata['biblio']['title'])
            except:
                title = ''
            try:
                date = metadata['biblio']['date']
                date = date[:4]
            except:
                date = ''
            try:
                journal = re.sub("'",'', metadata['biblio']['journal']['name'])
            except:
                journal = ''

            success += 1
            if not first:
                writer.write(',\n')
            first=False
            if success%ROW_PER_GROUP==0:
                row = f"    ('{key}', '{sid}', '{doi}', '{pmid}', '{lang}', '{title}', '{date}', '{journal}');\n\n"
                writer.write(row)
                if success%(ROW_PER_GROUP*GROUP_PER_FILE)!=0:
                    write_insert_group_start(writer)
                    first = True
            else:
                row = f"    ('{key}', '{sid}', '{doi}', '{pmid}', '{lang}', '{title}', '{date}', '{journal}')"
                writer.write(row)
        else:
            error += 1

        if lines%plotfreq==0:
            print(f'{lines}: S={success}, E={error}, N={nostatus}, B={badjson}', flush=True)
        if success%(ROW_PER_GROUP*GROUP_PER_FILE)==0:
            return False

    # Need to handle last group 
    writer.write(';\n')
    print(f'{lines}: S={success}, E={error}, N={nostatus}, B={badjson}', flush=True)
    return True

MAX_FILES=99
with open(filename) as reader:
    done = False
    outfile_index = 0
    while not done:
        if outfile_index > MAX_FILES:
            print('Too many files')
            exit(1)
        outfile_name  = f'{outfile}_{outfile_index:02d}.sql'
        outfile_index += 1
        with open(outfile_name, 'w') as writer:
            done = write_inserts_to_file(reader, writer)
