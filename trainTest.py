import LevenshteinDistance as LD
import re

corpus = open('spellchecker/corpus.txt').read()

dictionary = []
for row in corpus.split('\n'):
    data = {}

    row = row.split('\t')

    data['rank'] = row[0]
    data['word'] = re.sub(r"\s{3}", "", row[1]).lower()
    data['frequency'] = row[3]
    data['dispersion'] = row[4]

    dictionary.append(data)
    try:
        self.db.dictionary.insert(data)
        counter = counter + 1
    except:
        print "[ERROR] Cannot insert " + data['word']

for wordD in dictionary:
    parent = wordD['word']
    tmp = {}
    minEdit = 1000
    for wordD in dictionary:
        value = wordD['word']

        if value == parent:
            continue
        ed = LD.compute(parent, value)
        if not tmp.has_key(ed):
            tmp[ed] = {}
            tmp[ed]['words'] = []
        tmp[ed]['words'].append(value)

        minEdit = min(minEdit, ed)

    tmp[minEdit]['edits'] = minEdit
    data = {
        'parent': parent,
        'edits': minEdit,
        'words': tmp[minEdit]['words']
    }

    try:
        self.db.tree.insert(data)
        counter = counter + 1
    except:
        print "[ERROR] Cannot insert " + data['word']
